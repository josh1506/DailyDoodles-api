from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from dailydoodles_api.tasks.api.v1.serializers import TaskListSerializer, TaskSerializer
from dailydoodles_api.tasks.models import Task, TaskList


class TaskListCreateAPIView(ListCreateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer


class TaskDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer


class TaskListListCreateAPIView(ListCreateAPIView):
    queryset = TaskList.objects.all()
    serializer_class = TaskListSerializer


class TaskListDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = TaskList.objects.all()
    serializer_class = TaskListSerializer
