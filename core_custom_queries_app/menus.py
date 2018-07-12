""" Add Custom Queries to main menu
"""
from django.core.urlresolvers import reverse
from menu import Menu, MenuItem


types_children = (
    MenuItem("Custom Queries List", reverse("admin:core_custom_queries_app_queries"), icon="list"),
)

Menu.add_item(
    "admin", MenuItem("CUSTOM QUERIES", None, children=types_children)
)
