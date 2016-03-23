# coding=utf-8
import unicodedata
import logging


def remove_accents(input_str):
    if isinstance(input_str, unicode):
        nfkd_form = unicodedata.normalize('NFKD', input_str)
        return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
    else:
        return input_str


def get_graph_url():
    return "localhost:7474"


def _logger():
    if not hasattr(_logger, "logger"):
        _logger.logger = logging.getLogger(__name__)
    return _logger.logger


class Ressource:
    def __init__(self, name, csv_col, node_name="", to_check=False, field=""):
        self.name = name
        self.node_name = node_name
        self.to_check = to_check
        self.field = field
        self.csv_col = csv_col


def get_col_list():
    return [
        Ressource("id", "id", "Produit", True, "SKU"),
        Ressource("title", "title", "Produit", True, "Titre"),
        Ressource("brand", "brand", "Marque", True, "Nom"),
        Ressource("url", "producturl", "Product", True, "url"),
        Ressource("Non reconnu", "inconnu")
    ]

def match_col_title(first_line):
    ressource = {}
    ressource["id"] = Ressource("id", "id", "Produit", True, "SKU")
    ressource["title"] = Ressource("title", "title", "Produit", True, "Titre")
    ressource["brand"] = Ressource("brand", "brand", "Marque", True, "Nom")
    ressource["url"] = Ressource("url", "producturl", "Product", True, "url"),
    ressource["inconnu"] = Ressource("Non reconnu", "inconnu")

    col_list_matched = []
    for col_title in first_line:
        clean_title = remove_accents(col_title).lower()
        if clean_title in ressource.keys():
            col_list_matched.append(ressource[clean_title])
        else:
            col_list_matched.append(ressource["inconnu"])
    return col_list_matched


def get_col_to_check():
    res = get_col_list()
    column_to_check = []
    for it in res:
        if it.to_check:
            column_to_check.append(it.csv_col)
    return column_to_check