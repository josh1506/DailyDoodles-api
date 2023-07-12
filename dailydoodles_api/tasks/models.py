from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class TaskList(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="task_list")
    date_created = models.DateTimeField(auto_now=True, blank=False, null=False)

    def __str__(self):
        return self.title


class Task(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    task_list = models.ForeignKey(TaskList, on_delete=models.CASCADE, null=True, blank=True, related_name="task")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="task")
    is_completed = models.BooleanField(default=False, blank=False, null=False)
    due_date = models.DateField(blank=True, null=True)
    date_created = models.DateTimeField(auto_now=True, blank=False, null=False)

    def __str__(self):
        return self.title
