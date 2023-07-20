from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from dailydoodles_api.tasks.api.v1.permissions import IsOwner
from dailydoodles_api.tasks.api.v1.serializers import TaskListSerializer, TaskSerializer
from dailydoodles_api.tasks.models import Task, TaskList


class TaskListCreateAPIView(ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(user=user)


class TaskDetailAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(user=user)


class TaskListListCreateAPIView(ListCreateAPIView):
    queryset = TaskList.objects.all()
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        user = self.request.user
        return TaskList.objects.filter(user=user)


class TaskListDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = TaskList.objects.all()
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        user = self.request.user
        return TaskList.objects.filter(user=user)
