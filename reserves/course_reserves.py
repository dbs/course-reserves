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

app = Flask(__name__)
app.root_path = abspath(dirname(__file__))
babel = Babel(app)
login_manager = LoginManager()
login_manager.init_app(app)

c = ConfigFile('config.ini')
opt = c.getsection('Reserves')

parser = OptionParser()
parser.add_option('-d', '--debug', dest='DEBUG', action='store_true',
            help='Provides debug output when unhandled exceptions occur.')
parser.add_option('-v', '--verbose', dest='VERBOSE', action='store_true',
            help='Provides verbose output for what is being done.')
parser.add_option('-s', '--student', dest='STUDENT', action='store_true',
            help='Authenticates against the Student LDAP')
cmd_opt, all_opt = parser.parse_args()

opt['DEBUG']  = cmd_opt.DEBUG
opt['VERBOSE'] = cmd_opt.VERBOSE
opt['STUDENT'] = cmd_opt.STUDENT

# We import these here because they depend on opt[],
# which needs to resolve first.
import database
from user import User

@babel.localeselector
def select_locale():
    """
    Selects the locale. Babel uses this to
    determine which language to go with.
    """
    try:
        if opt['VERBOSE']:
            print(session['LANG'])
        return session['LANG']
    except Exception, ex:
        return opt['LANG']

@login_manager.user_loader
def load_user(id):
    return User.get_by_id(id)

@app.before_request
def pre_request():
    "Selects a user based on the session's UID"
    try:
        user = User.get_by_id(session['uid'])
        if not user:
            logout_user()
        else:
            current_user = user
    except Exception, ex:
        if opt['VERBOSE']:
            print('Exception occurred on user:')
            print(ex)

@app.errorhandler(401)
def forbidden_error(err):
    "Gives the user a login page."
    if opt['VERBOSE']:
        print('401 error:')
        print(err)
    return redirect(url_for('login_form')), 302

@app.errorhandler(404)
def not_found(err):
    "Gives a 404 page."
    if opt['VERBOSE']:
        print('404 error:')
        print(err)
    return render_template('404.html', opt=opt), 404

@app.errorhandler(500)
def server_problem(err):
    "Lets the user know that an error ocurred."
    if opt['VERBOSE']:
        print('500 error:')
        print(err)
    return render_template('500.html', opt=opt), 500

@app.route('/', methods=['GET', 'POST'])
@app.route('/view/', methods=['GET', 'POST'])
def view_reserves():
    "Our root page - show the list of reserves to the user."
    logout_user()
    return render_template('root.html',
            data=database.get_reserves(), opt=opt), 200

@app.route('/lang/<lang>/', methods=['GET', 'POST'])
def lang_switch(lang):
    "Switch languages in the session out of a list of supported ones."
    if lang in ['en', 'fr']:
        if opt['VERBOSE']:
            print('Language switched to: ' + lang)
        session['LANG'] = lang
    return redirect(url_for('view_reserves')), 302

@app.route('/login/', methods=['GET', 'POST'])
def login_form():
    """
    Gives the user a nice login form
    
    Afterwards, an LDAP server is queried to see if the credentials are valid.
    """
    if not current_user.is_authenticated():
        if request.method == 'POST':
            try:
                form = request.form
                user = User.try_login(opt['LDAP_HOST'],
                    form['username'], form['password'])
                session['uid'] = user.get_id()
                login_user(user)
                return redirect(url_for('admin')), 302
            except Exception, ex:
                if opt['VERBOSE']:
                    print('Login problem ocurred:')
                    print(ex)
                return render_template('login_fail.html', opt=opt), 200
        else:
            return render_template('login.html', opt=opt), 200
    else:
        return redirect(url_for('admin')), 302

@app.route('/admin/', methods=['GET', 'POST'])
@login_required
def admin():
    "Gives the administrator a page with forms to modify the database."
    return render_template('adminform.html',
        opt=opt, data=database.get_reserves()), 200

@app.route('/add/', methods=['POST'])
@login_required
def add_reserve():
    "Parses the form to add a reserve."
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
        return redirect(url_for('admin')), 302
    message = 'Form successfully submitted.'
    return redirect(url_for('admin')), 302

@app.route('/edit/', methods=['POST'])
@login_required
def edit_reserve():
    "Parses the form to edit a reserve."
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
        return redirect(url_for('admin')), 302
    message = 'Form successfully submitted.'
    return redirect(url_for('admin')), 302

@app.route('/delete/', methods=['POST'])
@login_required
def delete_reserve():
    "Parses the form to delete a reserve."
    try:
        form = request.form
        id = form['reserve_id']
        database.delete_reserve(id)
    except Exception, ex:
        print('Error occurred while parsing deletion: ')
        print(ex)
        message = 'Couldn\'t submit form.'
        return redirect(url_for('admin')), 302
    message = 'Form successfully submitted.'
    return redirect(url_for('admin')), 302

if opt['SECRET']:
    app.secret_key = opt['SECRET']
else:
    print('No secret key has been set. Aborting.')
    exit()

if opt['VERBOSE']:
    print('Using options:')
    print(opt)

if __name__ == '__main__':
    app.run(debug=opt['DEBUG'], host=opt['HOST'], port=opt['PORT'])
