from django.db import models

class recommendations(models.Model):
    row = models.CharField(max_length=2)
    cell = models.CharField(max_length=2)
    score = models.CharField(max_length=2)