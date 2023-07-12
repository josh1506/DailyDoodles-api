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


class TaskTestCase(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(email="testuser@yahoo.com", password="testpass")
        self.task_list = TaskList.objects.create(title="Test List Title", user=self.user)
        self.task = Task.objects.create(
            title="Test Title",
            description="Test description",
            task_list=self.task_list,
            is_completed=False,
            user=self.user,
        )

    def test_created_model(self):
        self.assertEqual("Test Title", self.task.title)
        self.assertEqual("Test description", self.task.description)
        self.assertEqual(self.task_list, self.task.task_list)
        self.assertEqual(False, self.task.is_completed)
        self.assertEqual(self.user, self.task.user)

    def test_fetch_model(self):
        task = Task.objects.get(id=self.task.pk)
        self.assertEqual(self.task.title, task.title)
        self.assertEqual(self.task.description, task.description)
        self.assertEqual(self.task.task_list, task.task_list)
        self.assertEqual(self.task.is_completed, task.is_completed)
        self.assertEqual(self.task.user, task.user)

    def test_update_model(self):
        updated_title = "Updated Title"
        updated_description = "Updated description"
        updated_status = True
        Task.objects.filter(id=self.task.pk).update(
            title=updated_title, description=updated_description, is_completed=updated_status
        )
        task = Task.objects.get(id=self.task.pk)
        self.assertEqual(updated_title, task.title)
        self.assertEqual(updated_description, task.description)
        self.assertEqual(updated_status, task.is_completed)

    def test_delete_model(self):
        Task.objects.get(id=self.task.pk).delete()
        task = Task.objects.filter(id=self.task.pk)
        self.assertEqual(0, len(task))
