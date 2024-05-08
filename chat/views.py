import json
import re
from django.http import HttpRequest, HttpResponse

from user.models import User, FriendRequest
from chat.models import Chat, Message, GroupNotice, UserReadTimestamp
from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require
from utils.utils_time import get_timestamp
from utils.utils_jwt import generate_jwt_token, check_jwt_token
from datetime import timezone,datetime
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
@CheckRequire
def message(req: HttpRequest):
    
    pattern_whitelist = r'^[0-9a-zA-Z_]+$'
    if req.method=="POST":
        body = json.loads(req.body.decode("utf-8"))
        userName = require(body, "userName", "string", err_msg="Missing or error type of [userName]")
        assert re.match(pattern_whitelist, userName), f"[userName] contains illegal character(s):{re.sub(r'[0-9a-zA-Z_]', '', userName)}"
        chat_id = require(body, "chat_id", "int", err_msg="Missing or error type of [chat_id]")
    elif req.method == "GET":
        try:
            userName: str = req.GET.get('userName','')
        except:
            return request_failed(-2, "Missing url parameter(s): should contain userName and chat_id", 400)
        chat_id: int = req.GET.get('chat_id',0)
        after: float = req.GET.get('after', 0)
        limit: int = int(req.GET.get('limit', '100'))

    else:
        return BAD_METHOD  
    
    if chat_id != 0:
        chat = Chat.objects.filter(chat_id=chat_id).first()
        if not chat:
            return request_failed(1, "Chat not found", 404)

    user = User.objects.filter(userName=userName).first()
    if not user:
        return request_failed(1, "User not found", 404)
    jwt_token = req.headers.get("Authorization")
    data = check_jwt_token(jwt_token)
    if data == None:
        return request_failed(2,"Invalid or expired JWT", 401)
    if userName != data["userName"]:
        return request_failed(2,"Invalid request", 401)
    if userName!= '' and chat_id != 0:
        members = chat.memberList.all()
        chatName = chat.chatName
        inMembers = members.filter(userName=userName).first()
        if not inMembers:
            return request_failed(3, f"User {userName} is not in chat {chatName}", 404)
    if req.method == "GET":
        if chat_id != 0:
            messages = chat.messageList.filter(created_time__gt=after).order_by("-created_time")
        else:
            messages = Message.objects.filter(created_time__gt=after).order_by("-created_time")
        visible_messages = []
        
        for message in messages:
            visibleList = message.visibleToUserList.all()
            inList = visibleList.filter(userName=userName).first()
            if inList:
                visible_messages.append(message)
        
        if len(visible_messages) > limit:
            visible_messages = visible_messages[:limit]
        
        returnMessageList = []
        for visible_message in visible_messages:
            message = return_field(visible_message.serialize(), ['message_id', 'content', 'sender', 'senderAvatar', 'created_time', 'replying', 'repliedCount'])
            message['chat_id'] = visible_message.belongToChat.chat_id
            returnMessageList.append(message)
        return_data = {
            "data": returnMessageList
        }
        return request_success(return_data)
    
    elif req.method == "POST":
        content = require(body, "content", "string", err_msg="Missing or error type of [content]")
        replying = require(body, "replying", "int", err_msg="Missing or error type of [replying]")
        isGroup = chat.isGroup
        if not isGroup:
            memberList = chat.memberList.all()
            for member in memberList:
                if member != user:
                    isFriend = user.friends.filter(userName=member.userName)
                    if not isFriend:
                        return request_failed(5, "He/She is not your friend", 405)
        if replying != 0:
            message = Message.objects.create(content=content, sender=user, belongToChat=chat, created_time=get_timestamp(), replying=replying)
            message.default_visible_to_user_list()
            replyMessage = Message.objects.filter(message_id=replying).first()
            if replyMessage:
                replyMessage.repliedCount += 1
                replyMessage.save()
            message.save()
        else:
            message = Message.objects.create(content=content, sender=user, belongToChat=chat, created_time=get_timestamp())
            message.default_visible_to_user_list()
            message.save()
        channel_layer = get_channel_layer()
        for member in chat.memberList.all():
            async_to_sync(channel_layer.group_send)(member.userName, {'type': 'notify'})
        return_data = {
            "data": {
                "message_id": message.message_id
            }
        }
        return request_success(return_data)
    else:
        return BAD_METHOD  
    
def create_private(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    
    body = json.loads(req.body.decode("utf-8"))
    createrName = require(body, "createrName", "string", err_msg="Missing or error type of [createrName]")
    memberName = require(body, "memberName", "string", err_msg="Missing or error type of [memberName]")
    creater = User.objects.filter(userName=createrName).first()
    member = User.objects.filter(userName=memberName).first()
    
    if not creater:
        return request_failed(1, "Creater not found", 404)
    if not member:
        return request_failed(1, "Member not found", 404)
    
    jwt_token = req.headers.get("Authorization")
    data = check_jwt_token(jwt_token)
    if data == None:
        return request_failed(2,"Invalid or expired JWT", 401)
    
    if createrName != data["userName"]:
        return request_failed(2,"Invalid request", 401)
    
    isFriend = creater.friends.filter(userName=memberName).first()
    if not isFriend:
        return request_failed(3, f"User {memberName} is not {createrName}'s friend", 403)
    
    possibleChatNames = [f"{createrName} and {memberName}", f"{memberName} and {createrName}"]
    chat = Chat.objects.filter(chatName__in=possibleChatNames,isGroup = False).first()
    if chat:
        return_data = {
            "data":{
                "chat_id": chat.chat_id,
                "alreadyCreated": True
            }
        }
        return request_success(return_data)
    
    chat = Chat.objects.create(chatName=f"{createrName} and {memberName}")
    chat.memberList.add(creater)
    chat.memberList.add(member)
    chat.save()
    
    createrReadTimestamp = UserReadTimestamp.objects.create(user=creater, chat=chat)
    memberReadTimestamp = UserReadTimestamp.objects.create(user=member, chat=chat)
    createrReadTimestamp.save()
    memberReadTimestamp.save()
    
    return_data = {
        "data": {
            "chat_id": chat.chat_id,
            "alreadyCreated": False
        }
    }
    return request_success(return_data)

def chat_info(req:HttpRequest):
    if req.method != "GET":
        return BAD_METHOD
    try:
        userName: str = req.GET.get('userName')
        chat_ids: int = req.GET.getlist('chat_id',[])
    except:
        return request_failed(-2, "Missing url parameter(s): should contain userName and chat_id", 400)
    user = User.objects.filter(userName=userName).first()
    if not user:
        return request_failed(1, "User not found", 404)
    jwt_token = req.headers.get("Authorization")
    data = check_jwt_token(jwt_token)
    if data == None:
        return request_failed(2,"Invalid or expired JWT", 401)
    if userName != data["userName"]:
        return request_failed(2,"Invalid request", 401)
    returnChatList = []
    for chat_id in chat_ids:
        chat = Chat.objects.filter(chat_id=chat_id).first()
        if not chat:
            chat_status = 1
            errChat = {}
            errChat["chat_id"] = chat_id
            errChat["chat_status"] = chat_status
            returnChatList.append(errChat)
        else:
            inChat = chat.memberList.filter(userName=userName).first()
            if not inChat:
                chat_status = 2
                errChat = {}
                errChat["chat_id"] = chat_id
                errChat["chat_status"] = chat_status
                returnChatList.append(errChat)
            else:
                chat_status = 0
                normalChat = chat.serialize()
                normalChat["chat_status"] = chat_status
                returnChatList.append(normalChat)
    return_data = {
        "data": returnChatList
    }
    return request_success(return_data)

@CheckRequire
def read_message(req:HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    
    body = json.loads(req.body.decode("utf-8"))
    userName = require(body, "userName", "string", err_msg="Missing or error type of [userName]")
    chat_id = require(body, "chat_id", "int", err_msg="Missing or error type of [chat_id]")
    after = require(body, "after", "float", err_msg="Missing or error type of [timestamp]")
    
    chat = Chat.objects.filter(chat_id=chat_id).first()
    if not chat:
        return request_failed(1, "Chat not found", 404)

    user = User.objects.filter(userName=userName).first()
    if not user:
        return request_failed(1, "User not found", 404)
    
    jwt_token = req.headers.get("Authorization")
    data = check_jwt_token(jwt_token)
    if data == None:
        return request_failed(2,"Invalid or expired JWT", 401)
    if userName != data["userName"]:
        return request_failed(2,"Invalid request", 401)
    
    userReadTimestamp = UserReadTimestamp.objects.filter(user=user, chat=chat).first()
    if not userReadTimestamp:
        userReadTimestamp = UserReadTimestamp.objects.create(user=user, chat=chat, after=after)
        userReadTimestamp.save()
    else:
        if after > userReadTimestamp.after:
            userReadTimestamp.after = after
            userReadTimestamp.save()
        
    return request_success()

@CheckRequire
def message_read_status(req:HttpRequest):
    if req.method != "GET":
        return BAD_METHOD
    
    userName: str = req.GET.get('userName','')
    message_id: int = req.GET.get('message_id', '')
    
    user = User.objects.filter(userName=userName).first()
    if not user:
        return request_failed(1, "User not found", 404)
    
    message = Message.objects.filter(message_id=message_id).first()
    if not message:
        return request_failed(1, "Message not found", 404)
    
    jwt_token = req.headers.get("Authorization")
    data = check_jwt_token(jwt_token)
    if data == None:
        return request_failed(2,"Invalid or expired JWT", 401)
    if userName != data["userName"]:
        return request_failed(2,"Invalid request", 401)
    
    visibleUser = message.visibleToUserList.all()
    chat = message.belongToChat
    
    alreadyReadUser = []
    
    for vuser in visibleUser:
        userReadTimestamp = UserReadTimestamp.objects.filter(user=vuser, chat=chat).first()
        if userReadTimestamp.after >= message.created_time:
            alreadyReadUser.append(vuser.userName)
    
    return_data = {
        "data": alreadyReadUser
    }
    
    return request_success(return_data)

@CheckRequire
def create_group(req:HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    
    body = json.loads(req.body.decode("utf-8"))
    userName = require(body, "userName", "string", err_msg="Missing or error type of [userName]")
    memberList = require(body, "memberList", "list", err_msg="Missing or error type of [memberList]")
    
    user = User.objects.filter(userName=userName).first()
    if not user:
        return request_failed(1, "User not found", 404)
    
    jwt_token = req.headers.get("Authorization")
    data = check_jwt_token(jwt_token)
    if data == None:
        return request_failed(2,"Invalid or expired JWT", 401)
    if userName != data["userName"]:
        return request_failed(2,"Invalid request", 401)
    
    members = User.objects.filter(userName__in=memberList)
    if len(members) < 2:
        return request_failed(3, "Group member < 3", 400)
    
    chatName = userName
    max_length = MAX_CHAR_LENGTH
    friends = user.friends.all()
    for member in members:
        if len(chatName) + len(member.userName) + 4 > max_length:
            chatName += "..."
            break
        chatName += "," + member.userName
        if member not in friends:
            return request_failed(4, "Not friend", 400)
    
    chat = Chat.objects.create(chatName=chatName, isGroup=True, owner=user)
    for member in members:
        chat.memberList.add(member)
        
    chat.save()
    return_data = {
        "chat_id": chat.chat_id
    }
    return request_success(return_data)