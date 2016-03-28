import json
import os
import traceback
from os.path import expanduser

from py2neo import *
from openerp import http
from model.wine import Wine
from ressourses.ressources import _logger
from services.queries import get_graph, check_best_price
from services.parsing_file import ParsingXls


class Offer:
    def __init__(self, param=None):
        try:
            if isinstance(param, basestring):
                self.id = param
            else:
                if 'partner' in param:
                    partner = json.loads(param["partner"])
                    self.partner = partner['name']
                    self.partner_odoo_id = partner['partner_id']
                if 'file_name' in param:
                    self.file_name = param['file_name']
                if 'offer_date' in param:
                    self.offer_date = param['offer_date']
                if 'is_new_price' in param:
                    if param['is_new_price'] == 'True':
                        self.is_new_price = True
                    else:
                        self.is_new_price = False
                if 'is_spot' in param:
                    if param['is_spot'] == 'True':
                        self.is_spot = True
                    else:
                        self.is_spot = False
                if 'spot_date' in param:
                    self.spot_date = param['spot_date']
                if 'is_producer' in param:
                    if param['is_producer'] == 'True':
                        self.is_producer = True
                    else:
                        self.is_producer = False
                company = http.request.env['res.company'].search([])[0].name
                if company is not None:
                    self.company = company
        except Exception as e:
            _logger().error(traceback.format_exc())

    def create(self):
        if not self.is_new_price:
            file_path = os.path.dirname(self.file_name)
            file_name = os.path.basename(self.file_name)
            file_ok = os.path.splitext(file_name)[0] + "-OK.csv"
            file_ko = os.path.splitext(file_name)[0] + "-KO.csv"
        query = "MATCH (soc:Company) WHERE lower(soc.Name) = lower(\"" + self.company + "\") MERGE (p:Partner {IdOdoo: \"" + str(
            self.partner_odoo_id) + "\"}) SET p.Name = \"" + self.partner + "\" "
        query += "CREATE (o:Offer { LineOK: 0, LineKO: 0, BestPrice: 0, DateOffer: \"" + self.offer_date + "\", LastUpdate: \"" + self.offer_date + "\", IsLoaded: false, IsActive: false, IsDeleting: false, "
        if self.is_spot:
            query += "IsSpot: true, IsToProcess: false," \
                     " EndSpotDate: \"" + self.spot_date + "\", "
        else:
            query += " IsSpot: false, IsToProcess: true, "
        if self.is_new_price:
            query += " IsNewPrice: true, "
        else:
            query += " IsNewPrice: false, "
        if self.is_producer:
            query += " IsProducer: true }) "
        else:
            query += " IsProducer: false }) "
        if not self.is_new_price:
            query += "CREATE (o)-[:REL_HAS]->(f:Files {Path: \"" + file_path + "\", Name: \"" + file_name + "\", NameOK: \"" + file_ok + "\", NameKO: \"" + file_ko + "\"})"
        query += "CREATE (o)-[:REL_HAS]->(p) CREATE (o)-[:REL_UPDATE_PARTNER]->(soc) RETURN id(o)"
        result = get_graph().cypher.execute(query)
        if result.__len__() != 0:
            self.id = result[0].__getattribute__("id(o)")
        else:
            self.id = -1
        if self.id is not str:
            self.id = str(self.id)
        return

    def loads(self):
        query = "MATCH (o:Offer)-[]-(p:Partner) "
        query += " WHERE id(o) = " + self.id + " OPTIONAL MATCH (o)-[]-(f:Files) RETURN o AS offer, f AS files, id(f) AS fileId, p AS partner"
        result = get_graph().cypher.execute(query)
        if result.__len__() != 0:
            self.partner = result[0].partner.properties["Name"]
            self.partner_odoo_id = result[0].partner.properties["IdOdoo"]
            self.line_ok = result[0].offer.properties["LineOK"]
            self.line_ko = result[0].offer.properties["LineKO"]
            self.best_price = result[0].offer.properties["BestPrice"]
            self.offer_date = result[0].offer.properties["DateOffer"]
            self.spot_date = result[0].offer.properties["EndSpotDate"]
            self.is_spot = result[0].offer.properties["IsSpot"]
            self.is_to_process = result[0].offer.properties["IsToProcess"]
            self.is_loaded = result[0].offer.properties["IsLoaded"]
            self.is_producer = result[0].offer.properties["IsProducer"]
            self.is_active = result[0].offer.properties["IsActive"]
            self.is_deleting = result[0].offer.properties["IsDeleting"]
            self.disable_date = result[0].offer.properties["DisableDate"]
            self.is_new_price = result[0].offer.properties["IsNewPrice"]
            if self.is_new_price == False:
                self.file_name = result[0].files.properties["Name"]
                self.file_path = result[0].files.properties["Path"]
                self.file_id = result[0].fileId
            else:
                self.file_name = "Aucun"
                self.file_path = ""
                self.file_id = ""
        else:
            _logger().error("Error: no Offer with an ID of " + self.id + " found.")

    def import_csv_ok(self, file_path):
        home = expanduser('~')
        file_path = "file://" + home + "/" + file_path
        query = "LOAD CSV WITH HEADERS FROM \"" + file_path + "\" AS csvLine FIELDTERMINATOR ';' "
        query += "MATCH (w:Wine)-[:REL_HAS]-(c:Color), (w)-[r3:REL_HAS]-(a:Appelation), (o:Offer), (f:Format), (pT:PackageType) "
        query += "WHERE lower(w.Name) = lower(csvLine.vin) and lower(c.Name) = lower(csvLine.couleur) and "
        query += "lower(a.Name) = lower(csvLine.appelation) and id(o) = " + str(self.id) + " "
        query += "AND f.Name = csvLine.format and lower(pT.Name) = lower(csvLine.type_conditionnement) "
        query += "MERGE (v:Vintage {Year: toInt(csvLine.millesime)})-[:REL_HAS]->(w) "
        query += "CREATE (ok:OfferLineOK {Quantity: csvLine.quantite, Price: csvLine.prix, IsBestPrice: false, IsActive: true, LastUpdate: \"" + self.offer_date + "\", Package: csvLine.conditionnement, Regie: csvLine.regie, Comment: csvLine.commentaire})-[:REL_HAS]->(v) "
        query += "CREATE (ok)-[:REL_HAS]->(f) CREATE (ok)-[:REL_HAS]->(pT) CREATE (ok)-[:REL_HAS]->(o)"
        return get_graph().cypher.execute(query)

    def export_xls_ok(self):
        try:
            company = http.request.env['res.company'].search([])[0].name
            query = "MATCH (part:Partner)-[]-(o:Offer)-[]-(ok:OfferLineOK)-[]-(v:Vintage)-[]-(w:Wine)-[]-(a:Appelation), "
            query += "(ok)-[]-(f:Format),(ok)-[]-(pt:PackageType),(w)-[]->(c:Color),(o)-[:REL_UPDATE_PARTNER]-(soc:Company), "
            query += "(o)-[]-(file:Files) "
            query += "WHERE soc.Name = \"" + company + "\" AND id(o) = " + self.id + " "
            query += "RETURN ok AS ok, v AS v, w AS w, a AS a, f AS f, pt AS pt, c AS c, file AS file"
            result = get_graph().cypher.execute(query)
            home = expanduser("~") + "/"
            file_name = os.path.basename(result[0].file.properties["Name"])
            file_name = os.path.splitext(file_name)[0] + "-LISTE-LIGNE-OK.xls"
            file_path = result[0].file.properties["Path"]
            file_path = file_path + "/" + file_name
            export_ok_file = open(home + file_path, "w")
            export_ok_obj = ParsingXls(export_ok_file)
            # PUSH COLUMN LABEL HERE
            export_ok_obj.append_line(["Vin", "Appellation", "Couleur", "Millesime", "Prix", "Quantite",
                                       "Format", "Conditionnement", "Regie"])
            for it in result:
                obj = []
                obj.append(it.w.properties["Name"])
                obj.append(it.a.properties["Name"])
                obj.append(it.c.properties["Name"])
                obj.append(str(int(it.v.properties["Year"])))
                obj.append(it.ok.properties["Price"].replace(".", ",", 1))
                obj.append(it.ok.properties["Quantity"])
                obj.append(it.f.properties["Name"])
                obj.append(it.pt.properties["Name"] + it.ok.properties["Package"])
                obj.append(it.ok.properties["Regie"])
                export_ok_obj.append_line(obj)
            export_ok_obj.book.save(export_ok_file)
            export_ok_file.close()
            return file_path
        except Exception as e:
            print traceback.format_exc()

    def import_csv_ko(self, file_path):
        home = expanduser('~')
        file_path = "file://" + home + "/" + file_path
        query = "LOAD CSV WITH HEADERS FROM \"" + file_path + "\" AS csvLine FIELDTERMINATOR ';' "
        query += "MATCH (o:Offer) WHERE id(o) = " + str(self.id) + " "
        query += "CREATE (ko:OfferLineKO {Quantity: csvLine.quantite, Format: csvLine.format, PackageType: csvLine.type_conditionnement, " \
                 "Vintage: csvLine.millesime, Wine: csvLine.vin, Price: csvLine.prix, Package: csvLine.conditionnement, " \
                 "Color: csvLine.couleur, Appelation: csvLine.appelation, IsArchived: false, Regie: csvLine.regie, Comment: csvLine.commentaire})-[:REL_HAS]->(o)"
        return get_graph().cypher.execute(query)

    def ko_to_ok_line(self, id_ko, offer_line):
        query = "MATCH (w:Wine)-[]-(c:Color), (w)-[]-(a:Appelation),(ko:OfferLineKO), (o:Offer), (f:Format), (pT:PackageType) "
        query += "WHERE id(o) = " + str(self.id) + " and lower(w.Name) = lower(\"" + offer_line.wine.name
        query += "\") and lower(c.Name) = lower(\"" + offer_line.wine.color + "\") and lower(a.Name) = lower(\"" + offer_line.wine.appellation + "\") "
        query += "AND f.Name = \"" + offer_line.wine.format + "\" AND lower(pT.Name) = lower(\"" + offer_line.wine.package_type + "\") AND id(ko) = " + id_ko
        query += " SET ko.IsArchived = true"
        query += " SET o.LineKO = (o.LineKO - 1)"
        self.add_line_ok(offer_line)
        return get_graph().cypher.execute(query)

    def add_line_ok(self, offer_line):
        query = "MATCH (w:Wine)-[:REL_HAS]-(c:Color), (w)-[r3:REL_HAS]-(a:Appelation), (o:Offer), (f:Format), (pT:PackageType) "
        query += "WHERE id(o) = " + str(self.id) + " and lower(w.Name) = lower(\"" + offer_line.wine.name
        query += "\") and lower(c.Name) = lower(\"" + offer_line.wine.color + "\") and lower(a.Name) = lower(\"" + offer_line.wine.appellation + "\") "
        query += "AND f.Name = \"" + offer_line.wine.format + "\" AND lower(pT.Name) = lower(\"" + offer_line.wine.package_type + "\") "
        query += " SET o.LineOK = (o.LineOK + 1) "
        query += "MERGE (v:Vintage {Year: " + offer_line.wine.vintage + "})-[:REL_HAS]->(w) CREATE (ok:OfferLineOK {Quantity: \"" + offer_line.quantity + "\""
        query += ", Price: \"" + offer_line.price + "\", IsBestPrice: false, IsActive: true, LastUpdate: o.LastUpdate, Package: \"" + offer_line.wine.package + "\", Regie: \"" + offer_line.regie + "\", Comment: \"" + offer_line.comment + "\"})-[:REL_HAS]->(v) "
        query += "CREATE (ok)-[:REL_HAS]->(f) CREATE (ok)-[:REL_HAS]->(pT) CREATE (ok)-[:REL_HAS]->(o)"
        return get_graph().cypher.execute(query)

    def set_lineok_lineko(self, line_ok, line_ko):
        query = "MATCH (o:Offer) WHERE id(o) = " + self.id + " SET o.LineOK = " + str(line_ok) + ", o.LineKO = " + str(
            line_ko) + " RETURN o"
        rewrite(("http", "0.0.0.0", 7474), ("http", "52.48.147.125", 7474))
        get_graph().cypher.execute(query)

    def set_is_loaded(self, boolean):
        query = "MATCH (o:Offer) where id(o) = " + self.id + " SET o.IsLoaded = " + str(boolean).lower() + " RETURN o"
        rewrite(("http", "0.0.0.0", 7474), ("http", "52.48.147.125", 7474))
        get_graph().cypher.execute(query)

    def remove(self):
        graph = get_graph()
        query = "MATCH (o:Offer) WHERE id(o)=" + self.id + " SET o.IsDeleting = true RETURN o"
        response = graph.cypher.execute(query)
        if len(response) == 0:
            return response
        self.update_best_price()
        # query = "MATCH (o:Offer)-[r:REL_HAS]-(ok:OfferLineOK)-[r1:REL_HAS]-(v:Vintage)-[r3]-(), "
        # query += "(bw:Company)-[r5]-(o)-[r6:REL_HAS]-(p:Partner), (o)-[r7]-(ko:OfferLineKO), (pt:PackageType)-[r8]-(ok)-[r9]-(form:Format) WHERE id(o) = " + self.id + " OPTIONAL MATCH (f:Files)-[r4:REL_HAS]-(o)"
        # query += " DELETE f,r4,o,r,ok,r1,v,r3,r5,r6,r7,ko,r8,r9"
        query = "MATCH (o:Offer)-[r]-() where id(o) = " + self.id + " delete o,r"
        # query = "MATCH (o:Offer)-[r]-(:Partner), (ko:OfferLineKO)-[r0]-(o)-[r1]-(ok:OfferLineOK)-[r2]-(), (:Company)-[r3]-(o)-[r4]-(f:Files) WHERE id(o) = " + 9989 + " DELETE o,r,ko,r0,r1,ok,r2,r3,r4,f"
        return graph.cypher.execute(query)

    def get_nb_line_ok(self):
        query = "MATCH (o:Offer)-[r]-(ok:OfferLineOK) WHERE id(o) = " + self.id + " RETURN COUNT(ok)"
        result = get_graph().cypher.execute(query)
        if len(result) != 0:
            return result[0].__getattribute__('COUNT(ok)')
        return 0

    def get_nb_line_ko(self):
        query = "MATCH (o:Offer)-[r]-(ko:OfferLineKO) WHERE id(o) = " + self.id + " AND ko.IsArchived = false RETURN COUNT(ko)"
        result = get_graph().cypher.execute(query)
        if len(result) != 0:
            return result[0].__getattribute__('COUNT(ko)')
        return 0

    def publish(self):
        query = "MATCH (o:Offer) WHERE id(o) = " + self.id + " SET o.IsToProcess = false, o.IsActive = true"
        return get_graph().cypher.execute(query)

    def get_partner(self):
        query = "MATCH (o:Offer)-[r]-(p:Partner) WHERE id(o) = " + self.id + " RETURN p.Name"
        result = get_graph().cypher.execute(query)
        if len(result) != 0:
            return result[0].__getattribute__("p.Name")
        return ""

    def set_is_active(self, is_active):
        if is_active is not str:
            is_active = str(is_active)
        query = "MATCH (o:Offer) WHERE id(o) = " + self.id + " SET o.IsActive = " + is_active + " RETURN o"
        result = get_graph().cypher.execute(query)
        return result

    def update_best_price(self):
        try:
            company = http.request.env['res.company'].search([])[0].name
            query = "MATCH (cp:Company)-[]-(o:Offer)-[]-(ok:OfferLineOK)-[]-(v:Vintage)-[]-(w:Wine)-[]-(c:Color), " \
                    "(w)-[]-(a:Appelation), (f:Format)-[]-(ok)-[]-(pt:PackageType) WHERE id(o) = " \
                    "" + self.id + " AND lower(cp.Name) = lower(\"" + company + "\") " \
                                                                                "RETURN w.Name AS name, a.Name AS appellation, c.Name AS color, v.Year AS vintage, " \
                                                                                "f.Name AS format, pt.Name AS package_type, ok.Package AS package"
            result = get_graph().cypher.execute(query)
            for it in result:
                wine = Wine(it.__dict__)
                check_best_price(wine, company)
        except Exception:
            _logger().error(traceback.format_exc())
