import traceback
from services.queries import get_graph


class Package():
    def __init__(self, package_type=None, package=None):
        self.package = package
        self.id = -1
        if type(package_type) is int:
            self.id = package_type
        else:
            self.type = package_type

    @staticmethod
    def exist(type):
        try:
            query = "MATCH (p:PackageType) WHERE lower(p.Name) = lower(\"" + type + "\") RETURN p"
            result = get_graph().cypher.execute(query)
            return len(result) > 0
        except Exception:
            print traceback.format_exc()
