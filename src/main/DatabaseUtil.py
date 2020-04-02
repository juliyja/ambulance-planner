import pymysql

def get_cursor():
    db_connect = pymysql.connect(host='127.0.0.1',
                                 database='AmbulanceDB',
                                 user='root',
                                 password='on@itsiriC_96')
    cursor = db_connect.cursor()
    return cursor


def close_connection(cursor):
    if cursor.connection.open:
        connection = cursor.connection
        cursor.close()
        connection.close()

