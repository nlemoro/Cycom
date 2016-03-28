# -*- coding: utf-8 -*-

import traceback
from model.vintage import Vintage
from model.package import Package
from model.format import Format
from ressourses.response import Response
from model.offer import Offer
from model.wine import Wine
from services.queries import get_graph
from services.parsing import parse_regie

from abc import abstractmethod


class OfferLine():
    def __init__(self, param=None):
        self.id = -1
        if type(param) is int:
            self.id = param
        if type(param) is dict and "id" in param:
            self.id = param["id"]

    @abstractmethod
    def update(self):
        pass


class OfferLineOK(OfferLine):
    def __init__(self, param=None):
        OfferLine.__init__(self, param)
        if type(param) is dict:
            self.format = Format(param["format_id"])
            self.regie = param["regie"]
            self.package = Package(param["package_type_id"], param["package"])
            self.release_price = param["release_price"] if param["release_price"] is not None else "\"\""
            self.selling_price = param["selling_price"] if param["selling_price"] is not None else "\"\""
            self.comment = param["comment"]
            self.vintage = Vintage(param["vintage_id"])

    def update(self):
        # Suppression des anciens liens avec le format + type de conditionnement
        query = "MATCH (p:PackageType)-[r1]-(o)-[r2]-(f:Format) WHERE id(o) = " + str(self.id) + " "
        query += "DELETE r1, r2"
        get_graph().cypher.execute(query)

        # Création liens avec le nouveau format + nouveau type de conditionnement
        query = "MATCH (o), (f), (p), (v) WHERE id(o) = " + str(self.id) + " AND id(f) = " + str(self.format.id) + " "
        query += "AND id(v) = " + str(self.vintage.id) + " "
        query += "AND id(p) = " + str(self.package.id) + " MERGE (p)<-[:REL_HAS]-(o)-[:REL_HAS]->(f) SET o.Regie = \"" + self.regie + "\", "
        query += "o.Comment = \"" + self.comment + "\", v.ReleasePrice = " + str(self.release_price) + ", v.SellingPrice = " + str(self.selling_price)
        query += ", o.Package = \"" + str(self.package.package) + "\""
        get_graph().cypher.execute(query)

    def logical_remove(self):
        query = "MATCH (n) WHERE id(n) = " + str(self.id) + " SET n.IsDeleted = true"
        get_graph().cypher.execute(query)


class OfferLineKO:
    def __init__(self, table=None, offer_line_id=None):
        if table is not None:
            if 'id_ko' in table:
                self.id_ko = table['id_ko']
            self.wine = Wine(table)
            self.quantity = table["quantity"]
            self.price = table["price"]
            self.regie = parse_regie(table["regie"])
            if 'comment' in table:
                self.comment = table['comment']
            else:
                self.comment = ""
        elif offer_line_id is not None:
            self.id = offer_line_id

    def remove(self):
        try:
            graph = get_graph()
            query = "MATCH (ko:OfferLineKO)-[r]-(o:Offer) WHERE id(ko) = " + self.id + " DELETE ko,r RETURN id(o)"
            result = graph.cypher.execute(query)
            if len(result) != 0:
                offer_id = result[0].__getattribute__('id(o)')
                offer = Offer(str(offer_id))
                line_ok_number = offer.get_nb_line_ok()
                line_ko_number = offer.get_nb_line_ko()
                offer.set_lineok_lineko(line_ok_number, line_ko_number)
        except Exception as e:
            return Response(Response.ERROR_STATUS, traceback.format_exc())
        return Response(Response.SUCCESS_STATUS, Response.SUCCESS_MSG, len(result))
