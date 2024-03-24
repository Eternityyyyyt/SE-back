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
    
    username = require(body, "username", "string", err_msg="Missing or error type of [userName]")
    password = require(body, "password", "string", err_msg="Missing or error type of [password]")
    

    if User.objects.filter(username=username).exists():
        user = User.objects.filter(username=username).first()
        if user.password == password:
            return request_success({"token": generate_jwt_token(username)})
        else:
            return request_failed("Wrong password", 401)
    else:
        return request_failed("User does not exist", 401)

def check_require(body):
    username = require(body, "username", "string", err_msg="Missing or error type of [userName]")
    phonenumber = require(body, "phonenumber", "string", err_msg="Missing or error type of [phonenumber]")
    email = require(body, "email", "string", err_msg="Missing or error type of [email]")
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    assert 0 < len(username) <= MAX_CHAR_LENGTH, "Bad length of [username]"
    assert len(phonenumber) == 11, "Bad length of [phonenumber]"
    assert re.match(pattern, email), "Bad format of [email]"
    return username, phonenumber, email
    
@CheckRequire
def register(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    
    # Request body example: {"userName": "Ashitemaru", "password": "123456"}
    body = json.loads(req.body.decode("utf-8"))
    
    password = require(body, "password", "string", err_msg="Missing or error type of [password]")
    
    username, phonenumber, email = check_require(body)
    
    if User.objects.filter(username=username).exists():
        return request_failed("User already exists", 401)
    else:
        User.objects.create(username=username, password=password, phonenumber=phonenumber, email=email)
        return request_success({"token": generate_jwt_token(username)})