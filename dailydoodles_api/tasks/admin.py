from django.contrib import admin

from dailydoodles_api.tasks.models import Task, TaskList


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "due_date", "is_completed", "is_deleted")
    search_fields = ("title", "user")
    list_filter = ("is_completed", "is_deleted")
    exclude = ("deleted_date", "is_deleted")


@admin.register(TaskList)
class TaskListAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "is_deleted")
    search_fields = ("title", "user")
    list_filter = ("is_deleted",)
    exclude = ("deleted_date", "is_deleted")
