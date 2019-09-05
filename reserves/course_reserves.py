#!/usr/bin/env python
# -*- coding: utf-8 -*-

import flask
import flask_login
from flask_babelex import Babel, _
from os.path import abspath, dirname
import optparse
import conf
import sys
import ldap
import psycopg2
import traceback

class LocalCGIRootFix(object):
    """Wrap the application in this middleware if you are using FastCGI or CGI
    and you have problems with your app root being set to the cgi script's path
    instead of the path users are going to visit
    .. versionchanged:: 0.9
       Added `app_root` parameter and renamed from `LighttpdCGIRootFix`.
    :param app: the WSGI application
    :param app_root: Defaulting to ``'/'``, you can set this to something else
        if your app is mounted somewhere else.

    Clone of workzeug.contrib.fixers.CGIRootFix, but doesn't strip leading '/'
    """

    def __init__(self, app, app_root='/'):
        self.app = app
        self.app_root = app_root

    def __call__(self, environ, start_response):
        # only set PATH_INFO for older versions of Lighty or if no
        # server software is provided.  That's because the test was
        # added in newer Werkzeug versions and we don't want to break
        # people's code if they are using this fixer in a test that
        # does not set the SERVER_SOFTWARE key.
        if 'SERVER_SOFTWARE' not in environ or \
           environ['SERVER_SOFTWARE'] < 'lighttpd/1.4.28':
            environ['PATH_INFO'] = environ.get('SCRIPT_NAME', '') + \
                environ.get('PATH_INFO', '')
        environ['SCRIPT_NAME'] = self.app_root.rstrip('/')
        return self.app(environ, start_response)

app = flask.Flask(__name__, static_url_path='/static', static_folder='static')
app.root_path = abspath(dirname(__file__))

c = conf.ConfigFile(app.root_path + '/config.ini')
opt = c.getsection('Reserves')

parser = optparse.OptionParser()
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

if opt['SECRET']:
    app.secret_key = opt['SECRET']
else:
    print('No secret key has been set. Aborting.')
    exit()

if opt['VERBOSE']:
    print('Using options:')
    print(opt)

app.wsgi_app = LocalCGIRootFix(app.wsgi_app, app_root=opt['APP_ROOT'])
babel = Babel(app)
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

# We import these here because they depend on opt[],
# which needs to resolve first.
import database
from user import User

@app.before_request
def pre_request():
    if flask.request.view_args and 'lang' in flask.request.view_args:
        lang = flask.request.view_args['lang']
        if lang in ['en', 'fr']:
            flask.g.current_lang = lang
            flask.request.view_args.pop('lang')
        else:
            return flask.abort(404)

@babel.localeselector
def select_locale():
    """
    Selects the locale. Babel uses this to
    determine which language to go with.
    """
    return flask.g.get('current_lang', 'en')

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
    return flask.redirect(flask.url_for('login_form', lang=_('en'))), 302

@app.errorhandler(404)
def not_found(err):
    "Gives a 404 page."
    if opt['VERBOSE']:
        print('404 error:')
        print(err)
    return flask.render_template('404.html', opt=opt), 404

@app.errorhandler(500)
def server_problem(err):
    "Lets the user know that an error ocurred."
    if opt['VERBOSE']:
        print('500 error:')
        print(err)
    return flask.render_template('500.html', opt=opt), 500

@app.route('/<lang>/', methods=['GET', 'POST'])
@app.route('/<lang>/view/', methods=['GET', 'POST'])
def view_reserves():
    "Our root page - show the list of reserves to the user."
    flask_login.logout_user()
    return flask.render_template('root.html',
            data=database.get_reserves(), opt=opt), 200

@app.route('/<lang>/login/', methods=['GET', 'POST'])
def login_form():
    """
    Gives the user a nice login form
    
    Afterwards, an LDAP server is queried to see if the credentials are valid.
    """
    try:
        if not flask_login.current_user.is_authenticated:
            if flask.request.method == 'POST':
                try:
                    form = flask.request.form
                    user = User.try_login(opt['LDAP_HOST'],
                        form['username'], form['password'])
                    flask.session['uid'] = user.get_id()
                    flask_login.login_user(user)
                    return flask.redirect(flask.url_for('admin', lang=_('en'))), 302
                except Exception as ex:
                    if opt['VERBOSE']:
                        print('Login problem ocurred:')
                        print(ex)
                    return flask.render_template('login_fail.html', opt=opt), 200
            else:
                return flask.render_template('login.html', opt=opt), 200
        else:
            return flask.redirect(flask.url_for('admin', lang=_('en'))), 302
    except Exception as ex:
        traceback.print_exc()

@app.route('/<lang>/admin/', methods=['GET', 'POST'])
@flask_login.login_required
def admin():
    "Gives the administrator a page with forms to modify the database."
    return flask.render_template('adminform.html',
        opt=opt, data=database.get_reserves()), 200

@app.route('/<lang>/add/', methods=['POST'])
@flask_login.login_required
def add_reserve():
    "Parses the form to add a reserve."
    try:
        form = flask.request.form
        code = form['course_code']
        instructor = form['instructor']
        bookbag = form['bookbag_id']
        database.add_reserve(code, instructor, bookbag)
    except Exception as ex:
        print('Error occurred while parsing addition: ')
        print(ex)
        message = 'Couldn\'t submit form.'
        return flask.redirect(flask.url_for('admin', lang=_('en'))), 302
    message = 'Form successfully submitted.'
    return flask.redirect(flask.url_for('admin', lang=_('en'))), 302

@app.route('/<lang>/edit/', methods=['POST'])
@flask_login.login_required
def edit_reserve():
    "Parses the form to edit a reserve."
    try:
        form = flask.request.form
        id = form['reserve_id']
        code = form['course_code']
        instructor = form['instructor']
        bookbag = form['bookbag_id']
        database.edit_reserve(id, code, instructor, bookbag)
    except Exception as ex:
        print('Error occurred while parsing edit: ')
        print(ex)
        message = 'Couldn\'t submit form.'
        return flask.redirect(flask.url_for('admin', lang=_('en'))), 302
    message = 'Form successfully submitted.'
    return flask.redirect(flask.url_for('admin', lang=_('en'))), 302

@app.route('/<lang>/delete/', methods=['POST'])
@flask_login.login_required
def delete_reserve():
    "Parses the form to delete a reserve."
    try:
        form = flask.request.form
        id = form['reserve_id']
        database.delete_reserve(id)
    except Exception as ex:
        print('Error occurred while parsing deletion: ')
        print(ex)
        message = 'Couldn\'t submit form.'
        return flask.redirect(flask.url_for('admin', lang=_('en'))), 302
    message = 'Form successfully submitted.'
    return flask.redirect(flask.url_for('admin', lang=_('en'))), 302

if __name__ == '__main__':
    # app.run(debug=opt['DEBUG'], host=opt['HOST'], port=opt['PORT'])
    from twisted.internet import reactor
    from twisted.web.server import Site
    from twisted.web.wsgi import WSGIResource

    resource = WSGIResource(reactor, reactor.getThreadPool(), app)
    site = Site(resource)

    reactor.listenTCP(opt['PORT'], site, interface=opt['HOST'])
    reactor.run()
