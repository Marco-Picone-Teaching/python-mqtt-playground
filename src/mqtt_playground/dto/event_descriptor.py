import json


class EventDescriptor:
    """ EventDescriptor class contains the event information """

    def __init__(self, timestamp, event_type, event_value):
        """
        Constructor for EventDescriptor class
        :param timestamp: Timestamp of the event
        :param event_type: Type of the event
        :param event_value: Value of the event
        """

        self.timestamp = timestamp
        self.event_type = event_type
        self.event_value = event_value

    def to_json(self):
        """ Convert the object to a JSON string """
        return json.dumps(self, default=lambda o: o.__dict__)
