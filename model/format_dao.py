from format import Format
import traceback
from services.queries import get_graph


class FormatDAO:

    def __init__(self):
        pass

    @staticmethod
    def get_format_from_synonyme(synonyme):
        try:
            query = "MATCH (fs:FormatSynonyme)-[]-(f:Format) WHERE lower(fs.Name) = lower(\"" + synonyme + "\") RETURN f.Name AS format LIMIT 1"
            result = get_graph().cypher.execute(query)
            if len(result) != 0:
                return Format(result[0].format)
            return None
        except Exception:
            print traceback.format_exc()
            return None