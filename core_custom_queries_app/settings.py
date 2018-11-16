from django.conf import settings

if not settings.configured:
    settings.configure()

REDIS_URL = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
