from django.db import models


class Result(models.Model):
    question_text = models.CharField(max_length=255)
    label_result = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
