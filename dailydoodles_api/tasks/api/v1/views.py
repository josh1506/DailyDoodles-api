from django.db.models import Prefetch
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from dailydoodles_api.tasks.api.v1.permissions import IsOwner
from dailydoodles_api.tasks.api.v1.serializers import TaskListSerializer, TaskSerializer
from dailydoodles_api.tasks.models import Task, TaskList

# Every queryset is scoped to the requesting user, so other users' objects answer 404
# (no existence oracle). IsOwner stays as defence in depth.


class TaskListCreateAPIView(ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Explicit order: Postgres heap order changes after UPDATE, which made tasks jump on reload.
        return Task.objects.filter(user=self.request.user).order_by("id")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TaskDetailAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)


def own_tasks(user):
    # Hide tasks other users may have filed under this list before S1 was fixed.
    return Prefetch("tasks", queryset=Task.objects.filter(user=user).order_by("id"))


class TaskListListCreateAPIView(ListCreateAPIView):
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TaskList.objects.filter(user=self.request.user).order_by("id").prefetch_related(own_tasks(self.request.user))

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TaskListDetailAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return TaskList.objects.filter(user=self.request.user).prefetch_related(own_tasks(self.request.user))
