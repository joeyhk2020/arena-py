from .arena_object import Object

class HandLeft(Object):
    """
    Class for VR Controllers Left in the ARENA.
    """
    object_type = "handLeft"

    def __init__(self, **kwargs):
        super().__init__(object_type=HandLeft.object_type, **kwargs)
        self.user = kwargs.get("data").get("dep", None)




    # def update_attributes(self, evt_handler=None, **kwargs):
    #     self.user = kwargs.get("data").get("dep", None)

class HandRight(Object):
    """
    Class for VR Controllers Right in the ARENA.
    """
    object_type = "handRight"

    def __init__(self, **kwargs):
        super().__init__(object_type=HandRight.object_type, **kwargs)
        self.user = kwargs.get("data").get("dep", None)




    # def update_attributes(self, evt_handler=None, **kwargs):
    #     self.user = kwargs.get("data", None).get("dep", None)


