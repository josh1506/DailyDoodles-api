from rest_framework import serializers

from dailydoodles_api.tasks.models import Task, TaskList


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "description",
            "task_list",
            "is_completed",
            "due_date",
        )


class TaskListSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = TaskList
        fields = ("id", "title", "tasks")
