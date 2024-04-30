from utils import utils_time
from datetime import datetime
from django.db import models
from utils.utils_request import return_field

from utils.utils_require import MAX_CHAR_LENGTH

# Create your models here.

class User(models.Model):
    id = models.BigAutoField(primary_key=True)
    userName = models.CharField(max_length=MAX_CHAR_LENGTH, unique=True)
    password = models.CharField(max_length=MAX_CHAR_LENGTH)
    created_time = models.FloatField(default=utils_time.get_timestamp)
    phoneNumber = models.CharField(max_length=11,default="")
    email = models.CharField(max_length=MAX_CHAR_LENGTH,default="")
    nickname = models.CharField(max_length=MAX_CHAR_LENGTH,default="")
    friends = models.ManyToManyField("self", symmetrical=True)
    avatar = models.CharField(max_length=MAX_CHAR_LENGTH,default="")
    class Meta:
        indexes = [models.Index(fields=["userName"])]
        
    def serialize(self):
        return {
            "id": self.id, 
            "userName": self.userName, 
            "nickname": self.nickname,
            "phoneNumber": self.phoneNumber,
            "email": self.email,
            "created_time": self.created_time,
            "avatar": self.avatar,
        }
    
    def __str__(self) -> str:
        return self.userName

class FriendRequest(models.Model):
    request_id = models.BigAutoField(primary_key=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sender")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="receiver")
    sendBySearch = models.BooleanField(default=False)
    requestMessage = models.CharField(max_length=100,default="")
    created_time = models.FloatField(default=utils_time.get_timestamp)
    status = models.IntegerField(default=0)
    class Meta:
        indexes = [models.Index(fields=["sender", "receiver"])]
        
    def serialize(self):
        return {
            "request_id": self.request_id,
            "sender": self.sender.userName,
            "avatar": self.sender.avatar,
            "receiver": self.receiver.userName,
            "created_time": f"{datetime.fromtimestamp(int(self.created_time))}",
            "sendBySearch": self.sendBySearch,
            "requestMessage": self.requestMessage,
            "status": self.status
        }

class FriendTag(models.Model):
    tag_id = models.BigAutoField(primary_key=True)
    tagName = models.CharField(max_length=MAX_CHAR_LENGTH, unique=True)
    belongToUser = models.ForeignKey(User, on_delete=models.CASCADE, related_name="belongToUser")
    inTagUserList = models.ManyToManyField(User, symmetrical=False, related_name="inTagUserList")