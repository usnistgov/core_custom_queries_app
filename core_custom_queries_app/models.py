""" Custom Queries models
"""
# FIXME: these models cannot be split into components for now because of circular dependencies
from datetime import datetime
from string import maketrans

from bson import ObjectId
from django.contrib.auth.models import User
from django.db import models
from django_mongoengine import fields, Document
from mongoengine import errors as mongoengine_errors
from redis import Redis, ConnectionError

from core_custom_queries_app.components.dyn_query.models import DynQuery
from core_custom_queries_app.components.log_file import api as log_file_api
from core_custom_queries_app.components.log_file.models import LogFile
from core_custom_queries_app.components.temp_bucket_id_files.models import TempBucketIdFiles
from core_custom_queries_app.components.temp_choice_list_file.models import TempChoiceListFile
from core_custom_queries_app.components.temp_output_file.models import TempOutputFile
from core_custom_queries_app.components.temp_user_step.models import TempUserStep
from core_custom_queries_app.exceptions import EmptyChoicesFromQuery
from core_custom_queries_app.permissions import rights
from core_custom_queries_app.utils import possible_projection, get_common_key_and_specific_header, get_title_data_leaf, \
    print_bloc, get_header_parents, get_general_key_output_dictionary, flat_list, send_mail_query_end, explore_star
from core_main_app.commons import exceptions
from core_main_app.commons.exceptions import DoesNotExist, ModelError
from core_main_app.components.template.models import Template
from core_main_app.permissions.utils import get_formatted_name
from core_main_app.system import api as system_api
from qdr.settings import REDIS_URL


class CustomQueries(models.Model):
    class Meta:
        verbose_name = 'core_custom_queries_app'
        default_permissions = ()
        permissions = (
            (rights.custom_queries_access, get_formatted_name(rights.custom_queries_access)),
        )


class HistoryQuery(Document):
    """ History object to retrieve a query to a specific step
    """
    user_id = fields.IntField()  # User link to the history
    query_id = fields.StringField()  # Query link to the history
    message = fields.StringField()  # History message
    status = fields.IntField()  # History status (0: Query step, 1: Waiting for treatment, 2: Output files created)

    @staticmethod
    def get_by_id(history_query_id):
        """ Return a HistoryQuery given its id.

        Args:
            history_query_id:

        Returns:

        """
        try:
            return HistoryQuery.objects.get(pk=str(history_query_id))
        except mongoengine_errors.DoesNotExist as e:
            raise exceptions.DoesNotExist(e.message)
        except Exception as ex:
            raise exceptions.ModelError(ex.message)

    @staticmethod
    def get_all():
        """ Return a list of all HistoryQuery.

        Returns:

        """
        return HistoryQuery.objects().all()

    @staticmethod
    def get_all_by_user_id(user_id):
        """ Return a list of HistoryQuery given their user_id.

        Args:
            user_id:

        Returns:

        """
        return HistoryQuery.objects.filter(user_id=str(user_id))

    def delete_database(self, from_query_admin=False):
        """ Delete function.

        If the deletion come from the admin panel, Delete all the user query linked to this history.

        Args:
            from_query_admin: Variable to avoid circle deletion.
        """
        if not from_query_admin:
            temp_user_queries = TempUserQuery.objects.filter(id=self.query_id)
            for temp_user_query in temp_user_queries:
                temp_user_query.delete_database(from_history=True)
        self.delete()


class TempUserQuery(Document):
    """ Model which define the query associated to a user choice
    """
    query = fields.ReferenceField(DynQuery, blank=True)

    current_position = fields.IntField()  # Current position in the query
    number_of_step = fields.IntField()  # Number of steps
    number_of_query_able_step = fields.IntField()  # Number of query able steps
    # List of steps associated to the query
    list_steps = fields.ListField(fields.ReferenceField(TempUserStep, blank=True), blank=True)
    str_id_file_json = fields.StringField()  # Output JSON file id when it has been created
    str_id_file_xml = fields.StringField()  # Output XML file id when it has been created
    str_id_file_csv = fields.StringField()  # Output CSV file id when it has been created
    last_modified = fields.DateTimeField()  # Last modified timestamp
    history = fields.ReferenceField(HistoryQuery, blank=True)  # History ID linked to the query

    @staticmethod
    def get_by_id(temp_user_query_id):
        """Return a TempUserQuery given its id.

        Args:
            temp_user_query_id:

        Returns:

        """
        try:
            return TempUserQuery.objects.get(pk=str(temp_user_query_id))
        except mongoengine_errors.DoesNotExist as e:
            raise exceptions.DoesNotExist(e.message)
        except Exception as ex:
            raise exceptions.ModelError(ex.message)

    @staticmethod
    def get_by_history_id(history_id):
        """Return a TempUserQuery given its history id.

        Args:
            history_id:

        Returns:

        """
        try:
            return TempUserQuery.objects.get(history=str(history_id))
        except mongoengine_errors.DoesNotExist as e:
            raise exceptions.DoesNotExist(e.message)
        except Exception as ex:
            raise exceptions.ModelError(ex.message)

    @staticmethod
    def get_all():
        """Return all TempUserQuery.

        Returns:

        """
        return TempUserQuery.objects().all()

    def delete_database(self, from_history=False):
        """ Delete function

        Delete each steps of the user query and each part of it.

        Args:
            from_history: If deletion coming from the history, variable to avoid circle deletion.
        """
        for step in self.list_steps:
            try:
                obj_step = TempUserStep.objects.get(id=step.id)
                obj_step.delete_database()
            except:
                pass

        # Delete if to treat
        queries = QueryToTreat.objects.filter(query=self)
        for query in queries:
            query.delete_database()

        # Delete History
        if not from_history:
            history_queries = HistoryQuery.objects.filter(query_id=str(self.id))
            for history_query in history_queries:
                history_query.delete_database(from_query_admin=True)

        # Delete output files
        if self.str_id_file_json != "":
            try:
                temp_file = TempOutputFile.objects.get(id=self.str_id_file_json)
                temp_file.delete_database()
            except DoesNotExist:
                pass
        if self.str_id_file_xml != "":
            try:
                temp_file = TempOutputFile.objects.get(id=self.str_id_file_xml)
                temp_file.delete_database()
            except DoesNotExist:
                pass
        if self.str_id_file_csv != "":
            try:
                temp_file = TempOutputFile.objects.get(id=self.str_id_file_csv)
                temp_file.delete_database()
            except DoesNotExist:
                pass

        # DeleteInfoRedis
        try:
            redis_server = Redis.from_url(REDIS_URL)
            if redis_server.exists("list_ids"):
                try:
                    redis_server.lrem("list_ids", str(self.id), 0)
                except AttributeError:
                    pass
        except ConnectionError:
            pass

        self.delete()

    def initialize_query(self, query_id=None):
        """ Initialise the query used step after step.

        It initialize a query used step after step. If the query name is given, the information
         are loaded from the query define by the admin into the query and his own steps.

        Args:
            query_id: The query name to load.

        Returns:
            The object initialized.
        """
        self.current_position = 0
        self.number_of_step = 0
        self.number_of_query_able_step = 0
        self.list_steps = list()
        self.last_modified = datetime.now()
        self.str_id_file_json = ""
        self.str_id_file_xml = ""
        self.str_id_file_csv = ""

        if query_id is not None:
            self.load_from_query_name_admin(query_id)

    def load_from_query_name_admin(self, query_id):
        """ Load the query from the admin query.

        The information are loaded from the query define by the admin into the query and his
         own steps. It is mainly used by the initialize_query method.


        Args:
            query_id: The query name to load.
        """
        query = DynQuery.objects.get(pk=query_id)
        self.query = query
        self.number_of_step = len(query.steps)

        position = 1
        position_to_show = 1
        full_x_path = ''
        for step in query.steps:
            # Create a new step
            new_step = TempUserStep()
            new_step.initialize_step(step=step)

            # Set the full XPath
            if new_step.step.xpath != ".":
                full_x_path += new_step.step.xpath
            new_step.full_xpath = full_x_path

            # Set and update the positions
            new_step.absolute_position = position
            if new_step.query_able:
                new_step.viewable_position = position_to_show
                position_to_show += 1
                self.number_of_query_able_step += 1
            else:
                new_step.viewable_position = 0

            position += 1

            self.list_steps.append(new_step)

    def save_whole_query(self):
        """ Save the whole query.

        Save the whole query:
        _save the general information,
        _save each steps,
        _save the choices-id_files.
        """

        for step in self.list_steps:
            for choice, list_files in step.dict_choices_id_file.iteritems():
                new_temp_choice_list_file = TempChoiceListFile()

                chunks = [list_files[x:x + 300] for x in xrange(0, len(list_files), 300)]
                list_bucket_temp = list()
                for chunk in chunks:
                    new_bucket = TempBucketIdFiles()
                    new_bucket.list_files = chunk
                    new_bucket.save()
                    list_bucket_temp.append(new_bucket)

                new_temp_choice_list_file.choice = choice
                new_temp_choice_list_file.list_buckets = list_bucket_temp
                new_temp_choice_list_file.save()

                step.list_choices_id_file.append(new_temp_choice_list_file)
            step.save()
        self.save()

    def update_current_position_into_the_db(self):
        """ Update the current position to the object in database.
        """
        self.update(current_position=self.current_position)

    def get_and_load_choices_first_step(self):
        """ Load the first query able step and return it.

        Returns:
             The first query able step
        """
        first_step = self.get_first_query_able_step()

        if first_step is None:
            return None
        else:
            full_projection = "dict_content." + first_step.full_xpath
            if first_step.step.target == 'attribute':
                full_projection += ".@" + first_step.step.value
            elif first_step.step.target == 'name':
                full_projection += ".@title"
            # FIXME: #text was hardcoded, but elements don't have #text if the xml tag does not have any attributes
            # else:
            #     full_projection += ".#text"
            full_projection = possible_projection(full_projection)
            dict_query = {'template': ObjectId(self.query.schema)}

            cursor_xml_data = system_api.execute_query_with_projection(dict_query, full_projection)

            if cursor_xml_data.count() == 0:
                schema_name = Template.objects.get(pk=self.query.schema).display_name
                raise EmptyChoicesFromQuery(schema=schema_name)

            elif first_step.step.data_type == "data":
                first_step.load_choices_and_xml_data(cursor_xml_data=cursor_xml_data)
            else:
                for file_xml_data in cursor_xml_data:
                    first_step.files.append(str(file_xml_data.id))

            return first_step

    def get_and_load_choices_next_step(self):
        """ Get and load the next query able step.

        Returns:
             the next query able step
        """
        current_step = self.get_current_step()
        next_step = self.get_next_query_able_step()
        if next_step is None:
            return None
        if current_step.step.data_type == 'data':
            unique_ids = current_step.get_id_files_from_user_choices()
        else:
            unique_ids = [ObjectId(x) for x in list(set(current_step.files))]

        if next_step.step.data_type == 'data':
            full_projection = 'dict_content.' + next_step.full_xpath
            if next_step.step.target == 'attribute':
                full_projection += ".@" + next_step.step.value
            elif next_step.step.target == 'name':
                full_projection += ".@title"
            # TODO: remove #text hardcoded
            # else:
            #     full_projection += ".#text"
            full_projection = possible_projection(full_projection)
            dict_query = {
                "template": ObjectId(self.query.schema),
                "_id": {"$in": unique_ids}
            }

            cursor_xml_data = system_api.execute_query_with_projection(dict_query, full_projection)

            if cursor_xml_data.count() == 0:
                schema_name = Template.objects.get(id=self.query.schema).display_name
                raise EmptyChoicesFromQuery(schema=schema_name)

            next_step.dict_choices_id_file = dict()
            next_step.load_choices_and_xml_data(cursor_xml_data=cursor_xml_data)
            next_step.update_choices_id_files_to_db()
        else:
            next_step.files = unique_ids
            next_step.update_files_in_db()

        return next_step

    def get_current_step(self):
        """ Return the step corresponding to the current position.

        Returns:
             Current step.
        """
        return self.list_steps[self.current_position]

    def get_first_query_able_step(self):
        """ Return the first query able step. If there is no query able step, it returns None.

        Returns:
            Return None if there is no query able step, or the first query able step.
        """
        self.current_position = 0
        if self.is_query_able(0):
            return self.list_steps[0]
        return self.get_next_query_able_step()

    def get_last_query_able_step(self):
        """ Return the last query able step. If there is no query able step, it returns None.

        Returns:
             Return None if there is no query able step, or the last query able step.
        """
        for step in reversed(self.list_steps):
            if step.query_able is True:
                return step
        return None

    def get_next_query_able_step(self):
        """ Return the next query able step. If there is no query able step, it returns None.

        Returns:
             Return None if there is no next query able step, or the next query able step.
        """
        current_viewable_position = self.list_steps[self.current_position].viewable_position
        if current_viewable_position == self.number_of_query_able_step:
            return None
        else:
            next_viewable_position = current_viewable_position + 1
            self.current_position += 1
            while self.list_steps[self.current_position].viewable_position \
                    != next_viewable_position:
                self.current_position += 1
            return self.list_steps[self.current_position]

    def get_previous_query_able_step(self):
        """ Return the previous query able step. If there is no query able step, it returns None.

        Returns:
             Return None if there is no previous query able step, or the previous query able step.
        """
        current_viewable_position = self.list_steps[self.current_position].viewable_position
        if current_viewable_position == 1:
            return None
        else:
            self.list_steps[self.current_position].clean_step()
            previous_viewable_position = current_viewable_position - 1
            self.current_position -= 1
            while self.list_steps[self.current_position].viewable_position != \
                    previous_viewable_position:
                self.list_steps[self.current_position].clean_step()
                self.current_position -= 1

            self.list_steps[self.current_position].update(choices=list())
            return self.list_steps[self.current_position]

    def get_previous_choices(self):
        """ Get the formatted the previous user choices.

        Return the previous user choices separated by "/".

        Returns:
             Return the formatted the previous user choices separated by "/".
        """
        prev_choices = list()
        for position in range(0, self.current_position + 1):
            if self.is_query_able(position):
                prev_choices.append(str(self.list_steps[position].choices))
        return " / ".join(prev_choices)

    def get_ids_files_last_step(self):
        """ Get the minimal list of files where data can be picked in. If there is no query able step, ie no choices,
        all the files linked to the query's schema will be returned.

        Returns:
             Minimal list of files from the database linked to the user choices.
        """
        last_query_able_step = self.get_last_query_able_step()
        if last_query_able_step is None:
            xml_data_list = system_api.get_all_by_template(ObjectId(self.query.schema))
            list_ids = list()
            for xml_data in xml_data_list:
                list_ids.append(xml_data.id)
            return list_ids

        if last_query_able_step.step.data_type == 'data':
            id_current_files = []
            for choice_id_file in last_query_able_step.list_choices_id_file:
                if choice_id_file.choice in last_query_able_step.choices:
                    for bucket in choice_id_file.list_buckets:
                        id_current_files.extend(bucket.list_files)
        else:
            id_current_files = last_query_able_step.files

        return [ObjectId(x) for x in list(set(id_current_files))]

    def is_query_able(self, position=None):
        """ Return if a step is query able.

        It returns True if the step is query able, False if the step is not query able. The
        tested step is the first one if the position is not given,
        or the step corresponding to the given position.

        Args:
            position: The position's step designing the tested step.

        Returns:
            Return True if the step is query able, False if the step is not query able.
        """
        if position is None:
            return self.list_steps[self.current_position].query_able
        else:
            return self.list_steps[position].query_able

    def is_current_first_step(self):
        """ Return if the current step is the first step.

        It returns True if the step is the first step, False if the step is not the first one.

        Returns:
            Return True if the step is query able, False if the step is not query able.
        """
        return self.get_current_step().viewable_position == 1

    def update_time(self):
        """ Update the query name.
        """
        self.update(last_modified=datetime.now())

    def save_to_history(self, user_id, history_id=None):
        """ Create or update the history query.

        Args:
            user_id: User id.
            history_id: History query associated. If none, the history has to be created.

        Returns:
            History id.
        """
        if history_id is None:
            history = HistoryQuery()
            history.query_id = str(self.id)
            history.status = 0
            history.user_id = user_id
            history.message = "Step " + \
                              str(self.get_current_step().viewable_position) + \
                              ": " + \
                              self.get_current_step().step.name
            history_id = history.save()
            self.update(history=history_id)
        else:
            history = HistoryQuery.objects.get(id=history_id)
            history.update(message="Step "
                                   + str(self.get_current_step().viewable_position)
                                   + ": "
                                   + self.get_current_step().step.name
                           )
        return history.id

    def update_message(self, _message):
        """ Update History message

        Args:
            _message: Message to be updated
        """
        TempUserQuery.objects.get(id=self.id).history.update(message=_message)

    def handle_history(self):
        """ Get previous choice and return step
        """
        choices = self.get_previous_choices()

        if choices[:-1] is not []:
            step = self.get_current_step()
            step.choices = []
            step.update(choices=[])
        else:
            raise ModelError("Previous choice does not exist")

        return step

    def create_files(self, dict_data, map_keys, list_headers, list_file_xml, list_file_json,
                     list_file_csv, depth, max_depth):
        """ Create the output file

        Args:
            dict_data: Tree of data.
            map_keys: Map a hash key to a key. The key is a dictionary representing a node.
            list_headers: List of headers parts common to all current element.
            list_file_xml: Different part of xml file.
            list_file_json: Different part of json file.
            list_file_csv: Different part of csv file.
            depth: Current depth in the tree.
            max_depth: Maximum depth in the tree.

        Returns:
            Output files.
        """

        if depth == max_depth:  # Leaf level
            if dict_data:
                list_keys = dict_data.keys()

                # Sort data if possible
                is_timestamp_present = True
                for hash_data in list_keys:
                    if "@timestamp" not in map_keys[hash_data].keys():
                        is_timestamp_present = False
                        break
                if is_timestamp_present:
                    list_keys = sorted(dict_data.keys(),
                                       key=lambda x: map_keys[x]['@timestamp'])

                # Keeping only the 10 000 last records
                if self.query.is_limited:
                    if self.query.number_records is not None:
                        list_keys = list_keys[-self.query.number_records:]

                if len(dict_data) > 1:
                    common_keys, list_specific_header = get_common_key_and_specific_header(
                        list_keys, map_keys)
                else:
                    common_keys = list()
                    list_specific_header = list_headers[:]  # Copy by slicing

                ddict_title_data = get_title_data_leaf(list_keys, map_keys)
                list_specific_header = list_headers + list_specific_header

                print_bloc(list_specific_header, ddict_title_data, common_keys,
                           list_file_xml,
                           list_file_json, list_file_csv)

            return
        else:  # Header level
            for key_hash, value in dict_data.iteritems():
                dict_key = map_keys[key_hash]
                list_header_actual_key = get_header_parents(dict_key)
                self.create_files(
                    dict_data=dict_data[key_hash],
                    map_keys=map_keys,
                    list_headers=list_headers + list_header_actual_key,
                    list_file_xml=list_file_xml,
                    list_file_json=list_file_json,
                    list_file_csv=list_file_csv,
                    depth=depth + 1,
                    max_depth=max_depth
                )
        return

    def init_data_result(self):
        """ Initialize the variables to create the files. Create the files and save them into the database.
        """
        translate_dt = maketrans("-:.T", '    ')  # Translate object for element date time
        translate_bounds = maketrans("-:", '  ')  # Translate object for bounds date time
        max_depth = self.number_of_step

        # Create the query
        ids_xml_data = self.get_ids_files_last_step()
        nb_files_total = len(ids_xml_data)
        first_step_xpath = self.list_steps[0].step.xpath.split("*")[0]
        full_projection = possible_projection("dict_content." + first_step_xpath)

        dict_query = {
            "template": ObjectId(self.query.schema),
            "_id": {
                "$in": ids_xml_data
            }
        }

        xml_data = [
            data.to_mongo()['dict_content']
            for data in system_api.execute_query_with_projection(dict_query, full_projection)
        ]

        depth = 0
        list_keys_xpath = []
        dict_data = dict()
        map_key = dict()
        list_nb_file_treated = list()
        list_nb_file_treated.append(1.0)

        # Get the filtered elements form the database.
        self.explore_elements(list(xml_data), list_keys_xpath, depth, max_depth, dict_data,
                              translate_dt, translate_bounds, map_key, list_nb_file_treated, nb_files_total)

        self.update_message("Creating output files.")

        list_step_dot_only = [x for x in self.list_steps if x.step.xpath == "."]
        max_depth -= len(list_step_dot_only) + 1

        # Create the output files
        depth = 0
        list_file_xml = list()
        list_file_json = list()
        list_file_csv = list()
        list_headers = list()

        list_file_json.append("{\r\n\t\"Data\": {\r\n\t\t\"Item\": [\r\n")
        list_file_xml.append("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\r\n<Data>\r\n")

        self.create_files(dict_data, map_key, list_headers, list_file_xml, list_file_json,
                          list_file_csv, depth, max_depth)

        file_csv = ''.join(list_file_csv)
        list_file_xml.append('</Data>')
        file_xml = ''.join(list_file_xml)
        file_json = ''.join(list_file_json)
        file_json = file_json[:-6] + file_json[-6:].replace(',', '')
        file_json += "\t\t]\r\n\t}\r\n}"

        self.update(str_id_file_json=TempOutputFile().save_file(str_file=file_json, type_file="json"))
        self.update(str_id_file_csv=TempOutputFile().save_file(str_file=file_csv, type_file="csv"))
        self.update(str_id_file_xml=TempOutputFile().save_file(str_file=file_xml, type_file="xml"))

        return

    def explore_elements(self, list_elements, list_keys_xpath, depth, max_depth, dict_to_add,
                         translate_dt, translate_bounds, map_key, list_nb_file_treated, nb_file_total):
        """ Explore the elements and filter them from an input file.

        Args:
            list_elements: List of current element.
            list_keys_xpath: List of sliced xpath.
            depth: Current depth in the element.
            max_depth: Maximum element depth.
            dict_to_add: Result dictionary.
            translate_dt: Translate python object for element date.
            translate_bounds: Translate python object for bounds date.
            map_key: Map between hash and dictionary.
            list_nb_file_treated: List used for the advancement percentage. Only the first element is used.
            nb_file_total:  Number of total files.
        """
        if depth == 1:
            self.update_message(
                "Gathering all data. - "
                + str("%.2f" % ((list_nb_file_treated[0] / nb_file_total) * 100))
                + " %"
            )
            list_nb_file_treated[0] += 1

        if depth == max_depth:
            return
        if not list_keys_xpath:
            # Create the list of xpath element for the current depth
            list_keys_xpath = [x for x in self.list_steps[depth].step.xpath.split(".") if x]
        element_title = list_keys_xpath[-1]

        while list_keys_xpath:
            key_xpath = list_keys_xpath.pop(0)
            if key_xpath == "*":
                # Solve start element
                set_possibilities = explore_star(list_elements)
                for key_possible in set_possibilities:
                    list_key_param_star = [key_possible]
                    if len(list_keys_xpath) != 0:
                        list_key_param_star.extend(list_keys_xpath)
                    self.explore_elements(
                        list_elements=list_elements,
                        list_keys_xpath=list_key_param_star,
                        depth=depth,
                        max_depth=max_depth,
                        dict_to_add=dict_to_add,
                        translate_dt=translate_dt,
                        translate_bounds=translate_bounds,
                        map_key=map_key,
                        list_nb_file_treated=list_nb_file_treated,
                        nb_file_total=nb_file_total,
                    )
                return
            else:
                # Go across all elements
                list_elements = [x.get(key_xpath) for x in list_elements if x.get(key_xpath)]

        # Flat the elements if an element i composed by a a list of elements
        if list_elements:
            if isinstance(list_elements[0], list):
                list_elements = flat_list(list_elements)

        # Apply the choices to the list of elements
        depth, list_elements_cleaned = self.apply_user_choices(list_elements, depth, max_depth,
                                                               element_title,
                                                               translate_dt, translate_bounds)

        if not list_elements_cleaned:
            return
        dict_to_str = hash
        for element in list_elements_cleaned:
            dict_key_output_master = get_general_key_output_dictionary(
                element, element_title)
            str_key_output_spec = dict_to_str(frozenset(dict_key_output_master.items()))

            if str_key_output_spec not in dict_to_add:
                map_key[str_key_output_spec] = dict_key_output_master
                dict_to_add[str_key_output_spec] = {}

            self.explore_elements(
                list_elements=[element],
                list_keys_xpath=[],
                depth=depth + 1,
                max_depth=max_depth,
                dict_to_add=dict_to_add[str_key_output_spec],
                translate_dt=translate_dt,
                translate_bounds=translate_bounds,
                map_key=map_key,
                list_nb_file_treated=list_nb_file_treated,
                nb_file_total=nb_file_total,
            )
        return

    def apply_user_choices(self, list_elements, depth, max_depth, element_title, translate_dt, translate_bounds):
        """ Apply user choices to a list of elements.

        Args:
            list_elements: List of elements to be filtered.
            depth: Current depth.
            max_depth: Maximum Depth.
            element_title: Current element title
            translate_dt: Translate python object for the element date time.
            translate_bounds: Translate python object for the bounds.

        Returns:
            depthm list cleaned elements
        """
        current_step = self.list_steps[depth]
        list_cleaned_elements = current_step.choose_filter_choice(
            list_elements=list_elements,
            element_title=element_title,
            translate_dt=translate_dt,
            translate_bounds=translate_bounds
        )

        while depth + 1 != max_depth and self.list_steps[depth + 1].step.xpath == ".":
            depth += 1
            current_step = self.list_steps[depth]
            list_cleaned_elements = current_step.choose_filter_choice(
                list_elements=list_cleaned_elements,  # FIXME: was list_elements (would ignore the first filter)
                element_title=element_title,
                translate_dt=translate_dt,
                translate_bounds=translate_bounds
            )
        return depth, list_cleaned_elements

    def add_query_to_waiting_line(self):
        """ Add query to the waiting line when the user end his choices.
        """
        query_to_treat = QueryToTreat()
        query_to_treat.query = self
        query_to_treat.save()

    def create_outputs_file(self):
        """ Create the output files
        """
        try:
            self.init_data_result()
        except Exception, e:
            current_step = self.get_current_step()
            log_file = LogFile(application="Custom Queries",
                               message="The step #"
                                       + str(current_step.absolute_position)
                                       + ": " + str(current_step.step.name)
                                       + " is not a valid timestamp."
                                       + str(e.message),
                               additionalInformation={'query_name': self.query_name,
                                                      'Status': "Result builder"},
                               timestamp=datetime.now())
            log_file_api.upsert(log_file)
            self.update_message("Error during result files creation.")
            return

        self.update_message("Result files created.")
        # Get the user to send him an email
        try:
            history = HistoryQuery.objects.get(query_id=str(self.id))
            user = User.objects.get(id=history.user_id)
            send_mail_query_end(query=self, user=user)
        except:
            pass
        self.update_status(2)

    def update_status(self, new_status):
        TempUserQuery.objects.get(id=self.id).history.update(status=new_status)


class QueryToTreat(Document):
    """ List of query waiting to be treated.
    """
    query = fields.ReferenceField(TempUserQuery, blank=True)

    @staticmethod
    def get_all():
        """ Return all QueryToTreat.

        Returns:

        """
        return QueryToTreat.objects().all()

    def delete_database(self):
        """ Delete function.
        """
        self.delete()
