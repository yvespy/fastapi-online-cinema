from celery import Celery

celery = Celery(
    "online_cinema",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["src.tasks.activation_tokens"]
)



celery.conf.beat_schedule = {
    "delete-expired-activation-tokens": {
        "task": "src.tasks.activation_tokens.delete_expired_tokens",
        "schedule": 9000.0,
    }
}
