from django.urls import path

from dailydoodles_api.tasks.api.v1.views import (
    TaskDetailAPIView,
    TaskListCreateAPIView,
    TaskListDetailAPIView,
    TaskListListCreateAPIView,
)

urlpatterns = [
    path("", TaskListCreateAPIView.as_view(), name="task-lists"),
    path("<int:pk>", TaskDetailAPIView.as_view(), name="task-detail"),
    path("lists", TaskListListCreateAPIView.as_view(), name="tasklist-lists"),
    path("lists/<int:pk>", TaskListDetailAPIView.as_view(), name="tasklist-detail"),
]
