import json


class DeviceDescriptor:
    """ DeviceDescriptor class contains the device information """

    def __init__(self, device_id: str, producer: str, software_version: str) -> None:
        """ Constructor for DeviceDescriptor class """
        self.device_id = device_id
        self.producer = producer
        self.software_version = software_version

    def to_json(self) -> str:
        """ Convert the object to a JSON string """
        return json.dumps(self, default=lambda o: o.__dict__)

