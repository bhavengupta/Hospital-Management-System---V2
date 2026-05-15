from celery import Celery, Task
from flask import Flask
from celery.schedules import crontab

celery = None

class FlaskTask(Task):
    def __call__(self, *args, **kwargs):
        from flask import current_app   
        with current_app.app_context():
            return self.run(*args, **kwargs)

class CeleryConfig():
    broker_url = "redis://localhost:6379/0"
    result_backend = "redis://localhost:6379/1"
    timezone = "Asia/Kolkata"

    beat_schedule = {
        "daily_reminder": {
            "task":"daily_reminder_task",
            "schedule": crontab(minute="*/1"),
        },
        "monthly_report": {
            "task":"monthly_report_task",
            "schedule": crontab(day_of_month = 1, hour = 9, minute = 0),
        },
    }
   
def celery_init_app(app: Flask) -> Celery:
    global celery
    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(CeleryConfig())
    celery_app.set_default()

    celery = celery_app
    app.extensions["celery"] = celery_app
    
    import backend.celery.tasks

    return celery_app