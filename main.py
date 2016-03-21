# -*- coding:utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
from Models.import_class import readexcel
from werkzeug.wsgi import LimitedStream
from werkzeug import secure_filename


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
        return render_template('new_import.xml')

    @app.route('/cycom/import_xls', methods=['POST'])
    def import_xls():
            date_import = request.form['date-import']
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                xl = readexcel(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                sheetnames = xl.worksheets()
                for sheet in sheetnames:
                    print sheet
                    for row in xl.getiter(sheet):
                        print row
                        print date_import
                    else:
                        print 'else all check'
                return render_template('import_result.xml')

    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route('/cycom/import_result')
    def import_result():
        return render_template('import_result.xml')

if __name__ == '__main__':
    app.run(debug=True)