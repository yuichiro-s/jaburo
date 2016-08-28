from django.db import models


class Paper(models.Model):
    paper_id = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    authors = models.CharField(max_length=200)
    year = models.IntegerField()
    conference = models.CharField(max_length=200)
    url = models.URLField()
