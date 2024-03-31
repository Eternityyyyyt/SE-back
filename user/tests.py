from django.test import TestCase
from user.models import User
from typing import Optional
import datetime
import hashlib
import hmac
import time
import json
import base64
import random

# Create your tests here.

from utils.utils_jwt import EXPIRE_IN_SECONDS, SALT, b64url_encode

class UserTest(TestCase):
    def setUp(self) -> None:
        test_user_name = "testuser"
        testuser = User.objects.create(userName="testuser",password = "123456", phoneNumber ="12345678901", email = "qwe@qwe.qwe",nickname = "测试" )
        testuser2 = User.objects.create(userName="testuser2",password = "123456", phoneNumber ="12345678901", email = "qwe@qwe.qwe",nickname = "测试2" )
        return super().setUp()
    # ! Utility functions
    def generate_jwt_token(self, payload: dict, salt: str):
        # * header
        header = {
            "alg": "HS256",
            "typ": "JWT"
        }
        # dump to str. remove `\n` and space after `:`
        header_str = json.dumps(header, separators=(",", ":"))
        # use base64url to encode, instead of base64
        header_b64 = b64url_encode(header_str)
        
        # * payload
        payload_str = json.dumps(payload, separators=(",", ":"))
        payload_b64 = b64url_encode(payload_str)
        
        # * signature
        signature_str = header_b64 + "." + payload_b64
        signature = hmac.new(salt, signature_str.encode("utf-8"), digestmod=hashlib.sha256).digest()
        signature_b64 = b64url_encode(signature)
        
        return header_b64 + "." + payload_b64 + "." + signature_b64

    
    def generate_header(self, username: str, payload: dict = {}, salt: str = SALT):
        if len(payload) == 0:
            payload = {
                "iat": int(time.time()),
                "exp": int(time.time()) + EXPIRE_IN_SECONDS,
                "data": {
                    "userName": username
                }
            }
        return {
            "HTTP_AUTHORIZATION": self.generate_jwt_token(payload, salt)
        }
    
    #Test section
    def test_register_success(self):
        data = {"userName": "testreg", "password": "123456" ,"phoneNumber": "12345678901", "email": "qwe@qwe.qwe"}
        res = self.client.post('/register', data=data, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)

    def test_register_user_already_exist(self):
        data = {"userName": "testuser", "password": "123456" ,"phoneNumber": "12345678901", "email": "qwe@qwe.qwe"}
        res = self.client.post('/register', data=data, content_type='application/json')
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()['code'], 1)

    def test_register_request_missing_username(self):
        data = {"password": "123456" ,"phoneNumber": "12345678901", "email": "qwe@qwe.qwe"}
        res = self.client.post('/register', data=data, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['code'], -2)

    def test_register_request_missing_phonenumber(self):
        data = { "userName" : "testregfail", "password": "123456" , "email": "qwe@qwe.qwe"}
        res = self.client.post('/register', data=data, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['code'], -2)

    def test_register_bad_method_get(self):
        res = self.client.get('/register')
        self.assertEqual(res.status_code, 405)
        self.assertEqual(res.json()['code'], -3)

    def test_register_userName_too_long(self):
        longusername = "a"*51
        data = { "userName" : longusername, "password": "123456" ,"phoneNumber": "12345678901", "email": "qwe@qwe.qwe"}
        res = self.client.post('/register', data=data, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['code'], -2)

    def test_register_userName_bad_format_illegal_char(self):
        wrong_format_userName= ''.join ([random.choice("qwertyuiopasdfghjklzxcvbnm1234567890_") for _ in range(15)]) + random.choice(";:'<>?/!@#$%^&*()[]【】？，。¥·～")
        data = { "userName" : wrong_format_userName, "password": "123456" ,"phoneNumber": "12345678901", "email": "qwe@qwe.qwe"}
        res = self.client.post('/register', data=data, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['code'], -2)

    def test_register_password_too_long(self):
        longpassword= "a"*51
        data = { "userName" : "testregfail", "password": longpassword ,"phoneNumber": "12345678901", "email": "qwe@qwe.qwe"}
        res = self.client.post('/register', data=data, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['code'], -2)

    def test_register_phoneNumber_bad_format_too_long(self):
        wrong_length_phoneNumber= ''.join ([random.choice("0123456789") for _ in range(random.choice([3,5,7,9,12,14,16,18]))])
        data = { "userName" : "testregfail", "password": "123456" ,"phoneNumber": wrong_length_phoneNumber, "email": "qwe@qwe.qwe"}
        res = self.client.post('/register', data=data, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['code'], -2)

    def test_register_email_bad_format_illegal_char(self):
        wrong_format_phoneNumber= ''.join ([random.choice("qwertyuiopasdfghjklzxcvbnm") for _ in range(10)]) + "@"+  random.choice(";:'<>?/!@#$%^&*()[]【】？，。¥·～") + "." + ''.join ([random.choice("qwertyuiopasdfghjklzxcvbnm") for _ in range(10)]) 
        data = { "userName" : "testregfail", "password": "123456" ,"phoneNumber": wrong_format_phoneNumber, "email": "qwe@qwe.qwe"}
        res = self.client.post('/register', data=data, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['code'], -2)
    
    # Test Login
    def test_login_success(self):
        data = {"userName": "testuser", "password": "123456"}
        res = self.client.post('/login', data=data, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)
        self.assertEqual( res.json()['token'].count('.'),2)

    def test_login_user_does_not_exist(self):
        data = {"userName": "notexistuser", "password": "123456"}
        res = self.client.post('/login', data=data, content_type='application/json')
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()['code'], 1)
    
    def test_login_wrong_password(self):
        data = {"userName": "testuser", "password": "wrongpassword"}
        res = self.client.post('/login', data=data, content_type='application/json')
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()['code'], 2)
    
    #Test getUserInfo
    def test_get_user_info_success(self):
        headers = self.generate_header(username="testuser")
    
        res = self.client.get("/user/testuser",data={}, content_type="application/json", **headers)
        self.assertEqual(res.status_code , 200)
        self.assertEqual(res.json()['userData']['phoneNumber'],'12345678901')
        self.assertEqual(res.json()['userData']['email'],"qwe@qwe.qwe")
    def test_get_user_info_get_not_existing_user(self):
        headers = self.generate_header(username="testuser")
    
        res = self.client.get("/user/notexistuser",data={}, content_type="application/json", **headers)
        self.assertEqual(res.status_code , 404)
        self.assertEqual(res.json()['code'],1)
    def test_get_user_info_with_illegal_jwt(self):
        headers = {
            "HTTP_AUTHORIZATION": "an.illegaljwt"
        }
        res = self.client.get("/user/testuser",data={}, content_type="application/json", **headers)
        self.assertEqual(res.status_code , 401)
        self.assertEqual(res.json()['code'],2)
    def test_get_user_info_get_other_user(self):
        headers = self.generate_header(username="notthisuser")
    
        res = self.client.get("/user/testuser",data={}, content_type="application/json", **headers)
        self.assertEqual(res.status_code , 403)
        self.assertEqual(res.json()['code'],3)

    #Test delete user
    def test_delete_user_success(self):
        testdeleteuser = User.objects.create(userName="testdeleteuser",password = "123456", phoneNumber ="12345678901", email = "qwe@qwe.qwe",nickname = "测试" )

        headers = self.generate_header(username="testdeleteuser")
        res = self.client.delete("/user/testdeleteuser",data={}, content_type="application/json", **headers)
        self.assertEqual(res.status_code , 200)
        self.assertEqual(res.json()['code'],0)
    def test_delete_user_get_not_existing_user(self):
        headers = self.generate_header(username="testuser")
    
        res = self.client.delete("/user/notexistuser",data={}, content_type="application/json", **headers)
        self.assertEqual(res.status_code , 404)
        self.assertEqual(res.json()['code'],1)
    def test_delete_user_with_illegal_jwt(self):
        headers = {
            "HTTP_AUTHORIZATION": "an.illegaljwt"
        }
        res = self.client.delete("/user/testuser",data={}, content_type="application/json", **headers)
        self.assertEqual(res.status_code , 401)
        self.assertEqual(res.json()['code'],2)
    def test_delete_user_delete_other_user(self):
        headers = self.generate_header(username="notthisuser")
    
        res = self.client.delete("/user/testuser",data={}, content_type="application/json", **headers)
        self.assertEqual(res.status_code , 403)
        self.assertEqual(res.json()['code'],3)
    
    #Test search user
    def test_search_user_success(self):
        res = self.client.get("/searchUser/testuser")
        self.assertEqual(res.status_code , 200)
        self.assertEqual(res.json()['code'],0)
        self.assertEqual(res.json()['userData']['nickname'],'测试')
    
    def test_search_user_not_exist(self):
        res = self.client.get("/searchUser/notexistuser")
        self.assertEqual(res.status_code , 404)
        self.assertEqual(res.json()['code'],1)
    
    #Test send friend request
    def test_send_friend_request_success(self):
        #testuser send a friend request to testuser2
        headers = self.generate_header(username="testuser")
        data = {
            "senderName" :"testuser",
            "sendBySearch": True,
            "requestMessage": "I'm testuser, fuck you man"
        }
        res = self.client.post("/sendFriendRequest/testuser2",data=data,content_type='application/json',**headers)
        print(res.json()['code'])
        self.assertEqual(res.status_code , 200)
        self.assertEqual(res.json()['code'],0)