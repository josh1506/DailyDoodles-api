from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class TaskList(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="task_lists")

    is_deleted = models.BooleanField(default=False, blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_date = models.DateTimeField(auto_now=True, blank=True, null=True)
    deleted_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.title


class Task(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    task_list = models.ForeignKey(TaskList, on_delete=models.CASCADE, null=True, blank=True, related_name="tasks")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    is_completed = models.BooleanField(default=False, blank=False, null=False)
    due_date = models.DateField(blank=True, null=True)

    is_deleted = models.BooleanField(default=False, blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_date = models.DateTimeField(auto_now=True, blank=True, null=True)
    deleted_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.title
