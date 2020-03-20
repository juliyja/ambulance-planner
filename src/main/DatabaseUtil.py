from main.Planner import accidents
from main.RESTapi import get_cursor



def print_time():
    while True:
        cursor = get_cursor()
        cursor.execute("SELECT * FROM Accident WHERE Time <= NOW() AND Processed is NULL")
        rows = cursor.fetchall()
        for row in rows:
            accidents.append(list(row))
            cursor.execute("UPDATE Accident SET Processed = 1 WHERE AccidentId = " + str(row[0]))
