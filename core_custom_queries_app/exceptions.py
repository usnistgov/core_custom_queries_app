""" Custom queries exceptions
"""


class EmptyChoicesFromQuery(Exception):
    def __init__(self, x_path="", schema=""):
        if x_path != "":
            self.message = "There is no choice for the user with the xpath %s" % str(x_path)
        else:
            self.message = "There is no XML data linked to the schema %s." % str(schema)
