from utils import utils_time
from django.db import models
from utils.utils_request import return_field

from utils.utils_require import MAX_CHAR_LENGTH

# Create your models here.

class User(models.Model):
    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=MAX_CHAR_LENGTH, unique=True)
    password = models.CharField(max_length=MAX_CHAR_LENGTH)
    created_time = models.FloatField(default=utils_time.get_timestamp)
    phonenumber = models.CharField(max_length=11)
    email = models.CharField(max_length=MAX_CHAR_LENGTH)
    class Meta:
        indexes = [models.Index(fields=["name"])]
        
    def serialize(self):
        return {
            "id": self.id, 
            "name": self.name, 
            "createdAt": self.created_time,
        }
    
    def __str__(self) -> str:
        return self.name