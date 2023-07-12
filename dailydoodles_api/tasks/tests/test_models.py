from django.contrib.auth import get_user_model
from django.test import TestCase

from dailydoodles_api.tasks.models import Task, TaskList

User = get_user_model()


class TaskListTestCase(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(email="testuser@yahoo.com", password="testpass")
        self.task_list = TaskList.objects.create(title="Test List Title", user=self.user)

    def test_created_model(self):
        self.assertEqual("Test List Title", self.task_list.title)
        self.assertEqual(self.user, self.task_list.user)

    def test_fetch_model(self):
        task_list = TaskList.objects.get(id=self.task_list.pk)
        self.assertEqual(self.task_list.title, task_list.title)
        self.assertEqual(self.task_list.user, task_list.user)

    def test_update_model(self):
        updated_title = "Updated List Title"
        TaskList.objects.filter(id=self.task_list.pk).update(title=updated_title)
        task_list = TaskList.objects.get(id=self.task_list.pk)
        self.assertEqual(updated_title, task_list.title)

    def test_delete_model(self):
        TaskList.objects.get(id=self.task_list.pk).delete()
        task_list = TaskList.objects.filter(id=self.task_list.pk)
        self.assertEqual(0, len(task_list))
