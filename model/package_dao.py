import traceback
from services.queries import get_graph
from package import Package


class PackageDAO():
    def __init__(self):
        pass

    @staticmethod
    def get_package_list():
        tab = []
        query = "MATCH (p:PackageType) RETURN p.Name AS package"
        result = get_graph().cypher.execute(query)
        for it in result:
            tab.append(Package(it.package))
        return tab
