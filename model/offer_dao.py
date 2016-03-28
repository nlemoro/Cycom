import traceback
from ressourses.ressources import _logger
from model.offer import Offer
from services.queries import get_graph
from openerp import http

OFFERS_PER_PAGE = 10


def _get_offers_from_company(page, where):
    try:
        offers = []
        company = http.request.env['res.company'].search([])[0].name

        query = "MATCH (p:Partner)-[]-(o:Offer)-[r]-(c:Company) WHERE " + where + " AND lower(c.Name) = lower(\"" + company + "\") OPTIONAL MATCH (o)-[]-(f:Files) RETURN id(o) AS id, id(f) AS file_id ORDER BY o.DateOffer DESC SKIP " + str((page - 1) * OFFERS_PER_PAGE) + " LIMIT " + str(OFFERS_PER_PAGE)
        result = get_graph().cypher.execute(query)
        if len(result) != 0:
            for it in result:
                offers.append(Offer(str(it.id)))
        response = {'offers': offers, 'current_page': page}

        query = "MATCH (p:Partner)-[]-(o:Offer)-[r]-(c:Company) WHERE " + where + " AND lower(c.Name) = lower(\"" + company + "\") OPTIONAL MATCH (o)-[]-(f:Files) RETURN COUNT(o) AS count"
        count = get_graph().cypher.execute(query).one
        if count % OFFERS_PER_PAGE == 0:
            response['page_count'] = count / OFFERS_PER_PAGE
        else:
            response['page_count'] = count / OFFERS_PER_PAGE + 1
        return response
    except Exception as e:
        print traceback.format_exc()
        return


class OfferDAO:
    def __init__(self):
        pass

    @staticmethod
    def get_offers_from_partner(partner, filter=None):
        offers = []
        try:
            company = http.request.env['res.company'].search([])[0].name
            if filter is not None:
                filter = "AND o.IsActive = true AND o.IsSpot = false "
            else:
                filter = ""
            query = "MATCH (c:Company)-[]-(o:Offer)-[r]-(p:Partner) WHERE lower(c.Name) = lower(\"" + company + "\") AND lower(p.Name) = lower(\"" + partner + "\") "
            query += filter + "RETURN id(o)"
            result = get_graph().cypher.execute(query)
            if len(result) != 0:
                for it in result:
                    id = str(it.__getattribute__("id(o)"))
                    offers.append(Offer(id))
            return offers
        except Exception as e:
            _logger().error(traceback.format_exc())
            return offers

    @staticmethod
    def get_published_offers_from_company(page):
        return _get_offers_from_company(page, "o.IsActive = true AND o.IsToProcess = false AND o.IsNewPrice = false")

    @staticmethod
    def get_to_process_offers_from_company(page):
        return _get_offers_from_company(page, "o.IsToProcess = true AND o.IsNewPrice = false")

    @staticmethod
    def get_disabled_offers_from_company(page):
        return _get_offers_from_company(page, "o.IsActive = false AND o.IsToProcess = false AND o.IsNewPrice = false")

    @staticmethod
    def get_all_offers_from_company(page):
        return _get_offers_from_company(page, "1 = 1 AND o.IsNewPrice = false")

    @staticmethod
    def get_spot_offers_from_company(page):
        return _get_offers_from_company(page, "o.IsSpot = true AND o.IsNewPrice = false")

    @staticmethod
    def get_producer_offers_from_company(page):
        return _get_offers_from_company(page, "o.IsProducer = true AND o.IsNewPrice = false")

    @staticmethod
    def get_new_price_offers_from_company(page):
        return _get_offers_from_company(page, "o.IsNewPrice = true")