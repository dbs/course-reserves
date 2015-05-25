import psycopg2
import random
from course_reserves import opt

def get_db():
    """
    Get a database connection

    With a host attribute in the mix, you could connect to a remote
    database, but then you would have to set up .pgpass or add a
    password parameter, so let's keep it simple.
    """
    try:
        return psycopg2.connect(
            database=opt['DB_NAME'],
            user=opt['DB_USER']
        )
    except Exception, ex:
        if opt['VERBOSE']:
            print(ex)

def get_reserves():
    """Returns all of the existing reserves."""
    dbh = get_db()
    cur = dbh.cursor()
    try:
        cur.execute("""
            SELECT id, course_code, instructor,
            bookbag_id from RESERVE
        """)
        result = cur.fetchall()
        dbh.close()
        return result
    except Exception, ex:
        if opt['VERBOSE']:
            print('Couldn\'t get table for reserves: ')
            print(ex)
    dbh.close()
    return None

def add_reserve(code, instructor, bookbag):
    """Adds a reserve."""
    dbh = get_db()
    cur = dbh.cursor()
    try:
        cur.execute("""INSERT INTO reserve VALUES (%s, %s, %s, %s)""", 
                    (random.SystemRandom().randint(-0xFFFFFF, 0xFFFFFF),
                    code, instructor, bookbag))
    except Exception, ex:
        if opt['VERBOSE']:
            print('Couldn\'t add a reserve: ')
            print(ex)
        raise ex
    dbh.commit()
    dbh.close()

def edit_reserve(id, code, instructor, bookbag):
    """
    Edits an existing reserve.
    """
    dbh = get_db()
    cur = dbh.cursor()
    try:
        cur.execute("""UPDATE TABLE reserve SET course_code, instructor,
            bookbag_id = %s, %s, %s WHERE id = %s""", (code, instructor, bookbag, id))
    except Exception, ex:
        if opt['VERBOSE']:
            print('Couldn\'t edit a reserve: ')
            print(ex)
        raise ex
    dbh.commit()
    dbh.close()

def delete_reserve(id):
    """
    Deletes a reserve.

    Careful!
    """
    dbh = get_db()
    cur = dbh.cursor()
    try:
        cur.execute("""DELETE FROM reserve where id = %s""" % id)
    except Exception, ex:
        if opt['VERBOSE']:
            print('Could not delete reserve:')
            print(ex)
        raise ex
    dbh.commit()
    dbh.close()