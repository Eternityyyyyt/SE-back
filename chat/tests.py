from django.test import TestCase
from user.models import User,FriendRequest
from chat.models import Chat,Message,GroupNotice
from typing import Optional
import datetime
import hashlib
import hmac
import time
import json
import base64
import random
from utils import utils_time

from utils.utils_jwt import EXPIRE_IN_SECONDS, SALT, b64url_encode

# Create your tests here.
class UserTest(TestCase):
    def setUp(self) -> None:
        test_user_name = "testuser"
        testuser = User.objects.create(userName="testuser",password = "123456", phoneNumber ="12345678901", email = "qwe@qwe.qwe",nickname = "测试" )
        testuser2 = User.objects.create(userName="testuser2",password = "123456", phoneNumber ="12345678901", email = "qwe@qwe.qwe",nickname = "测试2" )
        testuser3 = User.objects.create(userName="testuser3",password = "123456", phoneNumber ="12345678901", email = "qwe@qwe.qwe",nickname = "测试3" )
        testuser4 = User.objects.create(userName="testuser4",password = "123456", phoneNumber ="12345678901", email = "qwe@qwe.qwe",nickname = "测试4" )
        testuser5 = User.objects.create(userName="testuser5",password = "123456", phoneNumber ="12345678901", email = "qwe@qwe.qwe",nickname = "测试5")
        testuser.friends.add(testuser2)
        testuser.friends.add(testuser4)
        testuser.friends.add(testuser5)
        chat = Chat.objects.create(chatName = "testuser and testuser2")
        chat.memberList.add(testuser2)
        chat.memberList.add(testuser)
        messge = Message.objects.create(belongToChat=chat, content="a message sent by testuser!",sender=testuser)
        groupChat = Chat.objects.create(chatName = "testuser, testuser4, testuser5", isGroup=True, owner=testuser)
        groupChat.memberList.add(testuser4)
        groupChat.memberList.add(testuser5)
        groupChat.memberList.add(testuser)
        
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
    def test_create_private_chat_success(self):
        creater = "testuser"
        member = "testuser3"
        userCreater = User.objects.filter(userName=creater).first()
        userMember = User.objects.filter(userName=member).first()
        userCreater.friends.add(userMember)
        headers = self.generate_header(username="testuser")
        data = {
            "createrName": creater,
            "memberName": member
        }
        res = self.client.post("/chat/createPrivate",data=data, content_type="application/json", **headers)
        self.assertEqual(res.status_code , 200)
        self.assertEqual(res.json()['code'] , 0)
        self.assertEqual(res.json()['data']['alreadyCreated'],False)
        self.assertEqual(res.json()['data']['chat_id'],3)
    def test_create_private_chat_not_friend(self):
        creater = "testuser"
        member = "testuser3"
        headers = self.generate_header(username="testuser")
        data = {
            "createrName": creater,
            "memberName": member
        }
        res = self.client.post("/chat/createPrivate",data=data, content_type="application/json", **headers)
        self.assertEqual(res.status_code , 403)
        self.assertEqual(res.json()['code'] , 3)
    def test_create_private_chat_exist_success(self):     
        creater = "testuser"
        member = "testuser2"
        headers = self.generate_header(username="testuser")
        data = {
            "createrName": creater,
            "memberName": member
        }
        res = self.client.post("/chat/createPrivate",data=data, content_type="application/json", **headers)
        self.assertEqual(res.status_code , 200)
        self.assertEqual(res.json()['code'] , 0)
        self.assertEqual(res.json()['data']['alreadyCreated'],True)
    def test_create_private_chat_with_wrong_jwt(self):
        creater = "testuser"
        member = "testuser2"
        userCreater = User.objects.filter(userName=creater).first()
        userMember = User.objects.filter(userName=member).first()
        userCreater.friends.add(userMember)
        headers = self.generate_header(username="nottestuser")
        data = {
            "createrName": creater,
            "memberName": member
        }
        res = self.client.post("/chat/createPrivate",data=data, content_type="application/json", **headers)
        self.assertEqual(res.status_code , 401)
        self.assertEqual(res.json()['code'] , 2)
    def test_create_private_chat_creater_not_exist(self):
        creater = "notexistuser"
        member = "testuser2"
        headers = self.generate_header(username="notexist")
        data = {
            "createrName": creater,
            "memberName": member
        }
        res = self.client.post("/chat/createPrivate",data=data, content_type="application/json", **headers)
        self.assertEqual(res.status_code , 404)
        self.assertEqual(res.json()['code'] , 1)

    #Test posting message
    def test_post_message_in_private_chat_success(self):
        member1 = "testuser"
        member2 = "testuser2"
        headers = self.generate_header(username=member1)
        data = {
            "userName": member1,
            "chat_id": 1,
            "content": "Hello, I am your father",
            "replying": 0
        }
        res = self.client.post("/chat/message",data=data, content_type="application/json", **headers)
        self.assertEqual(res.status_code , 200)
        self.assertEqual(res.json()['code'] , 0)

    def test_post_message_in_private_chat_not_exist(self):
        member1 = "testuser"
        member2 = "testuser2"
        headers = self.generate_header(username=member1)
        data = {
            "userName": member1,
            "chat_id": 100,
            "content": "Hello, I am your father",
            "replying": 0
        }
        res = self.client.post("/chat/message",data=data, content_type="application/json", **headers)
        self.assertEqual(res.status_code , 404)
        self.assertEqual(res.json()['code'] , 1)
    def test_post_message_in_private_chat_user_not_in_chat(self):
        member1 = "testuser3"
        headers = self.generate_header(username=member1)
        data = {
            "userName": member1,
            "chat_id": 1,
            "content": "Hello, I am your father",
            "replying": 0
        }
        res = self.client.post("/chat/message",data=data, content_type="application/json", **headers)
        self.assertEqual(res.status_code , 404)
        self.assertEqual(res.json()['code'] , 3)

    def test_post_message_in_private_chat_wrong_jwt(self):
        member1 = "testuser"
        member2 = "testuser2"
        headers = self.generate_header(username="nottestuser")
        data = {
            "userName": member1,
            "chat_id": 1,
            "content": "Hello, I am your father",
            "replying": 0
        }
        res = self.client.post("/chat/message",data=data, content_type="application/json", **headers)
        self.assertEqual(res.status_code , 401)
        self.assertEqual(res.json()['code'] , 2)

    def test_get_message_in_private_chat_success(self):
        testuser = User.objects.filter(userName="testuser").first()
        chat = Chat.objects.filter(chat_id = 1).first()
        message = Message.objects.create(belongToChat=chat, content="a message sent by testuser",sender=testuser)
        message.default_visible_to_user_list()
        message.save()
        headers = self.generate_header(username="testuser")
        url = "/chat/message?userName=testuser&chat_id=1&after=0&limit=100"
        res = self.client.get(url,data={}, **headers)
        self.assertEqual(res.status_code , 200)
        self.assertEqual(res.json()['code'] , 0)
    
    def test_get_chat_info_user_not_exist(self):
        headers = self.generate_header(username="notexistuser")
        url = "/chat/chat?chat_id=1&userName=notexistuser"
        res = self.client.get(url, data={}, content_type = "application/json",**headers)
        self.assertEqual(res.status_code , 404)
        self.assertEqual(res.json()['code'] , 1)
    
    def test_get_chat_info_wrong_jwt(self):
        headers = self.generate_header(username="youknowwho")
        url = "/chat/chat?chat_id=1&chat_id=2&userName=testuser"
        res = self.client.get(url, data={}, content_type = "application/json",**headers)
        self.assertEqual(res.status_code , 401)
        self.assertEqual(res.json()['code'] , 2)
    
    def test_get_chat_info_success(self):
        headers = self.generate_header(username="testuser")
        url = "/chat/chat?chat_id=1&userName=testuser"
        res = self.client.get(url, data={}, content_type = "application/json",**headers)
        self.assertEqual(res.status_code , 200)
        self.assertEqual(res.json()['code'] , 0)
        self.assertEqual(res.json()['data'][0]['chat_id'],1)
        self.assertEqual(res.json()['data'][0]['chat_status'],0)
    
    def test_get_chat_info_not_exist(self):
        headers = self.generate_header(username="testuser")
        url = "/chat/chat?chat_id=10&userName=testuser"
        res = self.client.get(url, data={}, content_type = "application/json",**headers)
        self.assertEqual(res.status_code , 200)
        self.assertEqual(res.json()['code'] , 0)
        self.assertEqual(res.json()['data'][0]['chat_id'],'10')
        self.assertEqual(res.json()['data'][0]['chat_status'],1)
        
    def test_get_chat_info_user_not_in_chat(self):
        headers = self.generate_header(username="testuser3")
        url = "/chat/chat?chat_id=1&userName=testuser3"
        res = self.client.get(url, data={}, content_type = "application/json",**headers)
        self.assertEqual(res.status_code , 200)
        self.assertEqual(res.json()['code'] , 0)
        self.assertEqual(res.json()['data'][0]['chat_id'],'1')
        self.assertEqual(res.json()['data'][0]['chat_status'],2)
        
    def test_post_already_read_messages_success(self):
        headers = self.generate_header(username="testuser")
        data = {
            "userName": "testuser",
            "chat_id": 1,
            "after": utils_time.get_timestamp()
        }
        res = self.client.post("/chat/readMessage",data=data, content_type="application/json", **headers)
        self.assertEqual(res.status_code , 200)
        self.assertEqual(res.json()['code'] , 0)
        
    def test_post_already_read_messages_user_not_exits(self):
        headers = self.generate_header(username="youknowwho")
        data = {
            "userName": "youknowwho",
            "chat_id": 1,
            "after": utils_time.get_timestamp()
        }
        res = self.client.post("/chat/readMessage",data=data, content_type="application/json", **headers)
        self.assertEqual(res.status_code , 404)
        self.assertEqual(res.json()['code'] , 1)
        
    def test_post_already_read_messages_chat_not_exists(self):
        headers = self.generate_header(username="testuser")
        data = {
            "userName": "testuser",
            "chat_id": 100,
            "after": utils_time.get_timestamp()
        }
        res = self.client.post("/chat/readMessage",data=data, content_type="application/json", **headers)
        self.assertEqual(res.status_code , 404)
        self.assertEqual(res.json()['code'] , 1)
        
    def test_post_already_read_messages_wrong_jwt(self):
        headers = self.generate_header(username="youknowwho")
        data = {
            "userName": "testuser",
            "chat_id": 1,
            "after": utils_time.get_timestamp()
        }
        res = self.client.post("/chat/readMessage",data=data, content_type="application/json", **headers)
        self.assertEqual(res.status_code , 401)
        self.assertEqual(res.json()['code'] , 2)
        
    def test_post_already_read_messages_bad_method(self):
        headers = self.generate_header(username="testuser")
        data = {
            "userName": "testuser",
            "chat_id": 1,
            "after": utils_time.get_timestamp()
        }
        res = self.client.delete("/chat/readMessage",data=data, content_type="application/json", **headers)
        self.assertEqual(res.status_code , 405)
        self.assertEqual(res.json()['code'] , -3)
        
    def test_get_message_read_status_success(self):
        headers = self.generate_header(username="testuser")
        url = "/chat/messageReadStatus?userName=testuser&message_id=1"
        res = self.client.get(url, data={}, content_type = "application/json",**headers)
        self.assertEqual(res.status_code , 200)
        self.assertEqual(res.json()['code'] , 0)
        
    def test_get_message_read_status_wrong_jwt(self):
        headers = self.generate_header(username="youknowwho")
        url = "/chat/messageReadStatus?userName=testuser&message_id=1"
        res = self.client.get(url, data={}, content_type = "application/json",**headers)
        self.assertEqual(res.status_code , 401)
        self.assertEqual(res.json()['code'] , 2)
        
    def test_get_message_read_status_user_not_found(self):
        headers = self.generate_header(username="youknowwho")
        url = "/chat/messageReadStatus?userName=youknowwho&message_id=1"
        res = self.client.get(url, data={}, content_type = "application/json",**headers)
        self.assertEqual(res.status_code , 404)
        self.assertEqual(res.json()['code'] , 1)
        
    def test_get_message_read_status_message_not_found(self):
        headers = self.generate_header(username="testuser")
        url = "/chat/messageReadStatus?userName=testuser&message_id=100"
        res = self.client.get(url, data={}, content_type = "application/json",**headers)
        self.assertEqual(res.status_code , 404)
        self.assertEqual(res.json()['code'] , 1)
        
    def test_create_group_success(self):
        headers = self.generate_header(username="testuser")
        data = {
            "userName": "testuser",
            "memberList": [
                "testuser2",
                "testuser4",
                "testuser5"
            ]
        }
        res = self.client.post("/chat/createGroup", data=data, content_type="application/json",**headers)
        self.assertEqual(res.status_code , 200)
        self.assertEqual(res.json()['code'] , 0)
    
    def test_create_group_wrong_jet(self):
        headers = self.generate_header(username="youknowwho")
        data = {
            "userName": "testuser",
            "memberList": [
                "testuser2",
                "testuser4",
                "testuser5"
            ]
        }
        res = self.client.post("/chat/createGroup", data=data, content_type="application/json",**headers)
        self.assertEqual(res.status_code , 401)
        self.assertEqual(res.json()['code'] , 2)
        
    def test_create_group_user_not_exist(self):
        headers = self.generate_header(username="youknowwho")
        data = {
            "userName": "youknowwho",
            "memberList": [
                "testuser2",
                "testuser4",
                "testuser5"
            ]
        }
        res = self.client.post("/chat/createGroup", data=data, content_type="application/json",**headers)
        self.assertEqual(res.status_code , 404)
        self.assertEqual(res.json()['code'] , 1)
        
    def test_create_group_member_less_than_3(self):
        headers = self.generate_header(username="testuser")
        data = {
            "userName": "testuser",
            "memberList": [
                "testuser2",
            ]
        }
        res = self.client.post("/chat/createGroup", data=data, content_type="application/json",**headers)
        self.assertEqual(res.status_code , 400)
        self.assertEqual(res.json()['code'] , 3)
        
    def test_create_group_not_friend(self):
        headers = self.generate_header(username="testuser")
        data = {
            "userName": "testuser",
            "memberList": [
                "testuser2",
                "testuser3",
                "testuser5"
            ]
        }
        res = self.client.post("/chat/createGroup", data=data, content_type="application/json",**headers)
        self.assertEqual(res.status_code , 400)
        self.assertEqual(res.json()['code'] , 4)
        
    def test_set_group_admin_success(self):
        headers = self.generate_header(username="testuser")
        data = {
            "ownerName": "testuser",
            "chat_id": 2,
            "adminList": [
                "testuser4"
            ]
        }
        res = self.client.post("/chat/setAdmin", data=data, content_type="application/json",**headers)
        self.assertEqual(res.status_code , 200)
        self.assertEqual(res.json()['code'] , 0)
        
    def test_set_group_admin_wrong_jwt(self):
        headers = self.generate_header(username="youknowwho")
        data = {
            "ownerName": "testuser",
            "chat_id": 2,
            "adminList": [
                "testuser4"
            ]
        }
        res = self.client.post("/chat/setAdmin", data=data, content_type="application/json",**headers)
        self.assertEqual(res.status_code , 401)
        self.assertEqual(res.json()['code'] , 2)
        
    def test_set_group_admin_owner_not_exist(self):
        headers = self.generate_header(username="testuser")
        data = {
            "ownerName": "youknowwho",
            "chat_id": 2,
            "adminList": [
                "testuser4"
            ]
        }
        res = self.client.post("/chat/setAdmin", data=data, content_type="application/json",**headers)
        self.assertEqual(res.status_code , 404)
        self.assertEqual(res.json()['code'] , 1)
        
    def test_set_group_admin_chat_not_exist(self):
        headers = self.generate_header(username="testuser")
        data = {
            "ownerName": "testuser",
            "chat_id": 100,
            "adminList": [
                "testuser4"
            ]
        }
        res = self.client.post("/chat/setAdmin", data=data, content_type="application/json",**headers)
        self.assertEqual(res.status_code , 404)
        self.assertEqual(res.json()['code'] , 1)
        
    def test_set_group_admin_not_owner(self):
        headers = self.generate_header(username="testuser2")
        data = {
            "ownerName": "testuser2",
            "chat_id": 2,
            "adminList": [
                "testuser4"
            ]
        }
        res = self.client.post("/chat/setAdmin", data=data, content_type="application/json",**headers)
        self.assertEqual(res.status_code , 403)
        self.assertEqual(res.json()['code'] , 3)
        
    def test_set_group_admin_not_in_chat(self):
        headers = self.generate_header(username="testuser")
        data = {
            "ownerName": "testuser",
            "chat_id": 2,
            "adminList": [
                "testuser3"
            ]
        }
        res = self.client.post("/chat/setAdmin", data=data, content_type="application/json",**headers)
        self.assertEqual(res.status_code , 403)
        self.assertEqual(res.json()['code'] , 4)
        
    def test_change_group_owner_success(self):
        headers = self.generate_header(username="testuser")
        data = {
            "ownerName": "testuser",
            "chat_id": 2,
            "newOwnerName": "testuser4"
        }
        res = self.client.post("/chat/changeOwner", data=data, content_type="application/json",**headers)
        self.assertEqual(res.status_code , 200)
        self.assertEqual(res.json()['code'] , 0)
        
    def test_change_group_owner_wrong_jwt(self):
        headers = self.generate_header(username="youknowwho")
        data = {
            "ownerName": "testuser",
            "chat_id": 2,
            "newOwnerName": "testuser4"
        }
        res = self.client.post("/chat/changeOwner", data=data, content_type="application/json",**headers)
        self.assertEqual(res.status_code , 401)
        self.assertEqual(res.json()['code'] , 2)
        
    def test_change_group_owner_owner_not_exist(self):
        headers = self.generate_header(username="youknowwho")
        data = {
            "ownerName": "youknowwho",
            "chat_id": 2,
            "newOwnerName": "testuser4"
        }
        res = self.client.post("/chat/changeOwner", data=data, content_type="application/json",**headers)
        self.assertEqual(res.status_code , 404)
        self.assertEqual(res.json()['code'] , 1)
        
    def test_change_group_owner_chat_not_exist(self):
        headers = self.generate_header(username="testuser")
        data = {
            "ownerName": "testuser",
            "chat_id": 100,
            "newOwnerName": "testuser4"
        }
        res = self.client.post("/chat/changeOwner", data=data, content_type="application/json",**headers)
        self.assertEqual(res.status_code , 404)
        self.assertEqual(res.json()['code'] , 1)
        
    def test_change_group_owner_newOwner_not_exist(self):
        headers = self.generate_header(username="testuser")
        data = {
            "ownerName": "testuser",
            "chat_id": 100,
            "newOwnerName": "testuser100"
        }
        res = self.client.post("/chat/changeOwner", data=data, content_type="application/json",**headers)
        self.assertEqual(res.status_code , 404)
        self.assertEqual(res.json()['code'] , 1)
        
    def test_change_group_owner_not_owner(self):
        headers = self.generate_header(username="testuser2")
        data = {
            "ownerName": "testuser2",
            "chat_id": 2,
            "newOwnerName": "testuser4"
        }
        res = self.client.post("/chat/changeOwner", data=data, content_type="application/json",**headers)
        self.assertEqual(res.status_code , 403)
        self.assertEqual(res.json()['code'] , 3)
        
    def test_change_group_owner_not_in_group(self):
        headers = self.generate_header(username="testuser")
        data = {
            "ownerName": "testuser",
            "chat_id": 2,
            "newOwnerName": "testuser3"
        }
        res = self.client.post("/chat/changeOwner", data=data, content_type="application/json",**headers)
        self.assertEqual(res.status_code , 403)
        self.assertEqual(res.json()['code'] , 4)
        
    def test_leave_group_success(self):
        headers = self.generate_header(username="testuser5")
        data = {
            "userName": "testuser5",
            "chat_id": 2
        }
        res = self.client.post("/chat/leaveGroup", data=data, content_type="application/json",**headers)
        self.assertEqual(res.status_code , 200)
        self.assertEqual(res.json()['code'] , 0)
        
    def test_leave_group_wrong_jwt(self):
        headers = self.generate_header(username="youknowwho")
        data = {
            "userName": "testuser5",
            "chat_id": 2
        }
        res = self.client.post("/chat/leaveGroup", data=data, content_type="application/json",**headers)
        self.assertEqual(res.status_code , 401)
        self.assertEqual(res.json()['code'] , 2)
        
    def test_leave_group_user_not_exist(self):
        headers = self.generate_header(username="youknowwho")
        data = {
            "userName": "youknowwho",
            "chat_id": 2
        }
        res = self.client.post("/chat/leaveGroup", data=data, content_type="application/json",**headers)
        self.assertEqual(res.status_code , 404)
        self.assertEqual(res.json()['code'] , 1)
        
    def test_leave_group_user_not_exist(self):
        headers = self.generate_header(username="testuser5")
        data = {
            "userName": "testuser5",
            "chat_id": 100
        }
        res = self.client.post("/chat/leaveGroup", data=data, content_type="application/json",**headers)
        self.assertEqual(res.status_code , 404)
        self.assertEqual(res.json()['code'] , 1)
        
    def test_leave_group_user_not_in_group(self):
        headers = self.generate_header(username="testuser3")
        data = {
            "userName": "testuser3",
            "chat_id": 2
        }
        res = self.client.post("/chat/leaveGroup", data=data, content_type="application/json",**headers)
        self.assertEqual(res.status_code , 403)
        self.assertEqual(res.json()['code'] , 3)
        
    def test_leave_group_user_is_owner(self):
        headers = self.generate_header(username="testuser")
        data = {
            "userName": "testuser",
            "chat_id": 2
        }
        res = self.client.post("/chat/leaveGroup", data=data, content_type="application/json",**headers)
        self.assertEqual(res.status_code , 403)
        self.assertEqual(res.json()['code'] , 4)