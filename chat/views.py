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
        
        return_data = {
            "data": 
                return_field(visible_message.serialze(), ['message_id', 'content', 'senderNickname', 'created_time', 'replying', 'repliedCount']) for visible_message in visible_messages
        }
    else:
        return BAD_METHOD        