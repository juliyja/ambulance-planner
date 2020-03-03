import pymysql

from main.Planner import accidents


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


def print_time():
    while True:
        cursor = get_cursor()
        cursor.execute("SELECT * FROM Accident WHERE Time <= NOW() AND Processed is NULL")
        rows = cursor.fetchall()
        for row in rows:
            accidents.append(list(row))
            cursor.execute("UPDATE Accident SET Processed = 1 WHERE AccidentId = " + str(row[0]))
