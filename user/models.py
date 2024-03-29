from utils import utils_time
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
        }
    
    def __str__(self) -> str:
        return self.userName

class FriendRequest:
    request_id = models.BigAutoField(primary_key=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sender")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="receiver")
    sendBySearch = models.BooleanField(default=False)
    requstMessage = models.CharField(max_length=100,default="")
    created_time = models.FloatField(default=utils_time.get_timestamp)
    status = models.IntegerField(default=0)
    class Meta:
        indexes = [models.Index(fields=["sender", "receiver"])]
        
    def serialize(self):
        return {
            "request_id": self.request_id,
            "sender": return_field(self.sender),
            "receiver": return_field(self.receiver),
            "sendBySearch": self.sendBySearch,
            "requstMessage": self.requstMessage,
            "created_time": self.created_time,
            "status": self.status
        }