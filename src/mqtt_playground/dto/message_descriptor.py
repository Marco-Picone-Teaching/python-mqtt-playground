import json


class MessageDescriptor:
    """ MessageDescriptor class contains the message information """

    def __init__(self, timestamp, value_type, value):
        """ Constructor for MessageDescriptor class wih the following parameters:
        :param timestamp: The timestamp of the message
        :param value_type: The type of the value
        :param value: The value of the message
        """

        self.timestamp = timestamp
        self.value_type = value_type
        self.value = value

    def to_json(self):
        """ Convert the object to a JSON string """
        return json.dumps(self, default=lambda o: o.__dict__)
