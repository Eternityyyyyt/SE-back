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