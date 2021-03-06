# -*- coding:utf-8 -*-
import json
from os.path import expanduser
import sys
import traceback
import re

from flask import Flask, render_template, request, redirect, send_from_directory
import os
from werkzeug.wsgi import LimitedStream
from werkzeug import secure_filename
from services.parsing_file import ParsingFile
from ressourses.ressources import match_col_title, get_col_list
from ressourses.response import Response
from pattern.patterns import PatternList
from model.offer_dao import OfferDAO
from model.offer import Offer
from py2neo import GraphError
from services.queries import *
from services.parsing import parse_regie

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


class StreamConsumingMiddleware(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        stream = LimitedStream(environ['wsgi.input'],
                               int(environ['CONTENT_LENGTH'] or 0))
        environ['wsgi.input'] = stream
        app_iter = self.app(environ, start_response)
        try:
            stream.exhaust()
            for event in app_iter:
                yield event
        finally:
            if hasattr(app_iter, 'close'):
                app_iter.close()

app = Flask(__name__)
app.wsgi_app = StreamConsumingMiddleware(app.wsgi_app)

app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = set(['xls', 'xlsx', 'csv'])


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


class Controller(object):

    @app.route('/cycom/offer_list')
    def offer_list():
        return render_template('offer_list.html')

    @app.route('/cycom/load-offer-list-tab/')
    def load_disabled_offers_tab(self, **post):
        if 'page' not in post or 'tab_name' not in post:
            response = Response(Response.ERROR_STATUS, 'Missing page argument')
        # generate the function name wich is be called next based on the post value 'tab_name'
        offers = getattr(OfferDAO, 'get_' + post['tab_name'] + '_offers_from_company')(int(post['page']))
        tab_content = []
        for offer in offers['offers']:
            offer.loads()
            tab_content.append(offer.__dict__)
        response = {'page_count': offers['page_count'], 'current_page': offers['current_page'], 'offers': tab_content}
        return json.dumps(response)

    @app.route('/cycom/offer-loaded')
    def check_offer_status(self, **post):
        if 'offer_id' in post.keys():
            offer_id = post['offer_id']
        else:
            return str(Response(Response.ERROR_STATUS, "invalid argument list"))
        try:
            query = "MATCH (o:Offer) where id(o) = " + offer_id + " RETURN o"
            graph = get_graph()
            result = graph.cypher.execute(query)
            if len(result) == 0:
                return str(Response(Response.ERROR_STATUS, "invalid argument list"))
            isLoaded = result[0]
            return str(Response(Response.SUCCESS_STATUS, Response.SUCCESS_MSG, 1,
                                {"offer": json.dumps(isLoaded.o.properties), "offerId": offer_id}))
        except GraphError as e:
            return str(Response(Response.ERROR_STATUS, traceback.format_exc()))

    @app.route('/cycom/offer-status/')
    def import_set_status(self, table={}):
        table = json.loads(table)
        if "offer_id" not in table and "offer_status" not in table:
            return str(Response(Response.ERROR_STATUS, "Invalid argument"))
        try:
            offer_id = table["offer_id"]
            offer = Offer(offer_id)
            offer.set_is_active(table["offer_status"])
            offer.update_best_price()
            response = Response(Response.SUCCESS_STATUS, "OK")
        except GraphError as e:
            response = Response(Response.ERROR_STATUS, traceback.format_exc())
        return str(response)

    @app.route('/cycom/publish-offer/<string:offer_id>')
    def publish_offer(self, offer_id=None):
        if offer_id is None:
            return str(Response(Response.ERROR_STATUS, "invalid argument"))
        try:
            offer = Offer(offer_id)
            offers_to_disable = OfferDAO.get_offers_from_partner(offer.get_partner())
            for it in offers_to_disable:
                it.set_is_active(False)
                it.update_best_price()
            response = offer.publish()
            offer.update_best_price()
        except Exception:
            response = Response(Response.ERROR_STATUS, traceback.format_exc())
        return str(response)

    @app.route('/cycom/remove-offer/<string:offer_id>')
    def remove_offer(self, offer_id=None):
        if offer_id is None:
            return str(Response(Response.ERROR_STATUS, "Invalid argument"))
        try:
            offer = Offer(offer_id)
            response = offer.remove()
        except GraphError as e:
            response = Response(Response.ERROR_STATUS, traceback.format_exc())
        return str(response)

    @app.route('/cycom/update-line-ok-ko/<string:offer_id>')
    def update_line_ok_ko(self, offer_id=None):
        try:
            offer = Offer(offer_id)
            offer.set_lineok_lineko(offer.get_nb_line_ok(), offer.get_nb_line_ko())
            return str(Response(Response.SUCCESS_STATUS, Response.SUCCESS_MSG))
        except Exception:
            return str(Response(Response.ERROR_STATUS, traceback.format_exc()))

    @app.route('/cycom/offers-from-partner/<string:partner>')
    def offers_from_partner(self, partner=None):
        if partner is None:
            return str(Response(Response.ERROR_STATUS, "Invalid argument"))
        try:
            offers = OfferDAO.get_offers_from_partner(partner, True)
            for i in range(0, len(offers)):
                offers[i].loads()
                offers[i] = offers[i].__dict__
            return str(Response(Response.SUCCESS_STATUS, Response.SUCCESS_MSG, len(offers), offers))
        except Exception:
            return str(Response(Response.ERROR_STATUS, traceback.format_exc()))

    @app.route('/cycom/validation/')
    def bw_import_validation(**post):
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

    @app.route('/cycom/new_import')
    def new_import():
        return render_template('new_import.html')

    @app.route('/cycom/test_recup_wds', methods=['POST'])
    def test_recup_wds():
            date_import = request.form['date_import']
            if 'file' in request.files:
                file = request.files['file']
                filename = secure_filename(file.filename)
            else:
                print 'else all check'
                return redirect('/cycom/new_import')
            if not file or file is None:
                print 'not file'
                return redirect('/cycom/new_import')

            parsingFile = ParsingFile(file)
            if len(parsingFile) == 0:
                file.close()
                print 'len == 0'
                return redirect('/cycom/new_import')
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            worksheet = []

            i = 0
            matched_cols_list = None
            for item in parsingFile:
                if i == 0:
                    matched_cols_list = match_col_title(item)
                if i < 11:
                    worksheet.append(item)
                i += 1
            file.close()
            default_cols_list = get_col_list()
            patterns = [PatternList("format", ["xxxml", "xxcl", "x.xL"])]
            print default_cols_list
            return render_template('import_result.html', worksheet = worksheet,
                                                        default_cols_list = default_cols_list,
                                                        matched_cols_list = matched_cols_list,
                                                        patterns = patterns,
                                                        date_import = date_import, item = item, nbr_col = len(worksheet))

    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)