class BaseFault:
    """
    Standard interface Sensei expects.
    Converts simple check() faults into .result()
    """

    def __init__(self):
        self._result = None

    def check(self, msg):
        """
        Must be implemented by child classes.
        Should set self._result internally.
        """
        raise NotImplementedError

    def result(self):
        return self._result