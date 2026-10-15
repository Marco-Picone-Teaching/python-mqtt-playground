

class SwitchActuator:
    """ This class represents a switch actuator that can turn ON or OFF a device """

    def __init__(self):
        """ Constructor for SwitchActuator class """

        # Set the initial temperature value to 0.0
        self.switch_status = True

    def set_switch_status(self, switch_statue):
        """ Method to set the switch statue """
        self.switch_status = switch_statue

    def change_switch_status(self):
        """ Method to change the switch statue """
        # Generate a random switch statue value
        self.switch_status = not self.switch_status
