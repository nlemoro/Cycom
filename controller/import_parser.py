import json
import os
from os.path import expanduser
import sys
import traceback
import re

from werkzeug.utils import redirect
from py2neo import GraphError

from model.format import Format
from services.parsing import parse_regie
from model.offer import Offer
from services.queries import *
from ressourses.ressources import *
from ressourses.response import Response
from pattern.patterns import Pattern
from services.parsing_file import ParsingFile, ParsingCsv


class BigwineParser(object):
    @app.route('/cycom/validation/')
    def bw_import_validation(self, **post):
        try:
            if 'file_name' in post:
                column_list = json.loads(post['table'])
                file_name = post['file_name']
                offer = Offer(post)
            else:
                # TODO handle error page
                return "ERROR"
        except (ValueError, KeyError, TypeError) as e:
            # TODO handle error page
            sys.stderr.write(traceback.format_exc())
            return traceback.format_exc()
        try:
            home = expanduser("~") + "/"
            file = open(home + file_name, "rb")
            file_name = os.path.splitext(file_name)[0]
            line_ko_file = open(home + file_name + "-KO.csv", "w")
            line_ok_file = open(home + file_name + "-OK.csv", "w")
            line_ko = ParsingCsv(line_ko_file)
            line_ok = ParsingCsv(line_ok_file)
            parsing_file = ParsingFile(file)
            if len(parsing_file) == 0:
                return redirect('/cycom/new_import')

            res = get_col_list()
            column_to_check = get_col_to_check()
            nb_line_ok = 0
            nb_line_ko = 0
            offer.create()

            # init de la liste des colonnes qui sera integres dans les csv
            final_column_list = []
            i = 0
            for v in column_list:
                for it in res:
                    if it.name == v.encode("utf-8"):
                        final_column_list.append(it.csv_col.encode("utf-8"))
                        column_list[i] = it.csv_col.encode("utf-8")
                i += 1
            for it in res:
                if it.to_check:
                    if it.csv_col not in final_column_list:
                        final_column_list.append(it.csv_col)
                        column_list.append(it.csv_col)
            line_ok.append_line(final_column_list)
            line_ko.append_line(final_column_list)

            # Boucle principale de parsing, parcours chaque ligne du fichier d'origine et check chaque ligne
            parsing_file = parsing_file[:1]
            for item in parsing_file:
                i = 0
                new_line = []
                table = self.init_table_columns(column_list, column_to_check)
                empty = False
                for column in column_list:
                    if column != "":
                        value = "-"
                        if i < len(item):
                            it = item[i]
                            if type(it) is unicode:
                                # this delete every useless spaces (end begin and between words
                                it = re.sub(r"\s+", " ", it.encode("utf-8")).strip().lower()
                            it = it.replace('"', "'")
                            it = it.strip().lower()
                            it = self.bw_init_value(it, column_list[i])
                            if column in column_to_check:
                                table[column.lower()] = it
                            value = it
                            if column == 'Vin' and it == "-":
                                empty = True
                        else:
                            tmp = column.lower()
                            if tmp != "" and tmp in table and table[tmp] != "":
                                value = table[tmp]
                        new_line.append(value)
                    i += 1

                if not empty:
                    table_tmp = self.bw_apply_pattern(table, format_pattern)
                    if table_tmp != table:
                        for k, v in table_tmp.iteritems():
                            for i in range(0, len(final_column_list)):
                                if final_column_list[i] == k:
                                    new_line[i] = v
                    response = self.bw_check_line(table_tmp)
                    if response.status == Response.ERROR_STATUS:
                        print traceback.format_exc()
                        return traceback.format_exc()
                    elif response.status == Response.SUCCESS_STATUS and response.size == 0:
                        line_ko.append_line(new_line)
                        nb_line_ko += 1
                    else:
                        content = response.content
                        for k, v in content.iteritems():
                            for i in range(0, len(final_column_list)):
                                if final_column_list[i] == k:
                                    new_line[i] = v
                        line_ok.append_line(new_line)
                        nb_line_ok += 1

            file.close()
            line_ok_file.close()
            line_ko_file.close()
            offer.set_lineok_lineko(nb_line_ok, nb_line_ko)
            if nb_line_ok != 0:
                offer.import_csv_ok(file_name + "-OK.csv")
            if nb_line_ko != 0:
                offer.import_csv_ko(file_name + "-KO.csv")
            offer.set_is_loaded(True)
        except (IOError, GraphError) as e:
            sys.stderr.write(traceback.format_exc())
            offer.remove()
            return traceback.format_exc()
        return redirect('/cycom/offer-list')

    def bw_check_line(self, table):
        if not table:
            return Response(Response.SUCCESS_STATUS, "invalid argument list")

        if "vin" in table and "appelation" in table and "couleur" in table:
            wine = table['vin']
            color = table['couleur']
            appelation = table['appelation']
        else:
            return Response(Response.SUCCESS_STATUS, "invalid argument list")
        format = Format(table["format"])
        if not format.exist():
            return Response(Response.SUCCESS_STATUS, "invalid format", 0)
        try:
            result = check_line_from_graph(wine, color, appelation)
        except GraphError as e:
            print traceback.format_exc()
            return Response(Response.ERROR_STATUS, traceback.format_exc())
        return result

    def bw_apply_pattern(self, table, format_pattern):
        cpy = table.copy()
        data = {}
        if 'vin' in table:
            pattern = Pattern("wine", table['vin'])
            data = pattern.data
        if 'appelation' in table:
            pattern = Pattern("appelation", table['appelation'])
            data.update(pattern.data)
        if 'quantite' in table:
            pattern = Pattern("quantity", table['quantite'])
            data.update(pattern.data)
        if 'format' in table:
            pattern = Pattern(format_pattern, table["format"])
            data.update(pattern.data)
        if "type_conditionnement" in table:
            pattern = Pattern("package", table["type_conditionnement"].strip())
            data.update(pattern.data)
        if "conditionnement" in table:
            pattern = Pattern("package", table["conditionnement"].strip())
            if "type_conditionnement" in data and "type_conditionnement" in pattern.data:
                pattern.data.pop("type_conditionnement")
            if "conditionnement" in data and "conditionnement" in pattern.data:
                pattern.data.pop("conditionnement")
            data.update(pattern.data)
        if 'regie' in table:
            if "regie" not in data:
                data['regie'] = parse_regie(table['regie'])
        cpy.update(data)
        return cpy

    def bw_init_value(self, item, key):
        key = key.lower()
        if key == "couleur" and item == "":
            item = "rouge"
            #item = "-"
        elif key == "format" and item == "":
            item = "-"
        elif key == "conditionnement" and item == "":
            #item = "12"
            item = "-"
        elif key == "type_conditionnement" and item == "":
            #item = "CBO"
            item = "-"
        elif key == "regie" and item == "":
            item = "-"
        elif item == "":
            item = "-"
        return item

    def init_table_columns(self, column_list, column_to_check):
        table = {}
        for it in column_list:
            if it in column_to_check:
                table[it.lower()] = self.bw_init_value("", it.lower())
        return table
