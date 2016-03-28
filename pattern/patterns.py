from model.synonyme.synonyme_dao import SynonymeDAO
from model.package_dao import PackageDAO
from model.format import Format

import re

from services.queries import *
from model.format_dao import *


class Pattern:
    def __init__(self, pattern, to_convert):
        self.methods_map = {
            "xxcl": self.xxcl_pattern,
            "xxxml": self.xxxml_pattern,
            "x.xL": self.xL_pattern,
            "format?": self.format_default_pattern,
            "wine": self.wine_pattern,
            "appelation": self.appelation_pattern,
            "package": self.package_pattern,
            "quantity": self.quantity_pattern
        }
        self.data = {}
        self.format_pattern(pattern, to_convert)

    def xxcl_pattern(self, to_convert):
        self.data = convert_format(to_convert, 10)
        return self.data

    def xxxml_pattern(self, to_convert):
        self.data = convert_format(to_convert, 1)
        return self.data

    def xL_pattern(self, to_convert):
        self.data = convert_format(to_convert, 1000)
        return self.data

    def format_default_pattern(self, to_convert):
        self.data = convert_format(to_convert, 1)
        return self.data

    def wine_pattern(self, to_convert):
        to_convert = " " + to_convert.lower() + " "

        vintage = re.findall(r"\d{4}", to_convert)
        if len(vintage) != 0:
            to_convert = to_convert.replace(vintage[0], "")
            self.data = {"vin": to_convert.strip(), "millesime": vintage[0]}
        if is_wine_exist(to_convert.strip()):
            return self.data
        colors = get_colors()
        for it in colors.keys():
            if type(to_convert) is unicode:
                to_convert = to_convert.encode("utf-8")
            if " " + it.lower() + " " in to_convert:
                to_convert = to_convert.replace(it.lower() + " ", "").strip()
                self.data.update({"vin": to_convert, "couleur": colors[it].lower()})
        if "vin" in self.data:
            self.data["vin"] = re.sub(r"\s+", " ", self.data["vin"])
        return self.data

    def appelation_pattern(self, to_convert):
        to_convert = " " + to_convert.lower() + " "
        if type(to_convert) is unicode:
            to_convert = to_convert.encode("utf-8")
        to_convert = to_convert.replace(" aop ", " ")
        to_convert = to_convert.replace(" aoc ", " ")
        self.data.update({"appelation": to_convert.strip()})
        colors = get_colors()
        for it in colors.keys():
            if " " + it.lower() + " " in to_convert:
                to_convert = to_convert.replace(it.lower() + " ", "").strip()
                self.data.update({"appelation": to_convert, "couleur": colors[it].lower()})
        return self.data

    def package_pattern(self, to_convert):
        try:
            tab = PackageDAO.get_package_list()
            to_convert = to_convert.lower()
            data = {}
            if "unit" in to_convert:
                to_convert = to_convert.replace("unit", "1").strip()
            elif "unit." in to_convert:
                to_convert = to_convert.replace("unit.", "1").strip()
            if "acq" in to_convert:
                self.data.update({"regie": "ACQ"})
            elif "crd" in to_convert:
                self.data.update({"regie": "CRD"})
            package = re.findall(r"\d+", to_convert)
            if len(package) != 0:
                to_convert = to_convert.replace(package[0], "").strip()
                to_convert = re.sub(r"\s+", " ", to_convert)
                #if to_convert != "-" and to_convert != "":
                #    data_tmp = convert_format(to_convert, 1)
                #    if data_tmp["format"] != "-":
                #        self.data.update(data_tmp)
                for it in package:
                    to_convert = to_convert.replace(it, "").strip()
                data.update({"conditionnement": package[0]})
            for it in tab:
                if it.type.lower() in to_convert:
                    data.update({"type_conditionnement": it.type})
                    self.data.update(data)
                    return self.data
            if len(to_convert.strip()) != 0:
                self.data.update({"type_conditionnement": "-"})
            return self.data
        except Exception:
            print traceback.format_exc()

    def format_pattern(self, pattern, to_convert):
        for k, v in self.methods_map.iteritems():
            if k == pattern:
                v(to_convert)

    def quantity_pattern(self, to_convert):
        regex = re.compile('[^0-9]')
        to_convert = regex.sub('', to_convert)
        self.data.update({"quantite": to_convert})
        return self.data


class PatternList:
    def __init__(self, name, pattern_list):
        self.name = name
        self.pattern_list = pattern_list


def get_colors():
    if not hasattr(get_colors, "colors"):
        get_colors.colors = get_colors_synonymes()
    return get_colors.colors


def get_format_list():
    if not hasattr(get_format_list, "format"):
        get_format_list.colors = get_format_node_list()
    return get_format_list.colors


def convert_format(to_convert, coef):
    try:
        if to_convert == "-":
            return {"format": "750"}
        format_list = SynonymeDAO.get_list_full("Format")
        _format = None
        for it in format_list:
            if it.synonyme["Name"] in to_convert:
                if _format is None or (len(_format.name) < len(it.linked_node["Name"])):
                    _format = Format(it.linked_node["Name"])
        if _format is None:
            ret = re.findall(r"\d*[\.,]?\d+\s?.?l", to_convert)
            if len(ret) > 0:
                unit = re.findall(r"[^\s0-9]?l", ret[0])
                if unit[0] == "l":
                    coef = 1000
                elif unit[0] == "ml":
                    coef = 1
                elif unit[0] == "cl":
                    coef = 10
            to_convert = re.findall(r"[-+]?\d*\.\d+|\d+", to_convert.replace(",", "."))[0]
            to_convert = float(to_convert.strip())
            to_convert *= coef
            to_convert = '{:g}'.format(to_convert)
            _format = FormatDAO.get_format_from_synonyme(to_convert)
            if _format is None:
                _format = Format('-')
        data = {"format": _format.name}
    except (ValueError, IndexError):
        data = {"format": "-"}
    return data
