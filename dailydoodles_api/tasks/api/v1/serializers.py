from rest_framework import serializers

from dailydoodles_api.tasks.models import Task, TaskList


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        exclude = ("created_date", "updated_date", "is_deleted", "deleted_date")


class TaskListSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = TaskList
        exclude = ("created_date", "updated_date", "is_deleted", "deleted_date")
