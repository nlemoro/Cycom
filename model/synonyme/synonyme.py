import unicodedata
from services.queries import get_graph


class Synonyme():
    def __init__(self, synonyme=None, to_link=False):
        if type(synonyme) is int:
            self.id = synonyme
        if synonyme is None:
            pass
        elif type(synonyme) is dict:
            self.id = None
            self.synonyme = synonyme
        else:
            self.id = synonyme._id
            self.synonyme = synonyme.properties
        if to_link:
            try:
                node = self.get_linked_node()
                self.linked_node = node.properties
                self.linked_node["id"] = node._id
            except Exception:
                self.linked_node = None

    def create(self, node):
        query = "MATCH (n) where id(n) = " + self.linked_node["id"] + " MERGE (s:" + node + "Synonyme{Name: \"" + self.synonyme["Name"] + "\"})-[:REL_HAS]->(n) RETURN s"
        result = get_graph().cypher.execute(query)
        self.id = result[0].s._id

    def get_linked_node(self):
        query = "MATCH (s)-[]-(n) WHERE id(s) = " + str(self.id) + " RETURN n"
        result = get_graph().cypher.execute(query)
        return result[0].n

    def delete(self):
        query = "MATCH (n)-[r]-() WHERE id(n) = " + str(self.id) + " DELETE n,r"
        get_graph().cypher.execute(query)

    def create_name_without_accent(self):
        name_without_accent = unicodedata.normalize('NFKD', self.synonyme["Name"]).encode('ASCII', 'ignore')
        query = "MATCH (s) WHERE id(s) = " + str(self.id) + " SET s.NameWithoutAccent = \"" + name_without_accent + "\" RETURN s"
        get_graph().cypher.execute(query)