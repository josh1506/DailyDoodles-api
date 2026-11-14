from rest_framework import serializers

from dailydoodles_api.tasks.models import Task, TaskList


class TaskSerializer(serializers.ModelSerializer):
    # Bounded at the API (threat model F6); the column stays TEXT, so existing rows are untouched.
    description = serializers.CharField(max_length=10_000, allow_blank=True, allow_null=True, required=False)

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

    def validate_task_list(self, value):
        # A task may only be filed under the requester's own list. Reuse DRF's "does not exist"
        # message so a foreign list id is indistinguishable from a missing one.
        if value is not None and value.user_id != self.context["request"].user.id:
            self.fields["task_list"].fail("does_not_exist", pk_value=value.pk)
        return value


class TaskListSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = TaskList
        fields = ("id", "title", "tasks")
