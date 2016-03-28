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
        Ressource("Référence", "reference"),
        Ressource("Vin", "vin", "Wine", True, "Name"),
        Ressource("Appelation", "appelation", "Appelation", True, "Name"),
        Ressource("Classement", "classement"),
        Ressource("Couleur", "couleur", "Color", True, "Name"),
        Ressource("Millesime", "millesime", "Vintage", True, "Year"),
        Ressource("Prix", "prix", "", True),
        Ressource("Quantité", "quantite", "", True),
        Ressource("Format", "format", "", True),
        Ressource("Commentaire", "commentaire", "", True),
        Ressource("Conditionnement", "conditionnement", "", True),
        Ressource("Type de Conditionnement", "type_conditionnement", "PackageType", True, "Name"),
        Ressource("Régie", "regie", "", True),
        Ressource("Type", "type"),
        Ressource("Devise", "devise"),
        Ressource("Région", "region")
    ]

def match_col_title(first_line):
    ressource = {}
    ressource["reference"] = Ressource("Référence", "reference")
    ressource["vin"] = Ressource("Vin", "vin", "Wine", True, "Name")
    ressource["appellation"] = Ressource("Appelation", "appelation", "Appelation", True, "Name")
    ressource["classement"] = Ressource("Classement", "classement")
    ressource["couleur"] = Ressource("Couleur", "couleur", "Color", True, "Name")
    ressource["millesime"] = Ressource("Millesime", "millesime", "Vintage", True, "Year")
    ressource["prix"] = Ressource("Prix", "prix", "", True)
    ressource["quantite"] = Ressource("Quantité", "quantite", "", True)
    ressource["format"] = Ressource("Format", "format", "", True)
    ressource["commentaire"] = Ressource("Commentaire", "commentaire", "", True)
    ressource["conditionnement"] = Ressource("Conditionnement", "conditionnement", "", True)
    ressource["type de conditionnement"] = Ressource("Type de Conditionnement", "type_conditionnement", "PackageType", True, "Name")
    ressource["regie"] = Ressource("Régie", "regie", "", True)
    ressource["type"] = Ressource("Type", "type")
    ressource["devise"] = Ressource("Devise", "devise")
    ressource["region"] = Ressource("Région", "region")
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