# -*- coding: utf-8 -*-

from services.queries import get_graph

from abc import abstractmethod


class WineLine():
    def __init__(self, param=None):
        self.id = -1
        if type(param) is int:
            self.id = param
        if type(param) is dict and "id" in param:
            self.id = param["id"]

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def fusion(self):
        pass


class WineLineOK(WineLine):
    def __init__(self, param=None):
        WineLine.__init__(self, param)
        if type(param) is dict:
            self.vin_id = param['vin_id']
            self.appellation_id = param['appellation_id']
            self.couleur_id = param['couleur_id']
            self.wine = param['vin']
            self.appellation = param['appellation']
            self.couleur = param['couleur']
            self.ref_wds = param['ref_wds']
            self.winery = param['winery']
            self.winery_id = param['winery_id']
            self.name_without_accent = param['name_without_accent']
            self.ref_wine = param['ref_wine']

    def update(self):
        #Suppression des liens
        query = "MATCH (v:Vintage)-[r1]-(w:Wine)-[r2]-(a:Appelation) "
        query += ", (w)-[r3]->(c:Color), (w:Wine)-[r4]->(n:Winery) "
        query += " WHERE id(w) = " + str(self.vin_id) + " "
        query += "DELETE r2, r3, r4"
        get_graph().cypher.execute(query)

        #Création des nouveaux liens + set sur les nouvelles données
        query = "MATCH (w), (a), (c), (n) WHERE id(w) = " + str(self.vin_id) + " "
        query += "AND id(a) = " + str(self.appellation_id) + " "
        query += "AND id(c) = " + str(self.couleur_id) + " "
        query += "AND id(n) = " + str(self.winery_id) + " "
        query += "MERGE ((w)-[:REL_HAS]->(a)) MERGE ((w)-[:REL_HAS]->(c)) MERGE ((w)-[:REL_HAS]->(n)) "
        query += "SET w.Name = \"" + self.wine + "\" "
        query += "SET w.NameWithoutAccent = \"" + self.name_without_accent + "\""
        query += "SET w.RefWine = \"" + self.ref_wine + "\""
        get_graph().cypher.execute(query)

class FusionVin(WineLine):
    def __init__(self, param=None):
        WineLine.__init__(self, param)
        if type(param) is dict:
            self.vin_source_id = param['vin_source_id']
            self.vin_cible_id = param['vin_cible_id']
            self.vin_source_vintage_id = param['vin_source_vintage_id']
            self.vin_source_vintage = param['vin_source_vintage']
            self.vin_source_synonyme_id = param['vin_source_synonyme_id']

    def fusion(self):
        #On "Marque" les vintages du vin cible pour préparer le Merge des OfferLineOk
        query = "MATCH (v:Vintage)-[r1]-(w:Wine) "
        query += "WHERE id(w) in [" + str(self.vin_cible_id) + "] "
        query += "SET v.Status = \"cible\""
        #query += "RETURN v, w, ws "
        get_graph().cypher.execute(query)

        #On Crée une relations entre le vin source et le vin cible afin de pouvoir récupérer les id une fois fusionnés
        query = "MATCH (w:Wine) "
        query += "WHERE id(w) in [" + str(self.vin_cible_id) + ", " + str(self.vin_source_id) + "] "
        query += "WITH w "
        query += "START n=node(" + str(self.vin_cible_id) + "), m=node(" + str(self.vin_source_id) + ") "
        query += "MERGE (n)<-[:IS_FUSION]-(m) "
        query += "SET m.IsFusion = " + str(self.vin_cible_id) + " "
        get_graph().cypher.execute(query)

        #On MERGE les nouveaux liens
        query = "MATCH (v:Vintage), (w:Wine), (ws:WineSynonyme) "
        query += "WHERE id(w) in [" + str(self.vin_cible_id) + "] "
        query += "AND id(v) in " + str(self.vin_source_vintage_id) + " "
        query += "AND id(ws) in " + str(self.vin_source_synonyme_id) + " "
        query += "MERGE ((v)-[r:REL_HAS]->(w))"
        query += "MERGE ((ws)-[:REL_HAS]->(w))"
        #query += "RETURN v, w, ws "
        get_graph().cypher.execute(query)

        #On met une propriété IsDelete = TRUE sur les anciennes relations
        query = "MATCH (v:Vintage)-[r1]-(w:Wine)-[r2]-(ws:WineSynonyme) "
        query += "WHERE id(w) in [" + str(self.vin_source_id) + "] "
        query += "AND id(v) in " + str(self.vin_source_vintage_id) + " "
        query += "AND id(ws) in " + str(self.vin_source_synonyme_id) + " "
        query += "SET r1.IsDelete = TRUE "
        query += "SET r2.IsDelete = TRUE "
        query += "SET w.IsDelete = TRUE "
        #query += "RETURN v, w, ws "
        get_graph().cypher.execute(query)

        #Fusion des OfferLineOK sur les vintage qui n'ont pas été MERGE
        query = "MATCH (w)-[r1]-(v) "
        query += "WHERE id(w) in [" + str(self.vin_cible_id) + "] AND v.Year in " + str(self.vin_source_vintage) + " "
        query += "WITH v "
        query += "ORDER BY v.Status "
        query += "WITH v.Year AS year, collect(v) AS vintage, count(*) AS cnt "
        #query += "WHERE cnt > 0 "
        query += "WITH head(vintage) AS first, tail(vintage) AS rest "
        #query += "LIMIT 10000 "
        query += "UNWIND rest AS to_delete "
        query += "MATCH (to_delete)<-[r:REL_HAS]-(oflo:OfferLineOK) "
        query += "SET r.IsDelete = TRUE "
        query += "MERGE (first)<-[r2:REL_HAS]-(oflo) "
        query += "SET r2.Status = \"New\" "
        #query += "RETURN count(*); "
        get_graph().cypher.execute(query)

        #SET de la propriété IsDelete = TRUE sur les vintage en doublons
        query = "MATCH (w:Wine)-[r1]-(v:Vintage)  "
        query += "WHERE id(w) in [" + str(self.vin_cible_id) + "] "
        query += "WITH v.Year as Year, count(v.Year) as cntYear, collect(v) as vintage  "
        query += "WHERE cntYear > 1  "
        query += "UNWIND vintage as to_delete  "
        query += "MATCH (to_delete)-[]-(w)  "
        query += "WHERE id(w) in [" + str(self.vin_source_id) + "] "
        query += "SET to_delete.IsDelete = TRUE  "
        #query += "RETURN Year, cntYear, to_delete  "
        get_graph().cypher.execute(query)

        #DELETE des relations ayant comme propriété isDelete
        #query = "MATCH (w:Wine)-[r1]-(v:Vintage)  "
        #query += "WHERE id(w) in [" + str(self.vin_cible_id) + "] "
        #query += "WITH v.Year as Year, count(v.Year) as cntYear, collect(v) as vintage  "
        #query += "WHERE cntYear > 1  "
        #query += "UNWIND vintage as to_delete  "
        #query += "MATCH (to_delete)-[]-(w)  "
        #query += "WHERE id(w) in [" + str(self.vin_source_id) + "] "
        #query += "SET to_delete.IsDelete = TRUE  "
        #query += "RETURN Year, cntYear, to_delete  "
        #get_graph().cypher.execute(query)
