from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from dailydoodles_api.tasks.api.v1.permissions import IsOwner
from dailydoodles_api.tasks.api.v1.serializers import TaskListSerializer, TaskSerializer
from dailydoodles_api.tasks.models import Task, TaskList


class TaskListCreateAPIView(ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.tasks.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TaskDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsOwner]


class TaskListListCreateAPIView(ListCreateAPIView):
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.task_lists.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TaskListDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = TaskList.objects.all()
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated, IsOwner]
