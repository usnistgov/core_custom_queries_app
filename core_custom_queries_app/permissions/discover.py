""" Initialize permissions for core custom queries app
"""
from __future__ import print_function
from django.contrib.auth.models import Group, Permission
import core_main_app.permissions.rights as main_rights
import core_custom_queries_app.permissions.rights as custom_queries_rights


def init_permissions():
    """ Initialization of groups and permissions.

    Returns:

    """
    try:
        # Get or Create the default group
        default_group, created = Group.objects.get_or_create(name=main_rights.default_group)

        # Get custom queries permissions
        custom_queries_access_perm = Permission.objects.get(codename=custom_queries_rights.custom_queries_access)

        # Add permissions to default group
        default_group.permissions.add(custom_queries_access_perm)

    except Exception as e:
        print('ERROR : Impossible to init the permissions : ' + e.message)
