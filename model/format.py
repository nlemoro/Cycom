import traceback
from services.queries import get_graph


class Format:
    def __init__(self, param=None):
        try:
            self.id = -1
            if isinstance(param, Format):
                param = param.name
                self.id = param.id
            elif type(param) is int:
                self.id = param
            self.name = param
        except Exception:
            print traceback.format_exc()

    def exist(self):
        if self.name == "-":
            return False
        query = "MATCH (fs:FormatSynonyme)-[]-(f:Format) WHERE lower(fs.Name) = lower(\"" + self.name + "\") RETURN f.Name AS format LIMIT 1"
        result = get_graph().cypher.execute(query)
        if len(result):
            return True
        return False