from synonyme import Synonyme
from services.queries import get_graph


class SynonymeDAO():
    def __init__(self):
        pass

    @staticmethod
    def get_list(node, syn_name=None, linked_id=None):
        where = ""
        if syn_name is not None and linked_id is None:
            where = "s.Name =~ \"(?i).*" + syn_name + ".*\" AND "
        elif syn_name is None and linked_id is not None:
            where = "id(n) = " + str(linked_id) + " AND "
        elif syn_name is not None and linked_id is not None:
            where = "id(n) = " + str(linked_id) + " AND s.Name =~ \"(?i).*" + syn_name + ".*\" AND "
        where += "lower(s.Name) <> lower(n.Name) "
        query = "MATCH (s:" + node + "Synonyme)-[]-(n) WHERE " + where + "RETURN s ORDER BY n.Name"
        result = get_graph().cypher.execute(query)
        tab = []
        for it in result:
            tab.append(Synonyme(it.s, True))
        return tab

    @staticmethod
    def get_list_without_accent_less(node):
        query = "MATCH (s:" + node + "Synonyme)-[]-(n) WHERE HAS(s.NameWithoutAccent) = false RETURN s ORDER BY n.Name"
        result = get_graph().cypher.execute(query)
        tab = []
        for it in result:
            tab.append(Synonyme(it.s))
        return tab

    @staticmethod
    def get_list_full(node):
        where = ""
        query = "MATCH (s:" + node + "Synonyme)-[]-(n) RETURN s ORDER BY n.Name"
        result = get_graph().cypher.execute(query)
        tab = []
        for it in result:
            tab.append(Synonyme(it.s, True))
        return tab