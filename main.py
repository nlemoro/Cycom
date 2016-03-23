# -*- coding:utf-8 -*-
import json

from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
from Models.import_class import readexcel
from werkzeug.wsgi import LimitedStream
from werkzeug import secure_filename
from services.parsing_file import ParsingFile
from ressourses.ressources import match_col_title, get_col_list


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
            print matched_cols_list
            print default_cols_list
            return render_template('import_result.html', worksheet = worksheet,
                                                        default_cols_list = default_cols_list,
                                                        matched_cols_list = matched_cols_list,
                                                        date_import = date_import, item = item, nbr_col = len(worksheet))

    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route('/cycom/import_result')
    def validation(self):
        return render_template('import_result.html')

if __name__ == '__main__':
    app.run(debug=True)