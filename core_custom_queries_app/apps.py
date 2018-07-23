""" Apps file for setting core package when app is ready
"""
from django.apps import AppConfig


class CustomQueriesAppConfig(AppConfig):
    """ Core application settings.
    """
    name = 'core_custom_queries_app'

    def ready(self):
        """ Run when the app is ready.

        Returns:

        """
        import core_custom_queries_app.permissions.discover as discover
        discover.init_permissions()
