from django.db import models
import datetime

# Create your models here.
class Venue(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    lat = models.FloatField()
    lon = models.FloatField()
    
class Settings(models.Model):
    last_train_date = models.DateField(auto_now_add=True)