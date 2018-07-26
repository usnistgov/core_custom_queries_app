"""
Describe the admin forms used by custom_queries
"""

import re

from django import forms

from core_custom_queries_app.components.dyn_query import api as dyn_query_api
from core_main_app.components.template import api as template_api
from core_main_app.components.template_version_manager import api as template_version_manager_api


class QueryPieceForm(forms.Form):
    """
    Form to create or modify query steps
    """

    # Possible type of data
    typesData = (
        ('data', 'Data'),
        ('date', 'Date-Time')
    )

    # Possible type of target
    typesTarget = (
        ('attribute', 'Attribute'),
        ('name', 'Name'),
        ('value', 'Value')
    )

    # Step id - Hidden field
    step_id = forms.CharField(widget=forms.HiddenInput(),
                              label="Id",
                              required=False)

    # Step name - Text field
    name = forms.CharField(label="Name",
                           required=True,
                           widget=forms.TextInput(attrs={'class': 'full_item'})
                           )

    # Step xpath - Text field
    xpath = forms.CharField(label="XPath",
                            required=True,
                            widget=forms.TextInput(attrs={'class': 'full_item'})
                            )

    # Step output field, False if query able - Checkbox field
    output_field = forms.BooleanField(label="Output field only",
                                      required=False,
                                      widget=forms.CheckboxInput(attrs={'class': 'full_item'})
                                      )

    # Step target, represent the part of the node which will be query - Select field
    target = forms.ChoiceField(label="Target",
                               required=False,
                               choices=typesTarget,
                               initial='attribute',
                               widget=forms.Select(attrs={'class': 'full_item'})
                               )

    # Attribute name which will be query if target is "attribute" - Text field
    value = forms.CharField(label="Attribute name",
                            required=False,
                            widget=forms.TextInput(attrs={'class': 'full_item'})
                            )

    # Data type query, data or date - Select field
    data_type = forms.ChoiceField(label="Data type",
                                  required=False,
                                  choices=typesData,
                                  widget=forms.Select(attrs={'class': 'full_item'})
                                  )

    # Restriction, if there is applicable restriction to the query - Checkbox field
    restriction = forms.BooleanField(label="Restriction",
                                     required=False,
                                     initial=False,
                                     widget=forms.CheckboxInput(attrs={'class': 'full_item'})
                                     )

    # Minimum data range if applicable - Text field
    data_min_range = forms.IntegerField(label="Minimum range",
                                        required=False,
                                        widget=forms.TextInput(attrs={'class': 'full_item', 'disabled': 'disabled'})
                                        )

    # Maximum data range if applicable - Integer field
    data_max_range = forms.IntegerField(label="Maximum range",
                                        required=False,
                                        widget=forms.TextInput(attrs={'class': 'full_item', 'disabled': 'disabled'})
                                        )

    # Infinite data range if applicable - Checkbox field
    data_infinity = forms.BooleanField(label="Infinity",
                                       required=False,
                                       widget=forms.CheckboxInput(attrs={'class': 'full_item', 'disabled': 'disabled'})
                                       )

    # Date range if applicable - Integer field
    date_range = forms.IntegerField(label="Maximum day range",
                                    required=False,
                                    widget=forms.TextInput(attrs={'class': 'full_item', 'disabled': 'disabled'})
                                    )

    def __init__(self, *args, **kwargs):
        super(QueryPieceForm, self).__init__(*args, **kwargs)
        self.initial['data_type'] = 'data'
        self.empty_permitted = False

    def clean(self):
        # Define the cleaning rules for the step
        if 'name' not in self.cleaned_data or self.cleaned_data['name'] == "":
            if 'name' in self.errors:
                del self.errors['name']
            self.add_error('name', "You have to fill the name.")
        else:
            name = self.cleaned_data['name']
            if not (re.match('^[a-zA-Z0-9_]+$', name) is not None):
                self.add_error('name',
                               "A query name could only be composed by alphanumeric "
                               "characters.")

        if 'xpath' not in self.cleaned_data or self.cleaned_data['xpath'] == "":
            if 'xpath' in self.errors:
                del self.errors['xpath']
            self.add_error('xpath', "You have to fill the xpath.")
        else:
            xpath = self.cleaned_data["xpath"]
            if ".." in xpath:
                self.add_error('xpath', "The xpath can not contain \"..\".")

        if self.cleaned_data['target'] == 'attribute' \
                and self.cleaned_data['output_field'] is False:
            if 'value' not in self.cleaned_data or self.cleaned_data['value'] == '':
                self.add_error('value', "You have to fill the name of the attribute you want to "
                                        "query.")
        if self.cleaned_data['restriction'] is True \
                and self.cleaned_data['data_type'] == 'data' \
                and self.cleaned_data['output_field'] is False:
            if 'data_min_range' not in self.cleaned_data:
                if 'data_min_range' in self.errors:
                    del self.errors['data_min_range']
                self.add_error('data_min_range', "You have to fill the minimum range and has to be"
                                                 " an integer.")
            elif self.cleaned_data['data_min_range'] == '' or self.cleaned_data['data_min_range']\
                    is None:
                self.add_error('data_min_range', "You have to fill the minimum range.")
            elif self.cleaned_data['data_min_range'] < 0:
                self.add_error('data_min_range', "The minimum range has to be a positive integer.")

        if self.cleaned_data['data_infinity'] is False and self.cleaned_data['restriction'] is True \
                and self.cleaned_data['data_type'] == 'data' \
                and self.cleaned_data['output_field'] is False:
            if 'data_max_range' not in self.cleaned_data:
                if 'data_max_range' in self.errors:
                    del self.errors['data_max_range']
                self.add_error('data_max_range', "You have to fill the maximum range and has to be "
                                                 "an integer.")
            elif self.cleaned_data['data_max_range'] == '' or self.cleaned_data['data_max_range']\
                    is None:

                self.add_error('data_max_range', "You have to fill the maximum range.")
            elif self.cleaned_data['data_max_range'] < 0:
                self.add_error('data_max_range', "The maximum range has to be a positive integer.")

        if self.cleaned_data['data_type'] == 'data' \
                and self.cleaned_data['output_field'] is False:
            if self.cleaned_data['restriction'] is True:
                if self.cleaned_data['data_infinity'] is False:
                    if 'data_min_range' in self.cleaned_data and 'data_max_range' in self.cleaned_data:
                        if type(self.cleaned_data['data_max_range']) == int and \
                                        type(self.cleaned_data['data_min_range']) == int:
                            if self.cleaned_data['data_max_range'] < self.cleaned_data['data_min_range']:
                                self.add_error('data_max_range',
                                               "The maximum range has to superior to the minimum range.")

        if self.cleaned_data['restriction'] is True \
                and self.cleaned_data['data_type'] == 'date' \
                and self.cleaned_data['output_field'] is False:
            if 'date_range' not in self.cleaned_data:
                if 'date_range' in self.errors:
                    del self.errors['date_range']
                self.add_error('date_range', "You have to fill the date range and has to be an integer.")
            elif self.cleaned_data['date_range'] == '' or self.cleaned_data['date_range'] is None:
                self.add_error('date_range', "You have to fill the date range.")
            elif self.cleaned_data['date_range'] <= 0:
                self.add_error('date_range', "The date has to be a positive integer.")


class Query(forms.Form):
    """
        Form to create or modify query
    """

    # Possible group for the query
    groups = (
        ('admin', 'Admin-only'),
        ('user', 'User-allowed'),
    )

    # Query ID
    id = forms.CharField(
        widget=forms.HiddenInput(),
        label="Id",
        required=False
    )

    # Query name
    name = forms.CharField(label="Query name",
                           required=True)

    # Is query limited to number_records records
    is_limited = forms.BooleanField(label="Is the query limited",
                                    required=False,
                                    initial=False)

    # Number of records
    number_records = forms.IntegerField(
        label="Number of records to limit the query",
        required=False,
        min_value=1
    )

    # Schema ID associated to the query
    schema = forms.ChoiceField(label="Schema",
                               required=True)

    # Group associated to the query
    group = forms.ChoiceField(label="Group",
                              required=True,
                              choices=groups,
                              widget=forms.RadioSelect(),
                              initial='admin')

    # Delete field
    to_delete = forms.CharField(widget=forms.HiddenInput(attrs={'id': "to_delete"}),
                                initial=1234,
                                required=False)

    def _post_clean(self):
        """
        Cleaning method for POST call.
        """
        if 'schema' in self.errors:
            del self.errors['schema'][0]
            self.add_error('schema', 'The previously selected schema is not available anymore, '
                                     'please select an other.')

    def __init__(self, *args, **kwargs):
        """
        Init function for query.
        :param args: Used by the super class init.
        :param kwargs: Used by the super class init.
        """
        super(Query, self).__init__(*args, **kwargs)
        self.initial['group'] = 'admin'

        template_version_managers = template_version_manager_api.get_active_global_version_manager()

        list_templates = list()

        for template_version_manager in template_version_managers:
            for version_id in template_version_manager.versions:
                template = template_api.get(version_id)
                list_templates.append([version_id, template.display_name])

        self.fields['schema'].choices = list_templates

    def clean(self):
        """
        Clean function for the query
        :return:
        """
        if 'name' not in self.cleaned_data:
            if 'name' in self.errors:
                del self.errors['name']
            self.add_error('name', "The query name is required.")
        else:
            name = self.cleaned_data['name']
            if not (re.match('^[a-zA-Z0-9_]+$', name) is not None):
                self.add_error('name',
                               "A query name could only be composed by alphanumeric "
                               "characters.")

            cur_id = self.cleaned_data['id']
            if cur_id != '':
                names = dyn_query_api.get_all().filter(id__nin=[self.cleaned_data["id"]]).values_list('name')
            else:
                names = dyn_query_api.get_all().values_list('name')
            if name == "":
                self.add_error('name', "The name can not be empty.")
            elif name in names:
                self.add_error('name', "A query with this name has already been registered.")

        if 'is_limited' in self.cleaned_data:
            if self.cleaned_data['is_limited']:
                if 'number_records' in self.cleaned_data:
                    number_records = self.cleaned_data["number_records"]
                    if isinstance(number_records, int):
                        if number_records <= 0:
                            self.add_error('number_records', "The number of records has to be a positive integer ")
                    else:
                        self.add_error('number_records', "The number of records has to be a positive integer.")
                else:
                    self.add_error('number_records', "The number of records has to be filled")


class LogFilesFormPreview(forms.Form):
    """
    Form preview log files, give basic information
    """

    # Log file id - Hidden field
    id = forms.CharField(required=True,
                         widget=forms.widgets.HiddenInput())

    # Application link to the log file - Text field
    application = forms.CharField(label='Application',
                                  required=True,
                                  widget=forms.TextInput(attrs={'class': 'full_item', 'readonly': 'true'})
                                  )

    # Timestamp link to the log file - Text field
    timestamp = forms.DateTimeField(required=True,
                                    widget=forms.TextInput(attrs={'class': 'full_item', 'readonly': 'true'})
                                    )

    # Log file message - Text field
    message = forms.CharField(label='Error message',
                              required=True,
                              widget=forms.TextInput(attrs={'class': 'full_item', 'readonly': 'true'})
                              )


class LogFilesFormDetails(forms.Form):
    """
        Form detail log files, give full information
    """

    # Log file id - Hidden field
    id = forms.CharField(required=True,
                         widget=forms.widgets.HiddenInput())

    # Application link to the log file - Text field
    application = forms.CharField(label='Application',
                                  required=True,
                                  widget=forms.TextInput(attrs={'class': 'full_item', 'readonly': 'true'})
                                  )

    # Timestamp link to the log file - Text field
    timestamp = forms.DateTimeField(required=True,
                                    widget=forms.TextInput(attrs={'class': 'full_item', 'readonly': 'true'})
                                    )

    # Log file code - Text field
    code = forms.CharField(label='Error code',
                           required=False,
                           widget=forms.TextInput(attrs={'class': 'full_item', 'readonly': 'true'})
                           )

    # Log file message - Text field
    message = forms.CharField(label='Error message',
                              required=True,
                              widget=forms.TextInput(attrs={'class': 'full_item', 'readonly': 'true'})
                              )

    # Log file additional information, presented by a dictionary - Textarea field
    additional = forms.CharField(label='Additional information',
                                 required=False,
                                 widget=forms.Textarea(attrs={'class': 'additional_element', 'readonly': 'true'})
                                 )
