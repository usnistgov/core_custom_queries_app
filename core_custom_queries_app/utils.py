"""
Python functions used in the algorithm.
"""
from collections import defaultdict
from itertools import chain, ifilterfalse
from json import dumps

from core_main_app.utils.notifications.mail import send_mail


def get_dict_element_header(title=None, k=None, v=None):
    """
    File creation function - Get data for output file
    :param title: Element title
    :param k: Key value
    :param v: Value associated to the key
    :return: Dictionary with the [title], the key and the value
    """
    if title:
        return {
            "title": title,
            "key": k,
            "value": v
        }
    else:
        return {
            "key": k,
            "value": v
        }


def get_header_parents(dict_key):
    """
    Get information from parent elements.
    :param dict_key: Dictionary of keys.
    :return: List of dictionaries composed by parent element.
    """
    title = dict_key.get("#title")
    if len(dict_key) == 1:
        return [
            get_dict_element_header(title)
        ]
    else:
        return [
            get_dict_element_header(title, k, v)
            for k, v in dict_key.iteritems()
            if k != "#title"
            ]


def get_title_data_leaf(list_leaves, map_keys):
    """
    Get title for leaf elements.
    :param list_leaves: List of leaf elements.
    :param map_keys: Map of hash and elements.
    """
    ddict_title_data = defaultdict(list)
    for hash_leaf in list_leaves:
        leaf = map_keys[hash_leaf]
        title = leaf.pop("#title")
        ddict_title_data[title].append(leaf)
    return ddict_title_data


def get_common_key_and_specific_header(list_leaves, map_keys):
    """
    Get all the common key and value in the dict_leaves.
    :param list_leaves: List of leaves
    :param map_keys: Map of hash and elements.
    :return: List of unique keys and list of specific headers
    """
    dict_key_set_value = dict()
    list_keys = list()
    first = True

    for key_hash in list_leaves:
        dict_leaf = map_keys[key_hash]
        if first:
            for k_first, v_first in dict_leaf.iteritems():
                dict_key_set_value[k_first] = v_first
            list_keys = dict_key_set_value.keys()
            first = False
        else:
            for k, v in dict_leaf.iteritems():
                if k in list_keys \
                        and k in dict_key_set_value \
                        and v != dict_key_set_value[k]:
                    dict_key_set_value.pop(k)
    node_name = None
    if "#title" in dict_key_set_value.keys():
        node_name = dict_key_set_value["#title"]
    list_keys_headers_common = [
        (k, get_dict_element_header(node_name, k, v))
        for k, v in dict_key_set_value.iteritems()]
    list_keys_unique = list()
    list_specific_header = list()
    for keys_headers_common in list_keys_headers_common:
        list_keys_unique.append(keys_headers_common[0])
        list_specific_header.append(keys_headers_common[1])
    return list_keys_unique, list_specific_header


def print_bloc(list_specific_header, ddict_title_data, common_keys,
               list_file_xml, list_file_json, list_file_csv):
    """
    File creation function - Print data into output file

    :param list_specific_header: List of specific headers.
    :param ddict_title_data: Default dictionary of title
    :param common_keys: Common keys between the list of specific elements
    :param list_file_xml: Different parts of xml file.
    :param list_file_json: Different parts of json file.
    :param list_file_csv: Different parts of csv file.
    """

    print_headers(list_specific_header, list_file_xml, list_file_json,
                  list_file_csv)

    for title_leaf, list_dict_leaf in ddict_title_data.iteritems():
        print_leaves(title_leaf, list_dict_leaf, common_keys, list_file_xml, list_file_json,
                     list_file_csv)

    list_file_json[-1] = list_file_json[-1][:-3] + list_file_json[-1][-2:]  # Delete last ,
    list_file_json.append(3 * "\t" + "},\r\n")
    list_file_xml.append("\t</Item>\r\n")


def print_headers(list_headers, list_file_xml, list_file_json, list_file_csv):
    """
    File creation function - Print header into output file

    :param list_headers: List of headers
    :param list_file_xml: Different parts of xml file.
    :param list_file_json: Different parts of json file.
    :param list_file_csv: Different parts of csv file.
    """
    list_particular_header_csv = list()
    list_particular_header_json = list()
    list_particular_header_xml = ["\t<Item "]

    list_file_json.append(3 * "\t" + "{\r\n")

    for header in list_headers:
        if header["key"] is not None:
            if "title" in header:
                if header["key"] != "#title":
                    list_particular_header_csv.append("_".join((header["title"], header["key"], str(header["value"]))))
                    list_particular_header_json.append(": ".join(
                        (
                            "\"-" + str(header["title"])
                            + "_"
                            + str(header["key"]).replace("@", "", 1)
                            + "\"",
                            "\"" + str(header["value"]) + "\""
                        )
                    ))
                    list_particular_header_xml.append("=".join(
                        (
                            str(header["title"])
                            + "_"
                            + str(header["key"]).replace("@", "", 1),
                            "\"" + str(header["value"]) + "\""
                        )
                    ))

            elif header["key"] != "#title":
                list_particular_header_csv.append("_".join((str(header["key"]), str(header["value"]))))
                list_particular_header_json.append(": ".join(
                    (
                        "\"-" + str(header["key"]).replace("@", "", 1) + "\"",
                        "\"" + str(header["value"]) + "\""
                    )
                ))

                list_particular_header_xml.append("=".join(
                    (
                        str(header["key"]).replace("@", "", 1),
                        "\"" + str(header["value"]) + "\""
                    )
                ))
        else:
            list_particular_header_csv.append(str(header["title"]))

    list_file_csv.append(", ".join(list_particular_header_csv) + "\r\n")
    list_file_json.append("\t\t\t\t" + ",\r\n\t\t\t\t".join(list_particular_header_json) + ",\r\n")
    list_file_xml.append(" ".join(list_particular_header_xml) + ">\r\n")


def print_leaves(title_leaf, list_dict_leaf, common_keys, list_file_xml, list_file_json, list_file_csv):
    """
    File creation function - Print leaf element into output file

    :param title_leaf: Title of the leaf
    :param list_dict_leaf: Element of the leaf
    :param common_keys: List of common keys
    :param list_file_xml: Different parts of xml file.
    :param list_file_json: Different parts of json file.
    :param list_file_csv: Different parts of csv file.
    :return:
    """
    common_keys_to_avoid = []
    if len(common_keys) != 1:
        common_keys_to_avoid = common_keys

    list_file_json.append(4 * "\t" + "\"" + title_leaf + "\": [\r\n")
    for leaf in list_dict_leaf:
        list_file_csv.append("," + ", ".join(
            [
                title_leaf + ": ".join((str(k_leaf), str(v_leaf)))
                for k_leaf, v_leaf in leaf.iteritems()
                if k_leaf not in common_keys_to_avoid
                ]
        ) + "\r\n")

        list_file_json.append(5 * "\t" + "{\r\n" + 6 * "\t" + ",\r\n\t\t\t\t\t\t".join(
            [
                ": ".join(
                    (
                        "\"" + str(k_leaf).replace("@", "-") + "\"",
                        dumps(str(v_leaf))
                    )
                )
                for k_leaf, v_leaf in leaf.iteritems()
                if k_leaf not in common_keys_to_avoid
                ]
        ) + "\r\n" + 5 * "\t" + "},\r\n" )

        list_file_xml.append(2 * "\t" + "<" + title_leaf + " " + " ".join(
            [
                "=".join(
                    (
                        str(k_leaf).replace("@", ""),
                        "\"" + str(v_leaf) + "\""
                    )
                )
                for k_leaf, v_leaf in leaf.iteritems()
                if k_leaf not in common_keys_to_avoid and k_leaf != "#text"
            ]))

        if "#text" in leaf:
            list_file_xml.append("> ")
            list_file_xml.append(str(leaf["#text"]))
            list_file_xml.append(" </")
            list_file_xml.append(title_leaf)
            list_file_xml.append(">\r\n")
        else:
            list_file_xml.append("/>\r\n")

    list_file_json[-1] = list_file_json[-1][:-3] + list_file_json[-1][-2:]  # Delete last ","
    list_file_json.append(4 * "\t" + "],\r\n")


# Gathered data function
def flat_list(list_elements):
    """
    Flat a list of list into a list: [[1,2,3],[4,5,6]] ==> [1,2,3,4,5,6]

    :param list_elements: List of elements
    :return: List of flattened lists.
    """
    return list(chain.from_iterable(list_elements))


def explore_star(list_elements):
    """
    Get list of possible element to solve "*".
    :param list_elements: List of element to solve.
    :return: List of elements to replace the star.
    """
    return ifilterfalse(lambda x: x[0] in ['_', '@', "#"], set(chain.from_iterable(list_elements)))


def get_general_key_output_dictionary(element_cleaned, element_title):
    """
    Create a dictionary from a node attribute. The title is added.
    :param element_cleaned: Element cleaned to transform.
    :param element_title: Element title.
    :return: Element dictionary.
    """
    dict_key_general = {x: y for x, y in element_cleaned.iteritems() if x[0] in ("@", "#")}
    dict_key_general["#title"] = element_title
    return dict_key_general


def get_list_keys_from_xpath(xpath):
    """
    Split an xpath by the ".".
    :param xpath: the XPath to split.
    :return: List of XPath parts.
    """
    list_keys = xpath.split(".")
    if list_keys[-1] == "":
        list_keys = list_keys[:-1]
    if list_keys[0] == "":
        list_keys = list_keys[1:]

    return list_keys


def is_datetime_inf_or_equal(date_ref, date_comp):
    """
        Compare if date_ref <= date_comp

        Compare efficiently if date_ref <= date_comp. The date_comp is duplicated to allow the
        chaining function: is datetime_inf_or_equal(a, b), datetime_inf_or_equal(b, c) ...

        :param date_ref: Reference date, format: [Year, Month, Day, Hour, Minute, Second]
        :param date_comp: Compare date, format: [Year, Month, Day, Hour, Minute, Second]
        :return: True if date_ref <= date_comp, False if date_ref > date_comp
    """
    i = 0
    while date_ref[i] == date_comp[i] and i != 4:
        i += 1

    if date_ref[i] < date_comp[i] or i == 4:
        return True
    return False


# Prepare data for DB query
def possible_projection(str_projection):
    """
    Get the possible projection.
    "a.b.c"         ==> "a.b.c"
    "a.b.c.*"       ==> "a.b.c"
    "a.b.c.*.*"     ==> "a.b.c"
    "a.b.c.@title"  ==> "a.b.c"
    :param str_projection: String
    :return:
    """
    str_possible_projection = (str_projection.split("*")[0].split("@title")[0])
    if str_possible_projection.endswith("."):
        return str_possible_projection[:-1]
    else:
        return str_possible_projection


def send_mail_query_end(user, query):
    """
    Send the mail end query to the user.

    :param user: User to send the mail to
    :param query: Ended query
    """
    context = {
        'lastname': user.last_name,
        'firstname': user.first_name,
        'query_name': query.query.name
    }

    send_mail(subject='Query ended',
              path_to_template='core_custom_queries_app/user/email/end_query.html',
              context=context, recipient_list=[user.email])
