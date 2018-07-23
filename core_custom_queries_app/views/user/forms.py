""" Forms for Custom Queries user views
"""

from django import forms


class FormChooseQuery(forms.Form):
    """
    Form to choose a query with radio selection.
    """

    # Query field - Radio field
    query = forms.ChoiceField(widget=forms.widgets.RadioSelect(), required=True)

    def __init__(self, *args, **kwargs):
        _query = kwargs.pop('query', None)
        super(FormChooseQuery, self).__init__(*args, **kwargs)
        self.fields['query'].choices = _query


class FormBase(forms.Form):
    """
    Base information for steps
    """

    # Query name - Hidden field.
    queryName = forms.CharField(label='Query Name', required=True, widget=forms.widgets.HiddenInput())
    # Query position - Hidden field.
    position = forms.IntegerField(label='Position in query', required=True, widget=forms.widgets.HiddenInput())
    # Query id - Hidden field.
    user_query = forms.CharField(label='User query', required=True, widget=forms.widgets.HiddenInput())
    # Form type - Hidden field.
    data_type = forms.CharField(label='Query step type', required=True, widget=forms.widgets.HiddenInput())
    # Hidden input if the user want to go back.
    step_back = forms.BooleanField(required=False, widget=forms.widgets.HiddenInput())
    # History id linked to the step - Hidden field.
    history_id = forms.CharField(required=True, widget=forms.widgets.HiddenInput())

    def __init__(self, *args, **kwargs):
        _queryName = kwargs.pop('queryName', None)
        _position = kwargs.pop('position', None)
        _user_query = kwargs.pop('user_query', None)
        _data_type = kwargs.pop('data_type', None)
        _step_back = kwargs.pop('step_back', None)
        _history_id = kwargs.pop('history_id', None)
        super(FormBase, self).__init__(*args, **kwargs)
        self.fields['queryName'].initial = _queryName
        self.fields['position'].initial = _position
        self.fields['user_query'].initial = _user_query
        self.fields['data_type'].initial = _data_type
        self.fields['step_back'].initial = _step_back
        self.fields['history_id'].initial = _history_id


class FormRadio(FormBase):
    """
    Radio form for a query step.
    """

    # Choices for the current step - Radio field
    choices = forms.ChoiceField(widget=forms.widgets.RadioSelect(), required=True)

    def __init__(self, *args, **kwargs):
        # Init radio form
        _choices = kwargs.pop('choices', None)
        _stepName = kwargs.pop('stepName', None)
        super(FormRadio, self).__init__(*args, **kwargs)
        self.fields['choices'].choices = _choices
        self.fields['choices'].label = _stepName
        self.fields['data_type'].data = 'radio'


class FormCheck(FormBase):
    """
    Check form for the query step
    """

    # Choices for the current step - Check field
    choices = forms.MultipleChoiceField(widget=forms.widgets.CheckboxSelectMultiple(), required=True)
    # Minimum range for the current step - Hidden field
    data_min_range = forms.IntegerField(widget=forms.widgets.HiddenInput())
    # Maximum range for the current step - Hidden field
    data_max_range = forms.IntegerField(widget=forms.widgets.HiddenInput())
    # Infinity for the current step - Hidden field
    data_infinity = forms.BooleanField(widget=forms.widgets.HiddenInput())

    def __init__(self, *args, **kwargs):
        # Init check forms
        _choices = kwargs.pop('choices', None)
        _dataMinRange = kwargs.pop('data_min_range', None)
        _dataMaxRange = kwargs.pop('data_max_range', None)
        _dataInfinity = kwargs.pop('data_infinity', None)
        _stepName = kwargs.pop('stepName', None)
        super(FormCheck, self).__init__(*args, **kwargs)
        self.fields['choices'].choices = _choices
        self.fields['choices'].label = _stepName
        self.fields['data_min_range'].initial = _dataMinRange
        self.fields['data_max_range'].initial = _dataMaxRange
        self.fields['data_infinity'].initial = _dataInfinity


class FormDateTime(FormBase):
    """
    Date time form
    """

    # First threshold, "From" date
    timeFrom = forms.DateTimeField(label='From',
                                   required=True,
                                   widget=forms.TextInput(
                                       attrs={'readonly': 'True', 'class': 'form-control'}
                                   ))

    # Second threshold, "To" date
    timeTo = forms.DateTimeField(label='To',
                                 required=True,
                                 widget=forms.TextInput(
                                     attrs={'readonly': 'True', 'class': 'form-control'}
                                 ))

    # Number of days query able, maximum difference between "to" and "from"
    date_range = forms.CharField(widget=forms.widgets.HiddenInput())

    def __init__(self, *args, **kwargs):
        _dateRange = kwargs.pop('date_range', None)
        super(FormDateTime, self).__init__(*args, **kwargs)
        self.fields['date_range'].initial = _dateRange
        self.fields['data_type'].initial = 'date'


class FormResult(forms.Form):
    """
    Result form, with file preview and file download.
    """

    # Different format files
    choices = (
        ('csv', 'ASCII CSV'),
        ('json', 'JSON'),
        ('xml', 'XML')
    )

    # CSV file id - Hidden field
    hidden_id_file_csv = forms.CharField(required=False, widget=forms.widgets.HiddenInput())
    # JSON file id - Hidden field
    hidden_id_file_json = forms.CharField(required=False, widget=forms.widgets.HiddenInput())
    # XML file id - Hidden field
    hidden_id_file_xml = forms.CharField(required=False, widget=forms.widgets.HiddenInput())
    # CSV file preview - Hidden field
    preview_file_csv = forms.CharField(required=False, widget=forms.widgets.HiddenInput())
    # JSON file preview - Hidden field
    preview_file_json = forms.CharField(required=False, widget=forms.widgets.HiddenInput())
    # XML file preview - Hidden field
    preview_file_xml = forms.CharField(required=False, widget=forms.widgets.HiddenInput())
    # Query name - Hidden field
    hidden_query_name = forms.CharField(required=True, widget=forms.widgets.HiddenInput())
    # Format file selected - Radio field
    formats = forms.ChoiceField(required=False,
                                choices=choices,
                                widget=forms.widgets.RadioSelect(),
                                initial='csv')

    def __init__(self, *args, **kwargs):
        # Init result forms
        hidden_id_file_csv = kwargs.pop('hidden_id_file_csv', None)
        hidden_id_file_json = kwargs.pop('hidden_id_file_json', None)
        hidden_id_file_xml = kwargs.pop('hidden_id_file_xml', None)
        preview_file_csv = kwargs.pop('preview_file_csv', None)
        preview_file_json = kwargs.pop('preview_file_json', None)
        preview_file_xml = kwargs.pop('preview_file_xml', None)
        hidden_query_name = kwargs.pop('queryName', None)
        super(FormResult, self).__init__(args, kwargs)
        self.data['hidden_id_file_csv'] = hidden_id_file_csv
        self.data['hidden_id_file_json'] = hidden_id_file_json
        self.data['hidden_id_file_xml'] = hidden_id_file_xml
        self.data['preview_file_csv'] = preview_file_csv
        self.data['preview_file_json'] = preview_file_json
        self.data['preview_file_xml'] = preview_file_xml
        self.data['hidden_query_name'] = hidden_query_name
        self.fields['formats'].initial = 'csv'


class FormHistory(forms.Form):
    """
    Form to select / delete history query
    """

    # Query ID - Hidden field
    id_history = forms.CharField(widget=forms.widgets.HiddenInput())
    # Query name - Text field
    query_name = forms.CharField(
        label='Query name',
        required=False,
        widget=forms.TextInput(attrs={'class': 'full_item'})
    )
    # Last modified timestamp - Text field
    query_last_modified = forms.DateTimeField(
        label='Last modified',
        required=False,
        widget=forms.TextInput(attrs={'class': 'full_item'})
    )
    # Query message - Text field
    query_message = forms.CharField(
        label='Status',
        required=False,
        widget=forms.TextInput(attrs={'class': 'full_item'})
    )
    # Query status - Hidden fields
    status = forms.IntegerField(widget=forms.widgets.HiddenInput())
