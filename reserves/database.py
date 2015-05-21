import psycopg2
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
            print('Couldn\'t get table for reserves.')
    dbh.close()
    return None

#This will hold all of our DB methods.
