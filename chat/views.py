import json
import re
from django.http import HttpRequest, HttpResponse

from user.models import User, FriendRequest
from chat.models import Chat, Message, GroupNotice
from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require
from utils.utils_time import get_timestamp
from utils.utils_jwt import generate_jwt_token, check_jwt_token

@CheckRequire
def message(req: HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    pattern_whitelist = r'^[0-9a-zA-Z_]+$'
    userName = require(body, "userName", "string", err_msg="Missing or error type of [userName]")
    assert re.match(pattern_whitelist, userName), f"[userName] contains illegal character(s):{re.sub(r'[0-9a-zA-Z_]', '', userName)}"
    chat_id = require(body, "chat_id", "int", err_msg="Missing or error type of [chat_id]")
    user = User.objects.filter(userName=userName).first()
    chat = Chat.objects.filter(chat_id=chat_id).first()
    
    if not user:
        return request_failed(1, "User not found", 404)
    if not chat:
        return request_failed(1, "Chat not found", 404)
    
    jwt_token = req.headers.get("Authorization")
    data = check_jwt_token(jwt_token)
    if data == None:
        return request_failed(2,"Invalid or expired JWT", 401)
    if userName != data["userName"]:
        return request_failed(2,"Invalid request", 401)
    
    members = chat.memberList.all()
    chatName = chat.chatName
    inMembers = members.filter(userName=userName).first()
    if not inMembers:
        return request_failed(3, f"User {userName} is not in chat {chatName}", 404)

    if req.method == "GET":
        after = require(body, "after", "float", err_msg="Missing or error type of [after]")
        limit = require(body, "limit", "int", err_msg="Missing or error type of [limit]")
        messages = chat.messageList.filter(created_time__gte=after).order_by("-created_time")
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
            message = return_field(visible_message.serialize(), ['message_id', 'content', 'senderNickname', 'created_time', 'replying', 'repliedCount'])
            message['chat_id'] = chat_id
            returnMessageList.append(message)
        return_data = {
            "data": returnMessageList
        }
        return request_success(return_data)
    
    elif req.method == "POST":
        content = require(body, "content", "string", err_msg="Missing or error type of [content]")
        replying = require(body, "replying", "int", err_msg="Missing or error type of [replying]")
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
    chat = Chat.objects.filter(chatName__in=possibleChatNames).first()
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
    
    return_data = {
        "data": {
            "chat_id": chat.chat_id,
            "alreadyCreated": False
        }
    }
    return request_success(return_data)