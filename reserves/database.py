from course_reserves import opt
import psycopg2
import os

def get_db():
    """
    Get a database connection.

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
            SELECT course_code, instructor,
            bookbag_id FROM reserve
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
    "Adds a reserve to the database."
    dbh = get_db()
    cur = dbh.cursor()
    try:
        cur.execute("""INSERT INTO reserve VALUES (%s, %s, %s, %s)""", 
                    (os.urandom(24).encode('hex'),
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
    Edits an existing reserve with the given id.
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
    Deletes the reserve with the given id.

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
