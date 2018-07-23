""" Exceptions
"""


class EmptyChoicesFromQuery(Exception):
    def __init__(self, x_path='', schema=''):
        if x_path != '':
            self.message = "There is no choice for the user with the x_path: " + str(x_path)
        else:
            self.message = "There is not XMLData linked to the schema " + str(schema) + "."
