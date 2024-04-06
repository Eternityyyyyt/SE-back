import json
import re
from django.http import HttpRequest, HttpResponse

from user.models import User, FriendRequest
from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require
from utils.utils_time import get_timestamp
from utils.utils_jwt import generate_jwt_token, check_jwt_token

@CheckRequire
def startup(req: HttpRequest):
    return HttpResponse("Congratulations! You have successfully installed the requirements. Go ahead!")


@CheckRequire
def login(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    
    # Request body example: {"userName": "Ashitemaru", "password": "123456"}
    body = json.loads(req.body.decode("utf-8"))
    pattern_whitelist = r'^[0-9a-zA-Z_]+$'
    userName = require(body, "userName", "string", err_msg="Missing or error type of [userName]")
    password = require(body, "password", "string", err_msg="Missing or error type of [password]")
    assert re.match(pattern_whitelist, userName), f"[userName] contains illegal character(s):{re.sub(r'[0-9a-zA-Z_]', '', userName)}"
    assert re.match(pattern_whitelist,password), f"[password] contains illegal character(s):{re.sub(r'[0-9a-zA-Z_]', '', password)}"
    if User.objects.filter(userName=userName).exists():
        user = User.objects.filter(userName=userName).first()
        if user.password == password:
            return request_success({"token": generate_jwt_token(userName)})
        else:
            return request_failed(2 ,"Wrong password", 401)
    else:
        return request_failed(1, "User does not exist", 401)

def check_require(body):
    userName = require(body, "userName", "string", err_msg="Missing or error type of [userName]")
    phoneNumber = require(body, "phoneNumber", "string", err_msg="Missing or error type of [phoneNumber]")
    email = require(body, "email", "string", err_msg="Missing or error type of [email]")
    pattern_whitelist = r'^[0-9a-zA-Z_]+$'
    pattern_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    pattern_phoneNumber = r"^\d{11}$"
    assert 0 < len(userName) <= MAX_CHAR_LENGTH, "Bad length of [userName]"
    assert re.match(pattern_whitelist, userName), f"[userName] contains illegal character(s):{re.sub(r'[0-9a-zA-Z_]', '', userName)}"
    assert re.match(pattern_phoneNumber, phoneNumber), "Bad format of [phoneNumber]"
    assert re.match(pattern_email, email), "Bad format of [email]"
    return userName, phoneNumber, email
    
@CheckRequire
def register(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    
    # Request body example: {"userName": "Ashitemaru", "password": "123456"}
    body = json.loads(req.body.decode("utf-8"))
    
    password = require(body, "password", "string", err_msg="Missing or error type of [password]")
    pattern_whitelist = r'^[0-9a-zA-Z_]+$'
    assert 0 < len(password) <= MAX_CHAR_LENGTH, "Bad length of [password]"
    assert re.match(pattern_whitelist,password), f"[password] contains illegal character(s):{re.sub(r'[0-9a-zA-Z_]', '', password)}"
    userName, phoneNumber, email = check_require(body)
    
    if User.objects.filter(userName=userName).exists():
        return request_failed(1,"User already exists", 401)
    else:
        User.objects.create(userName=userName, password=password, phoneNumber=phoneNumber, email=email, nickname=userName)
        return request_success()
    
@CheckRequire
def user_board(req: HttpRequest, userName:any) :
    user_name = require({"userName": userName}, "userName", "string", err_msg="Bad param [userName]", err_code=-1)
    user = User.objects.filter(userName = user_name).first()
    if req.method == "GET":

        if user:
            jwt_token = req.headers.get("Authorization")
            print(jwt_token) #Debug
            data = check_jwt_token(jwt_token)
            if data == None:
                return request_failed(2,"Invalid or expired JWT",401)
            if user.userName != data["userName"]:
                return request_failed(3, "Cannot view info of other users",403)
            return_data = {
                "userData": {
                    "userName": user.userName,
                    "nickname": user.nickname,
                    "phoneNumber": user.phoneNumber,
                    "email": user.email
                }
            }
            return request_success(return_data)
        else:
            return request_failed(1,"User not found" , 404)
    
    elif req.method == "DELETE":
        if user:
            jwt_token = req.headers.get("Authorization")
            print(jwt_token) #Debug
            data = check_jwt_token(jwt_token)
            if data == None:
                return request_failed(2,"Invalid or expired JWT", 401)
            if user.userName != data["userName"]:
                return request_failed(3, "Cannot delete other users", 403)
            else:
                user.delete()
                return request_success({
                    "info": "Successfully deleted user"
                })
        else:
            return request_failed(1 ,"User not found" , 404)
    else:
        return BAD_METHOD

@CheckRequire
def search_user(req: HttpRequest, userName:any) :
    userName = require({"userName": userName}, "userName", "string", err_msg="Bad param [userName]", err_code=-1)
    pattern_whitelist = r'^[0-9a-zA-Z_]+$'
    assert re.match(pattern_whitelist, userName), f"[userName] contains illegal character(s):{re.sub(r'[0-9a-zA-Z_]', '', userName)}"
    user = User.objects.filter(userName = userName).first()
    if req.method == "GET":
        
        if user:
            return_data = {
                "userData": {
                    "userName": user.userName,
                    "nickname": user.nickname,
                    "phoneNumber": user.phoneNumber,
                    "email": user.email
                }
            }
            return request_success(return_data)
        else:
            return request_failed(1,"User not found" , 404) 
    else:
        return BAD_METHOD
    
@CheckRequire
def send_friend_request(req: HttpRequest, receiverName:any) :
    if req.method != "POST":
        return BAD_METHOD
    
    body = json.loads(req.body.decode("utf-8"))
    senderName = require(body, "senderName", "string", err_msg="Missing or error type of [sender]")
    sendBySearch = require(body, "sendBySearch", "boolean", err_msg="Missing or error type of [sendBySearch]")
    requestMessage = require(body, "requestMessage", "string", err_msg="Missing or error type of [requestMessage]")
    pattern_whitelist = r'^[0-9a-zA-Z_]+$'
    assert re.match(pattern_whitelist, receiverName), f"[getterName] contains illegal character(s):{re.sub(r'[0-9a-zA-Z_]', '', receiverName)}"
    assert re.match(pattern_whitelist, senderName), f"[sender] contains illegal character(s):{re.sub(r'[0-9a-zA-Z_]', '', senderName)}"
    
    receiver = User.objects.filter(userName = receiverName).first()
    jwt_token = req.headers.get("Authorization")
    data = check_jwt_token(jwt_token)
    if data == None:
        return request_failed(2,"Invalid or expired JWT", 401)
    if senderName != data["userName"]:
        return request_failed(2,"Invalid request", 401)
    sender = User.objects.filter(userName = senderName).first()
    if sender:
        if receiver:
            if senderName == receiverName:
                return request_failed(4,"Cannot send friend request to yourself", 400)
            else:
                friends = sender.friends
                if friends.filter(userName = receiverName):
                    return request_failed(5, "He/She is already your friend", 400)
                else:
                    friendRequestToHim = FriendRequest.objects.filter(sender=sender, receiver=receiver).last()
                    if friendRequestToHim:
                        if friendRequestToHim.status == 0:
                            return request_failed(3,"Friend request already exists", 400)
                        # else: continue
                    friendRequestToMe = FriendRequest.objects.filter(sender=receiver, receiver=sender).last()
                    if friendRequestToMe:
                        if friendRequestToMe.status == 0:
                            return request_failed(6,"He/she has already sent a friend request to you, please handle it first", 400)
                    FriendRequest.objects.create(sender=sender, receiver=receiver, sendBySearch=sendBySearch, requestMessage=requestMessage)
                    return request_success()
        else:
            return request_failed(1,"Target user not found" , 404)
        
    else:
        return request_failed(1,"Sender not found" , 404)
    
@CheckRequire
def friend_request(req: HttpRequest, userName:any): 
    jwt_token = req.headers.get("Authorization")
    data = check_jwt_token(jwt_token)
    receiver = User.objects.filter(userName = userName).first()
    if data == None:
        return request_failed(2,"Invalid or expired JWT", 401)
    if userName != data["userName"]:
        return request_failed(3,"Can not view other's friend requests", 403)
      
    if req.method == "GET":
        requests = FriendRequest.objects.filter(receiver=receiver)
        return_data = {
            "info": "Successfully retrieved friend requests",
            "data": [
                return_field(request.serialize(),["request_id","sender","receiver","created_time","sendBySearch","requestMessage","status"]) for request in requests
            ]
        }
        return request_success(return_data)
    
    elif req.method == "POST":
        receiver = User.objects.filter(userName = userName).first()
        body = json.loads(req.body.decode("utf-8"))
        request_id = require(body, "request_id", "int", err_msg="Missing or error type of [request_id]")
        accept = require(body, "accept", "boolean", err_msg="Missing or error type of [accept]")
        friendRequest = FriendRequest.objects.filter(request_id = request_id).first()
        sender = friendRequest.sender
        if friendRequest:
            if accept:
                friendRequest.status = 1
                receiver.friends.add(sender)
                receiver.save()
            else:
                friendRequest.status = -1
            friendRequest.save()
            return request_success()
        else:
            return request_failed(1,"Not Found" , 404)
        
@CheckRequire
def friend_list(req: HttpRequest, userName: any):
    jwt_token = req.headers.get("Authorization")
    data = check_jwt_token(jwt_token)
    if data == None:
        return request_failed(2,"Invalid or expired JWT", 401)
    if userName != data["userName"]:
        return request_failed(3,"Can not view other's friend list", 403)
    
    if req.method != 'GET':
        return BAD_METHOD
    user = User.objects.filter(userName = userName).first()
    friends = user.friends.all()
    sorted_friends = sorted(friends, key=lambda x: x.nickname)
    return_data = {
        "friendDataList":[
            return_field(friend.serialize(),["nickname"]) for friend in sorted_friends
        ]
    }
    return request_success(return_data)

@CheckRequire
def friend_detail(req: HttpRequest, userName: any, friendName: any):
    user = User.objects.filter(userName = userName).first()
    friend = user.friends.filter(userName = friendName).first()
    if friend == None:
        return request_failed(1, "Friend Not Found", 404)
    if req.method == "GET":
        return_data = {
            "userData":
                # TODO: add in friend's tag
                return_field(friend.serialize(), ['userName','phoneNumber','email'])
        }
        return request_success(return_data)
    elif req.method == "DELETE":
        jwt_token = req.headers.get("Authorization")
        data = check_jwt_token(jwt_token)
        if data == None:
            return request_failed(2,"Invalid or expired JWT", 401)
        if userName != data["userName"]:
            return request_failed(3,"Can not delete other's friend", 403)
        user.friends.remove(friend)
        user.save()
        return request_success()
    else:
        return BAD_METHOD