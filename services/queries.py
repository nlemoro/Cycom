# coding=utf-8

import time
from py2neo import Graph, rewrite, authenticate
import unicodedata
from ressourses.ressources import get_graph_url
from ressourses.response import Response

BEST_PRICE_MIN_QTY = 12

def get_graph():
    if not hasattr(get_graph, "graph"):
        authenticate(get_graph_url(), "neo4j", "smartillac33")
        get_graph.graph = Graph("http://" + get_graph_url() + "/db/data")
    return get_graph.graph


def check_line_query(wine, color, appelation):
    wine = unicodedata.normalize('NFKD', wine.decode("utf-8")).encode('ASCII', 'ignore')
    appelation = unicodedata.normalize('NFKD', appelation.decode("utf-8")).encode('ASCII', 'ignore')
    color = unicodedata.normalize('NFKD', color.decode("utf-8")).encode('ASCII', 'ignore')
    query = "MATCH (W:Wine)-[:REL_HAS]-(C:Color)-[:REL_HAS]-(c:ColorSynonyme), (w:WineSynonyme)-[:REL_HAS]-(W)-[:REL_HAS]-(A:Appelation)-[:REL_HAS]-(a:AppelationSynonyme) WHERE "
    query += "lower(c.NameWithoutAccent)=\"" + color + "\" AND "
    query += "lower(w.NameWithoutAccent)=\"" + wine + "\" AND "
    query += "lower(a.NameWithoutAccent)=\"" + appelation + "\" "
    query += "RETURN W.Name,C.Name,A.Name"
    return query


def check_line_from_graph(wine, color, appelation):
    query = check_line_query(wine, color, appelation)
    result = get_graph().cypher.execute(query)
    result_length = len(result)
    if result_length == 0:
        if "ch." in wine:
            query = check_line_query(wine.replace("ch.", "château"), color, appelation)
            result = get_graph().cypher.execute(query)
            result_length = len(result)
    if result_length != 0:
        ret = {"vin": result[0].__getattribute__("W.Name"), "couleur": result[0].__getattribute__("C.Name"),
               "appelation": result[0].__getattribute__("A.Name")}
    else:
        ret = None
    return Response(Response.SUCCESS_STATUS, Response.SUCCESS_MSG, result_length, ret)


def create_wine_synonyme(wine, wine_synonyme, appelation, color):
    if wine_synonyme == "-":
        return []
    query = "MATCH (a:Appelation)-[:REL_HAS]-(w:Wine)-[:REL_HAS]-(c:Color) WHERE lower(w.Name) = lower(\"" + wine + "\") and "
    query += "lower(a.Name) = lower(\"" + appelation + "\")  and lower(c.Name) = lower(\"" + color + "\") "
    query += "MERGE (ws:WineSynonyme {Name: lower(\"" + wine_synonyme + "\"), NameWithoutAccent: \""
    query += unicodedata.normalize('NFKD', wine_synonyme).encode('ASCII', 'ignore') + "\"})-[:REL_HAS]->(w) RETURN w,ws"
    return get_graph().cypher.execute(query)


def create_line_ok(id_ko, id_offer, wine, color, appelation, vintage, quantity, price):
    graph = get_graph()
    query = "MATCH (w:Wine)-[:REL_HAS]-(c:Color), (w)-[r3:REL_HAS]-(a:Appelation), (ko:OfferLineKO), (o:Offer) "
    query += "WHERE id(ko) = " + id_ko + " and id(o) = " + id_offer + " and lower(w.Name) = lower(\"" + wine
    query += "\") and lower(c.Name) = lower(\"" + color + "\") and lower(a.Name) = lower(\"" + appelation + "\") "
    query += "SET o.LineOK = (o.LineOK + 1) SET o.LineKO = (o.LineKO - 1) SET ko.IsArchived = true "
    query += "CREATE (v:Vintage {Year: \"" + vintage + "\"})-[:REL_HAS]->(w) CREATE (ok:OfferLineOK {Quantity: \""
    query += quantity + "\", Price: \"" + price + "\", IsActive: true, LastUpdate: o.LastUpdate})-[:REL_HAS]->(v) CREATE (ok)-[:REL_HAS]->(o)"
    return graph.cypher.execute(query)


def create_appelation_synonyme(graph, wine, appelation_synonyme, appelation, color):
    if appelation_synonyme == "-":
        return []
    query = "MATCH (a:Appelation)-[:REL_HAS]-(w:Wine)-[:REL_HAS]-(c:Color) WHERE lower(w.Name) = lower(\"" + wine + "\") and "
    query += "lower(a.Name) = lower(\"" + appelation + "\")  and lower(c.Name) = lower(\"" + color + "\") "
    query += "MERGE (ws:AppelationSynonyme {Name: lower(\"" + appelation_synonyme + "\"), NameWithoutAccent: \""
    query += unicodedata.normalize('NFKD', appelation_synonyme).encode('ASCII', 'ignore') + "\"})-[:REL_HAS]->(a) RETURN a,ws"
    return graph.cypher.execute(query)


def create_color_synonyme(graph, wine, color_synonyme, appelation, color):
    if color_synonyme == "-":
        return []
    query = "MATCH (a:Appelation)-[:REL_HAS]-(w:Wine)-[:REL_HAS]-(c:Color) WHERE lower(w.Name) = lower(\"" + wine + "\") and "
    query += "lower(a.Name) = lower(\"" + appelation + "\")  and lower(c.Name) = lower(\"" + color + "\") "
    query += "MERGE (ws:ColorSynonyme {Name: lower(\"" + color_synonyme + "\"), NameWithoutAccent: \""
    query += unicodedata.normalize('NFKD', color_synonyme).encode('ASCII', 'ignore') + "\"})-[:REL_HAS]->(c) RETURN c,ws"
    return graph.cypher.execute(query)


def get_colors_synonymes():
    query = "MATCH (cs:ColorSynonyme)-[:REL_HAS]-(c:Color) return cs.Name, c.Name"
    rewrite(("http", "0.0.0.0", 7474), ("http", "52.48.147.125", 7474))
    result = get_graph().cypher.execute(query)
    ret = {}
    for it in result:
        ret[it.__getattribute__("cs.Name").encode("utf-8")] = it.__getattribute__("c.Name").encode("utf-8")
    return ret


def get_format_node_list():
    query = "MATCH (f:Format) return f.Name"
    rewrite(("http", "0.0.0.0", 7474), ("http", "52.48.147.125", 7474))
    result = get_graph().cypher.execute(query)
    ret = []
    for it in result:
        ret.append(it.__getattribute__("f.Name"))
    return ret


def is_wine_exist(wine):
    query = "MATCH (w:WineSynonyme) WHERE lower(w.Name) = lower(\"" + wine + "\") RETURN w"
    result = get_graph().cypher.execute(query)
    if len(result) == 0:
        return False
    return True


def is_package_type_exist(package_type):
    query = "MATCH (p:PackageType) WHERE lower(p.Name) = lower(\"" + package_type + "\") RETURN p"
    result = get_graph().cypher.execute(query)
    if len(result) == 0:
        return False
    return True


def publish_partner_generic_offer(offer_id):
    query = "MATCH (o:Offer)-[:REL_HAS]-(p:Partner) WHERE id(o) = \"" + offer_id + "\" AND o.IsSpot = false SET o.IsActive = true"
    return get_graph().cypher.execute(query)


def disable_partner_generic_offer(partner):
    query = "MATCH (o:Offer)-[:REL_HAS]-(p:Partner) WHERE p.Name = \"" + partner + "\" AND o.IsActive = true AND o.IsSpot = false SET o.IsActive = false"
    return get_graph().cypher.execute(query)


def check_best_price(wine, company):
    try:
        query = "MATCH (a:Appelation)-[]-(w:Wine)-[]-(c:Color), (w)-[]-(v:Vintage)-[]-(ok:OfferLineOK)-[]-(f:Format), (cp:Company)-[]-(o:Offer)-[]-(ok)-[]-(pt:PackageType) "
        query += "WHERE lower(cp.Name) = lower(\"" + company + "\") AND lower(a.Name) = lower(\"" + wine.appellation + "\") AND lower(w.Name) = lower(\"" + wine.name + "\") AND lower(c.Name) = lower(\"" + wine.color + "\") "
        query += "AND str(v.Year) = \"" + wine.vintage + "\" AND f.Name = \"" + wine.format +"\" AND pt.Name = \"" + wine.package_type + "\" AND ok.Package = \"" + wine.package + "\" AND ok.IsBestPrice = true "
        query += "SET ok.IsBestPrice = false, o.BestPrice = o.BestPrice - 1 RETURN ok"
        result = get_graph().cypher.execute(query)
        query = "MATCH (a:Appelation)-[]-(w:Wine)-[]-(c:Color), (w)-[]-(v:Vintage)-[]-(ok:OfferLineOK)-[]-(f:Format), (cp:Company)-[]-(o:Offer)-[]-(ok)-[]-(pt:PackageType) "
        query += "WHERE o.IsActive = true AND o.IsToProcess = false AND o.IsDeleting = false "
        query += "AND lower(cp.Name) = lower(\"" + company + "\") AND lower(a.Name) = lower(\"" + wine.appellation + "\") AND lower(w.Name) = lower(\"" + wine.name + "\") AND lower(c.Name) = lower(\"" + wine.color + "\") "
        query += "AND str(v.Year) = \"" + wine.vintage + "\" AND f.Name = \"" + wine.format + "\" AND pt.Name = \"" + wine.package_type + "\" AND ok.Package = \"" + wine.package + "\" AND ok.IsBestPrice = false "
        query += "AND toInt(ok.Quantity) >= \"" + str(BEST_PRICE_MIN_QTY) + "\" "
        query += "WITH ok, o ORDER BY toFloat(ok.Price) ASC LIMIT 1 SET ok.IsBestPrice = true, o.BestPrice = o.BestPrice + 1 RETURN id(ok) as id"
        result = get_graph().cypher.execute(query)
    except Exception as e:
        return e.message
