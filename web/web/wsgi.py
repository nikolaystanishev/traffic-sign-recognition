"""
WSGI config for web project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

sys.path.append('/opt/bitnami/apps/django/django_projects/remove_4ovek/web')
os.environ.setdefault("PYTHON_EGG_CACHE", "/opt/bitnami/apps/django/django_projects/remove_4ovek/web/egg_cache")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web.settings")

application = get_wsgi_application()
