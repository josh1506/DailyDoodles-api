from django.urls import path

from dailydoodles_api.tasks.api.v1.views import (
    TaskDetailAPIView,
    TaskListCreateAPIView,
    TaskListDetailAPIView,
    TaskListListCreateAPIView,
)

urlpatterns = [
    path("task-lists", TaskListCreateAPIView.as_view(), name="task-lists"),
    path("task-lists/<int:pk>", TaskDetailAPIView.as_view(), name="task-detail"),
    path("tasklist-lists", TaskListListCreateAPIView.as_view(), name="tasklist-lists"),
    path("tasklist-lists/<int:pk>", TaskListDetailAPIView.as_view(), name="tasklist-detail"),
]
