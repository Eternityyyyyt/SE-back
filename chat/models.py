from utils import utils_time
from datetime import datetime
from django.db import models
from utils.utils_request import return_field

from utils.utils_require import MAX_CHAR_LENGTH

from user.models import User
# Create your models here.

class Chat(models.Model):
    chat_id = models.AutoField(primary_key=True)
    chatName = models.CharField(max_length=MAX_CHAR_LENGTH)
    created_time = models.FloatField(default=utils_time.get_timestamp)
    updateTime = models.FloatField(default=utils_time.get_timestamp)
    isGroup = models.BooleanField(default=False)
    memberList = models.ManyToManyField(User, related_name='memberList')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owner')
    adminList = models.ManyToManyField(User, related_name='adminList')
    
class Message(models.Model):
    message_id = models.AutoField(primary_key=True)
    belongToChat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messageList')
    content = models.CharField(max_length=MAX_CHAR_LENGTH)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messageSender')
    created_time = models.FloatField(default=utils_time.get_timestamp)
    visibleToUserList = models.ManyToManyField(User, related_name='visibleToUserList')
    replying = models.ForeignKey('Message', on_delete=models.CASCADE, related_name='replyingMessages', null=True)
    repliedCount = models.BigIntegerField(default=0) 
    
    def default_visible_to_user_list(self):
        chat = self.belongToChat
        if chat:
            self.visibleToUserList.set(chat.memberList.all())
            self.save()

    def serialize(self):
        replyMessage = self.replying
        replyid = None
        if replyMessage:
            replyChat = replyMessage.belongToChat
            inChat = replyChat.messageList.filter(message_id = self.message_id).first()
            if inChat:
                replyid = replyMessage.message_id
        return{
            'message_id': self.message_id,
            'content': self.content,
            'sender': self.sender.nickname,
            'created_time': self.created_time,
            'replying': replyid,
            'repliedCount': self.repliedCount,
        }
            
class GroupNotice(models.Model):
    groupNotice_id = models.AutoField(primary_key=True)
    belongToChat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='noticeList')
    content = models.CharField(max_length=MAX_CHAR_LENGTH)
    created_time = models.FloatField(default=utils_time.get_timestamp)
    