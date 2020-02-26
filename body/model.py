
class Leg3Dof(object):

    def __init__(self, offset: (int, int, int)) -> None:
        super().__init__()
        self.offset = offset
        self.s = (0.0, 0.0, 0.0)


class BodyModel(object):
    pass