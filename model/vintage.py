

class Vintage():
    def __init__(self, param):
        self.id = -1
        if type(param) is int:
            self.id = param
        if type(param) is dict and "id" in param:
            self.id = param["id"]