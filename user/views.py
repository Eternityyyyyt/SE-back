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
    
    userName = require(body, "userName", "string", err_msg="Missing or error type of [userName]")
    password = require(body, "password", "string", err_msg="Missing or error type of [password]")
    
    # TODO Start: [Student] Finish the login function according to the comments below
    # If the user does not exist, create a new user and save; while if the user exists, check the password
    if User.objects.filter(userName=userName).exists():
        user = User.objects.filter(userName=userName).first()
        if user.password == password:
            return request_success({"token": generate_jwt_token(userName)})
        else:
            return request_failed("Wrong password", 401)
    else:
        return request_failed("User does not exist", 401)

def check_require(body):
    userName = require(body, "userName", "string", err_msg="Missing or error type of [userName]")
    phoneNumber = require(body, "phoneNumber", "string", err_msg="Missing or error type of [phoneNumber]")
    email = require(body, "email", "string", err_msg="Missing or error type of [email]")
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    assert 0 < len(userName) <= MAX_CHAR_LENGTH, "Bad length of [userName]"
    assert len(phoneNumber) == 11, "Bad length of [phoneNumber]"
    assert re.match(pattern, email), "Bad format of [email]"
    return userName, phoneNumber, email
    
@CheckRequire
def register(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    
    # Request body example: {"userName": "Ashitemaru", "password": "123456"}
    body = json.loads(req.body.decode("utf-8"))
    
    password = require(body, "password", "string", err_msg="Missing or error type of [password]")
    
    userName, phoneNumber, email = check_require(body)
    
    if User.objects.filter(userName=userName).exists():
        return request_failed("User already exists", 401)
    else:
        User.objects.create(userName=userName, password=password, phoneNumber=phoneNumber, email=email)
        return request_success({"token": generate_jwt_token(userName)})
    
@CheckRequire
def user_board(req: HttpRequest, userName:any) :
    user_name = require({"userName": userName}, "userName", "string", err_msg="Bad param [userName]", err_code=-1)
    assert 0 < len(user_name) <= 50, "Bad param [userName]"
    user = User.objects.filter(userName = user_name).first()
    if req.method == "GET":

        if user:
            jwt_token = req.headers.get("Authorization")
            data = check_jwt_token(jwt_token)
            if data == None:
                return request_failed("Invalid or expired JWT",401)
            if user.userName != data["userName"]:
                return request_failed("Cannot view info of other users",403)
            return_data = {
                "userName": user.userName,
                "phoneNumber": user.phoneNumber,
                "email": user.email,
                "info": "Get user info succeeded"
            }
            return request_success(return_data)
        else:
            return request_failed("User not found" , 404)
    
    elif req.method == "DELETE":
        if user:
            jwt_token = req.headers.get("Authorization")
            data = check_jwt_token(jwt_token)
            if data == None:
                return request_failed("Invalid or expired JWT", 401)
            if user.userName != data["userName"]:
                return request_failed("Cannot delete other users", 403)
            else:
                user.delete()
                return request_success({
                    "info": "Successfully deleted user"
                })
        else:
            return request_failed("User not found" , 404)
    else:
        return BAD_METHOD
