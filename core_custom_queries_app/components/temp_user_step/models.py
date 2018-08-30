""" TempUserStep model
"""
from collections import defaultdict

from bson import ObjectId
from django_mongoengine import Document, fields

from core_custom_queries_app.components.dyn_query_step.models import DynQueryStep
from core_custom_queries_app.components.temp_bucket_id_files.models import TempBucketIdFiles
from core_custom_queries_app.components.temp_choice_list_file.models import TempChoiceListFile
from core_custom_queries_app.exceptions import EmptyChoicesFromQuery
from core_custom_queries_app.utils import flat_list, explore_star, is_datetime_inf_or_equal


class TempUserStep(Document):
    """
    Model which define the step associated to a user choice
    """
    step = fields.ReferenceField(DynQueryStep, blank=True)  # Base step

    # Attribute for query_management
    query_able = fields.BooleanField()  # True if the query is query able, false else
    # List of choices and files
    list_choices_id_file = fields.ListField(fields.ReferenceField(TempChoiceListFile, blank=True), blank=True)
    dict_choices_id_file = dict()  # Dict of choices and files id
    files = fields.ListField(blank=True)  # List of file for date step
    choices = fields.ListField(blank=True)  # User choices for the step
    form_type = fields.StringField()  # Form step type (radio, check, date)
    absolute_position = fields.IntField()  # Position in the list of steps for the query
    viewable_position = fields.IntField()  # Position in the list of query able steps for the query
    full_xpath = fields.StringField()  # Full path to the query

    @staticmethod
    def get_all():
        """Return all TempUserStep.

        Returns:

        """
        return TempUserStep.objects().all()

    def delete_database(self):
        """
        Delete function

        Delete each choices and the associated files.
        """

        for choices_id_file in self.list_choices_id_file:
            try:
                choices_id_file_obj = TempChoiceListFile.objects.get(id=choices_id_file.id)
                choices_id_file_obj.delete_database()
            except:
                pass

        self.delete()

    def initialize_step(self, step=None):
        """
            Initialise the query step.

            It initialize a step. If the step name is given, the information are loaded from the
            step define by the admin into step.

            :param step: The step to load.
            :return: The object initialized.
        """

        # Attribute for query_management
        self.list_choices_id_file = list()
        self.dict_choices_id_file = dict()
        self.files = list()  # List of file for date step
        self.choices = list()  # User choice for the step
        self.form_type = ''
        self.absolute_position = None
        self.viewable_position = None
        self.full_xpath = None
        self.query_able = False

        if step is not None:
            self.load_from_step_admin(step=step)

    def load_from_step_admin(self, step):
        """
            Load the step from the admin defined step.

            The information are loaded from the step define by the admin into the user's step.
            It is mainly used by the __init__.

            :param step: The step to load.
        """
        self.step = step

        self.query_able = not step.output_field

        if self.step.data_type == 'data':
            if self.step.data_min_range == 1 and self.step.data_max_range == 1:
                self.form_type = 'radio'
            else:
                self.form_type = 'check'
        else:
            self.form_type = 'date'

    def load_choices_and_xml_data(self, cursor_xml_data):
        """
            Load the dictionary of choices and files from the list of input files

            :param cursor_xml_data: List of input files
        """
        dict_choices_file = defaultdict(set)
        for file_xml_data in cursor_xml_data:
            data_dict = file_xml_data.to_mongo()
            self.get_choices(
                [data_dict['dict_content']],
                [x for x in self.full_xpath.split(".") if x],
                dict_choices_file,
                data_dict['_id']
            )
        for choices, set_files in dict_choices_file.iteritems():
            self.dict_choices_id_file[choices] = list(set_files)

        if len(self.dict_choices_id_file) == 0:
            raise EmptyChoicesFromQuery(x_path=self.full_xpath)

    def get_id_files_from_user_choices(self):
        """
        Get the list of unique files from the user choices and the list of choices and files.
        :return: List of unique files
        """
        unique_id_files = set()
        for temp_choice_list_file in self.list_choices_id_file:
            if temp_choice_list_file.choice in self.choices:
                for bucket in temp_choice_list_file.list_buckets:
                    for id_file in bucket.list_files:
                        unique_id_files.add(ObjectId(id_file))
        return list(unique_id_files)

    def get_choices_as_tuple(self):
        """
            Get list of choices.

            Get a list of possible choices for the user as tuple as
            [(choice1, choice1), (choice2, choice2), ...].

            :return: List of possible choices for the user as tuple or None if there is no choices.
        """
        if len(self.dict_choices_id_file) == 0:
            return None
        else:
            choices = set()
            for keys in self.dict_choices_id_file:
                choices.add((keys, keys))
            return sorted(tuple(choices))

    def update_choices_to_db(self):
        """
            Update the user choices for the step.
        """
        self.update(choices=self.choices)

    def update_choices_id_files_to_db(self):
        """
            Update the choices and the corresponding files to the db.

            Update the choices and the corresponding files to the db. Change also the way of data
             structure, from a dictionary based structure to a list based structure more suitable
             for database restriction.
        """
        choices_id_files_to_save = self.dict_choices_id_file

        # Delete old data in the DB
        for choice in self.list_choices_id_file:
            for bucket in choice.list_buckets:
                for files in bucket.list_files:
                    files.delete()
                bucket.delete()
            choice.delete()

        # Transform and update the data
        new_list_choices_list_files = list()
        for choice, list_value in choices_id_files_to_save.items():
            new_temp_choice_list_file = TempChoiceListFile()
            new_temp_choice_list_file.choice = choice
            list_bucket_temp = list()
            chunks = [list_value[x:x + 300] for x in xrange(0, len(list_value), 300)]
            for chunk in chunks:
                new_bucket = TempBucketIdFiles()
                new_bucket.list_files = chunk
                new_bucket.save()
                list_bucket_temp.append(new_bucket)

            new_temp_choice_list_file.list_buckets = list_bucket_temp
            new_temp_choice_list_file.save()
            new_list_choices_list_files.append(new_temp_choice_list_file)

        self.update(list_choices_id_file=new_list_choices_list_files)

    def transform_choices_files_list_to_dict(self):
        """
            Transform and return the possible choices-lists from db-list to use-dict

            Transform the choices-files list structure into a DB to a usable choices-files dict
            structure. It also delete old trace of existing choices-files dict structure.
        """
        self.dict_choices_id_file = dict()
        for list_choices_id_file in self.list_choices_id_file:
            self.dict_choices_id_file[list_choices_id_file.choice] = list()
            for buckets in list_choices_id_file.list_buckets:
                self.dict_choices_id_file[list_choices_id_file.choice].extend(buckets.list_files)

    def update_files_in_db(self):
        """
            Update the list  of files into the db
        """
        self.update(files=self.files)

    def clean_step(self):
        """
            Clean a specific step into the database.
        """
        self.update(choices=list())
        self.update(files=list())

        for list_choices_id_file in self.list_choices_id_file:
            for bucket in list_choices_id_file.list_buckets:
                bucket.delete()
            list_choices_id_file.delete()
        self.update(list_choices_id_file=list())

    def filter_user_choice_date(self, element, time_from, time_to, translate_dt):
        """
        Filter a specif element against it date value
        :param element: element too filter
        :param time_from: First threshold to filter
        :param time_to: Second threshold to filter
        :param translate_dt: Python translate for the element value
        :return: Return true is the element date is after the time_from and before the time_to
        """
        timestamp = str(element["@" + self.step.value])
        if timestamp[-1] == 'Z':
            timestamp = timestamp[:-1]
        timestamp = map(int, timestamp.translate(translate_dt).split())
        if (is_datetime_inf_or_equal(time_from, timestamp) and
                is_datetime_inf_or_equal(timestamp, time_to)) is False:
            return False
        else:
            return True

    def choose_filter_choice(self, list_elements, element_title, translate_dt, translate_bounds):
        """
        Choose a specific filter and apply it to a list of elements.
        :param list_elements: List of elements to filter
        :param element_title: Title of the elements
        :param translate_dt: Translate object for date comparison
        :param translate_bounds: Translate object for date comparison
        :return: Filtered list of elements
        """
        if self.query_able:
            if self.step.data_type == 'data':
                target = self.step.target
                choices = self.choices
                if target == 'attribute':
                    value = "@" + self.step.value
                    list_elements_cleaned = [x for x in list_elements if x[value] in choices]
                    return list_elements_cleaned
                elif target == 'name':
                    if element_title not in choices:
                        list_elements_cleaned = []
                    else:
                        list_elements_cleaned = list_elements
                    return list_elements_cleaned
                else:
                    # FIXME: #text was hardcoded, but elements don't have #text if the xml tag does not have any
                    # FIXME: attributes
                    list_elements_cleaned = [x for x in list_elements if isinstance(x, dict) and x['#text'] in choices
                                             or x in choices]
                    return list_elements_cleaned
            else:
                time_from = map(int, str(self.choices[0]).
                                translate(translate_bounds).split())
                time_to = map(int, str(self.choices[1]).
                              translate(translate_bounds).split())
                my_filter_date = self.filter_user_choice_date
                list_elements_cleaned = [
                    x
                    for x in list_elements
                    if my_filter_date(element=x, time_from=time_from, time_to=time_to,
                                      translate_dt=translate_dt)
                    ]
                return list_elements_cleaned
        else:
            return list_elements

    def get_choices(self, list_elements, list_keys_xpath, dict_choices_file, id_file):
        """
        Get possibles choices from a list of elements to explore.
        :param list_elements: List of elements to explore
        :param list_keys_xpath: List of elements from the xpath spliced
        :param dict_choices_file: Dictionary of choices, linked to a list of files
        :param id_file:Current if file
        :return:
        """
        element_title = list_keys_xpath[-1]

        while list_keys_xpath:
            key_xpath = list_keys_xpath.pop(0)
            if list_elements:
                if isinstance(list_elements[0], list):
                    list_elements = flat_list(list_elements)
            if key_xpath == "*":
                set_possibilities = explore_star(list_elements)
                for key_possible in set_possibilities:
                    list_key_param_star = [key_possible]
                    if len(list_keys_xpath) != 0:
                        list_key_param_star.extend(list_keys_xpath)
                    self.get_choices(
                        list_elements=list_elements,
                        list_keys_xpath=list_key_param_star,
                        dict_choices_file=dict_choices_file,
                        id_file=id_file
                    )
                return
            else:
                list_elements = [x.get(key_xpath) for x in list_elements if x.get(key_xpath)]

        target = self.step.target
        if target == 'name':
            dict_choices_file[element_title].add(id_file)
        else:
            if list_elements:
                if isinstance(list_elements[0], list):
                    list_elements = flat_list(list_elements)
            if target == 'attribute':
                value = "@" + self.step.value
                set_elements = (str(x.get(value)) for x in list_elements)
                for element in set_elements:
                    dict_choices_file[element].add(id_file)
            else:
                # FIXME: #text was hardcoded, but elements don't have #text if the xml tag does not have any attributes
                # set_elements = (x.get("#text") for x in list_elements)
                set_elements = (x.get("#text") if isinstance(x, dict) else str(x) for x in list_elements)
                for element in set_elements:
                    dict_choices_file[element].add(id_file)
        return

