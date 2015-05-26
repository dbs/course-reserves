from course_reserves import opt
import os
import psycopg2
import ldap
import database

class User():
    def __init__(self, username, session_id=None):
        if not session_id:
            self.id = os.urandom(24).encode('hex')
        else:
            self.id = session_id
        self.username = username

    @staticmethod
    def try_login(host, username, password):
        "Tries to log into Laurentian's LDAP servers with the provided info."
        try:
            conn = ldap.initialize(host)
            if opt['STUDENT']:
                conn.simple_bind_s('cn=%s,ou=STD,o=LUL' % username, password)
            else:
                conn.simple_bind_s('cn=%s,ou=Empl,o=LUL' % username, password)
            u = User(username)
            u.add_to_db()
            return u
        except Exception, ex:
            if opt['VERBOSE']:
                print('Couldn\' log in:')
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
        except Exception, ex:
            if opt['VERBOSE']:
                print('Couldn\'t query database, or user is expired:')
                print(ex)
        dbh.close()
        return None

    def add_to_db(self):
        dbh = database.get_db()
        cur = dbh.cursor()
        try:
            cur.execute("INSERT INTO users VALUES (%s, %s)",
                (self.id, self.username))
        except Exception, ex:
            print('Could\'t add user to database:')
            print('ex')
        dbh.commit()
        dbh.close()

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id
