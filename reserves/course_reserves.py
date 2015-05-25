#!/usr/bin/env python

from flask import Flask, abort, request, redirect, url_for, \
                    render_template, make_response, g, session
from flask_login import LoginManager, login_required, current_user, \
                    login_user, logout_user
from flask_babelex import Babel
from os.path import abspath, dirname
from optparse import OptionParser
from conf import ConfigFile
import sys
import ldap
import psycopg2
import StringIO
import database

app = Flask(__name__)
app.root_path = abspath(dirname(__file__))
babel = Babel(app)

c = ConfigFile('config.ini')
opt = {}
opt = c.getsection('Reserves')

parser = OptionParser()
parser.add_option('-d', '--debug', dest='DEBUG', action='store_true',
            help='Provides debug output when unhandled exceptions occur.')
parser.add_option('-v', '--verbose', dest='VERBOSE', action='store_true',
            help='Provides verbose output for what is being done.')
cmd_opt, junk = parser.parse_args()

opt['DEBUG']  = cmd_opt.DEBUG
opt['VERBOSE'] = cmd_opt.VERBOSE

if opt['VERBOSE']:
    print('Using options:')
    print(opt)

@babel.localeselector
def select_locale():
    "Selects the locale. Babel uses this to determine which language to go with."
    try:
        if opt['VERBOSE']:
            print(session['LANG'])
        return session['LANG']
    except Exception, ex:
        return opt['LANG']

@app.route(opt['APP_ROOT'], methods=['GET', 'POST'])
@app.route(opt['APP_ROOT']+'view/', methods=['GET', 'POST'])
def view_reserves():
    return render_template('root.html',
            data=database.get_reserves(), opt=opt), 200

@app.route(opt['APP_ROOT']+'lang/<lang>/', methods=['GET', 'POST'])
def lang_switch(lang):
    if lang in ['en', 'fr']:
        if opt['VERBOSE']:
            print('Language switched to: ' + lang)
        session['LANG'] = lang
        return render_template('root.html', opt=opt, data=database.get_reserves()), 200

@app.route(opt['APP_ROOT']+'admin/', methods=['GET', 'POST'])
def admin():
    return render_template('adminform.html', opt=opt), 200

@app.route(opt['APP_ROOT']+'add/', methods=['POST'])
def add_reserve():
    try:
        form = request.form
        code = form['course_code']
        instructor = form['instructor']
        bookbag = form['bookbag_id']
        database.add_reserve(code, instructor, bookbag)
    except Exception, ex:
        print('Error occurred while parsing addition: ')
        print(ex)
        message = 'Couldn\'t submit form.'
        return render_template('adminform.html', opt=opt, message=message), 200
    message = 'Form successfully submitted.'
    return render_template('adminform.html', opt=opt, message=message), 200

@app.route(opt['APP_ROOT']+'edit/', methods=['POST'])
def edit_reserve():
    try:
        form = request.form
        id = form['reserve_id']
        code = form['course_code']
        instructor = form['instructor']
        bookbag = form['bookbag_id']
        database.edit_reserve(id, code, instructor, bookbag)
    except Exception, ex:
        print('Error occurred while parsing edit: ')
        print(ex)
        message = 'Couldn\'t submit form.'
        return render_template('admin', opt=opt, message=message), 200
    message = 'Form successfully submitted.'
    return render_template('admin', opt=opt, message=message), 200

@app.route(opt['APP_ROOT']+'delete/', methods=['POST'])
def delete_reserve():
    try:
        form = request.form
        id = form['reserve_id']
        database.delete_reserve(id)
    except Exception, ex:
        print('Error occurred while parsing deletion: ')
        print(ex)
        message = 'Couldn\'t submit form.'
        return render_template('adminform.html', opt=opt, message=message), 200
    message = 'Form successfully submitted.'
    return render_template('adminform.html', opt=opt, message=message), 200
    
app.secret_key = opt['SECRET']

if __name__ == '__main__':
    app.run(debug=opt['DEBUG'], host=opt['HOST'], port=opt['PORT'])
