import json


class ActionDescriptor:
    """ ActionDescriptor class contains the action information """

    def __init__(self, action_type, action_value):
        """ Constructor for DeviceDescriptor class """
        self.action_type = action_type
        self.action_value = action_value

    def to_json(self):
        """ Convert the object to a JSON string """
        return json.dumps(self, default=lambda o: o.__dict__)

