# DailyDoodles

DailyDoodles is a productive application created using React.js, Vite, and Django. It provides various features such as
a to-do app, sticky notes, and more, enabling users to stay organized and boost productivity.

## Features

- **To-Do App**: Easily manage your tasks, create to-do lists, and keep track of your progress.
- **Sticky Notes**: Capture quick notes, reminders, and important information on virtual sticky notes.
- **Customization**: Personalize the app by choosing different themes, colors, and styles to suit your preferences.
- **Collaboration**: Collaborate with others by sharing to-do lists and sticky notes, making teamwork more efficient.
- **Reminders and Notifications**: Set reminders and receive notifications to stay on top of your tasks and deadlines.
- **Cross-Platform**: Access DailyDoodles on various devices, including desktops, tablets, and mobile phones, for
  seamless productivity.

## Technologies Used

- **React.js**: A JavaScript library for building user interfaces, providing a fast and interactive app experience.
- **Vite**: A build tool that offers lightning-fast development and production builds for React.js applications.
- **Django**: A high-level Python web framework that provides the backend infrastructure for the application.
- **Other Libraries**: DailyDoodles also utilizes additional libraries and tools for enhanced functionality and
  efficient development.

## License

This project is licensed under the [MIT License](./LICENSE). Feel free to modify and use the code according to your needs.

## Settings

Moved to [settings](./config/settings).

## Basic Commands

### Setting Up Your Users

- To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

- To create a **superuser account**, use this command:

      $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

### Type checks

Running type checks with mypy:

    $ mypy dailydoodles_api

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

#### Running tests with pytest

    $ pytest

### Celery

This app comes with Celery.

To run a celery worker:

```bash
cd dailydoodles_api
celery -A config.celery_app worker -l info
```

Please note: For Celery's import magic to work, it is important _where_ the celery commands are run. If you are in the same folder with _manage.py_, you should be right.

To run [periodic tasks](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html), you'll need to start the celery beat scheduler service. You can start it as a standalone process:

```bash
cd dailydoodles_api
celery -A config.celery_app beat
```

or you can embed the beat service inside a worker with the `-B` option (not recommended for production use):

```bash
cd dailydoodles_api
celery -A config.celery_app worker -B -l info
```

## Deployment

The following details how to deploy this application.
