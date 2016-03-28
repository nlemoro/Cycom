import json
import traceback
from services.queries import *


class Wine:
    def __init__(self, param=None):
        try:
            if param is not None:
                if 'name' in param:
                    self.name = param['name']
                if 'name_without_accent' in param:
                    self.name_without_accent = param['name_without_accent']
                if 'appellation' in param:
                    self.appellation = param['appellation']
                if 'color' in param:
                    self.color = param['color']
                if 'vintage' in param:
                    self.vintage = str(param['vintage'])
                if 'format' in param:
                    self.format = param['format']
                if 'package' in param:
                    self.package = param['package']
                if 'package_type' in param:
                    self.package_type = param['package_type']
                if 'winery' in param:
                    self.winery = param['winery']
                if 'picture' in param:
                    self.picture = param['picture']
                if 'comment' in param:
                    self.comment = param['comment']
        except Exception as e:
            print traceback.format_exc()

    def __eq__(self, obj):
        if isinstance(obj, Wine):
            try:
                result = obj.name == self.name and obj.color == self.color and obj.vintage == self.vintage
            except Exception as e:
                print e
                return False
            return result
        return NotImplemented

    def __ne__(self, obj):
        result = self.__eq__(obj)
        if result is NotImplemented:
            return result
        return not result

    def create(self, company):
        try:
            if company:
                query = "MATCH (soc:Company), (a:Appelation), (c:Color) "
                if self.winery:
                    query += ", (wr:Winery) "
                query += "WHERE lower(soc.Name) = lower(\"" + company + "\") AND lower(a.Name) = lower(\"" + self.appellation + "\") AND lower(c.Name) = lower(\"" + self.color + "\") "
                if self.winery:
                    query += "AND lower(wr.Name) = lower(\"" + self.winery + "\") "
                query += "CREATE (a)<-[:REL_HAS]-(w:Wine { Name: \"" + self.name + "\", NameWithoutAccent: \"" + self.name_without_accent + "\""
                if self.picture:
                    query += ", Picture: \"" + self.picture + "\""
                if self.comment:
                    query += ", Comment: \"" + self.comment + "\""
                query += "})-[:REL_HAS]->(c), (ws:WineSynonyme { Name: \"" + self.name + "\", NameWithoutAccent: \"" + self.name_without_accent + "\"})-[:REL_HAS]->(w)-[:REL_HAS]->(soc) "
                if self.winery:
                    query += "CREATE (w)-[:REL_HAS]->(wr)"
                result = get_graph().cypher.execute(query)
        except Exception as e:
            print traceback.format_exc()

    def is_obvious(self):
        wine = self.exist_wine_name()
        if wine is None:
            return False
        appellation = self.exist_appellation_name()
        color = self.exist_color_name()
        query = "MATCH (c:Color)-[]-(w:Wine)-[]-(a:Appelation) WHERE w.Name = \"" + wine
        query += "\" AND (c.Name = \"" + (color if color else "") + "\" OR a.Name = \""
        query += (appellation if appellation else "") + "\") return c.Name as color, w.Name as wine, a.Name as appellation"
        result = get_graph().cypher.execute(query)
        if len(result) == 1:
            self.name = result[0].wine
            self.color = result[0].color
            self.appellation = result[0].appellation
            return True
        return False

    def exist_wine_name(self):
        query = "MATCH (w:Wine)-[]-(ws:WineSynonyme) WHERE lower(ws.Name) = lower(\"" + self.name + "\") RETURN w.Name as n"
        result = get_graph().cypher.execute(query)
        if len(result):
            return result[0].n
        return None

    def exist_appellation_name(self):
        query = "MATCH (a:Appelation)-[]-(as:AppelationSynonyme) WHERE lower(as.Name) = lower(\"" + self.appellation + "\") RETURN a.Name as n"
        result = get_graph().cypher.execute(query)
        if len(result):
            return result[0].n
        return None

    def exist_color_name(self):
        query = "MATCH (c:Color)-[]-(cs:ColorSynonyme) WHERE lower(cs.Name) = lower(\"" + self.color + "\") RETURN c.Name as n"
        result = get_graph().cypher.execute(query)
        if len(result):
            return result[0].n
        return None

    def __str__(self):
        return json.dumps(self.__dict__)

