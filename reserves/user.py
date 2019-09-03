from course_reserves import opt
import os
import psycopg2
import ldap
import database

authorized = []

class User():
    """
    A class necessary for Flask-Login to function. It holds methods
    to log users in from LDAP and add them to a database of users.
    """

    def __init__(self, username, session_id=None):
        "Returns a User object for Flask-Login"
        if not session_id:
            self.id = os.urandom(24).hex()
        else:
            self.id = session_id
        self.username = username

    @staticmethod
    def try_login(host, username, password):
        "Tries to log into Laurentian's LDAP servers with the provided info."
        try:
            if username not in authorized:
                return None
            conn = ldap.initialize(host)
            if opt['STUDENT']:
                conn.simple_bind_s('cn=%s,ou=STD,o=LUL' % username, password)
            else:
                conn.simple_bind_s('cn=%s,ou=Empl,o=LUL' % username, password)
            u = User(username)
            u.add_to_db()
            return u
        except Exception as ex:
            if opt['VERBOSE']:
                print("Couldn't log in:")
                print(ex)
            raise ex
        
    @staticmethod
    def get_by_id(id):
        "Returns a logged-in user with the given id."
        dbh = database.get_db()
        cur = dbh.cursor()
        try:
            cur.execute("SELECT * FROM get_users WHERE id = '%s'" % id)
            return User(cur.fetchone()[1], id)
        except Exception as ex:
            if opt['VERBOSE']:
                print('Couldn\'t query database, or user is expired:')
                traceback.print_exc()
        dbh.close()
        return None

    def add_to_db(self):
        "Adds a user to the database."
        dbh = database.get_db()
        cur = dbh.cursor()
        try:
            cur.execute("INSERT INTO users VALUES (%s, %s)",
                (self.id, self.username))
        except Exception as ex:
            print('Could\'t add user to database:')
            print(ex)
        dbh.commit()
        dbh.close()

    def is_authenticated(self):
        """
        Returns the authentication status of a user.
        Because this user always requires a password, this is always true.
        Needed by Flask-Login.
        """
        return True

    def is_active(self):
        "Like above - this is needed by Flask-Login."
        return True

    def is_anonymous(self):
        "Needed by Flask-Login."
        return False

    def get_id(self):
        "Returns the user's UID."
        return self.id
