import traceback
from services.queries import get_graph
from openerp import http

class OfferLineDAO:

    def __init__(self):
        pass

    @staticmethod
    def check_best_price():
        offers = []
        try:
            company = http.request.env['res.company'].search([])[0].name
            query = "MATCH (c:Company)-[]-(o:Offer)-[r]-(p:Partner) WHERE lower(c.Name) = lower(\"" + company + "\") AND lower(p.Name) = lower(\"" + partner + "\") RETURN id(o)"
            result = get_graph().cypher.execute(query)
            if len(result) != 0:
                for it in result:
                    id = str(it.__getattribute__("id(o)"))
                    offers.append(Offer(id))
            return offers
        except Exception as e:
            print traceback.format_exc()
            return offers
