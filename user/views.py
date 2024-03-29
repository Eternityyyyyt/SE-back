import json
import re
from django.http import HttpRequest, HttpResponse

from user.models import User
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