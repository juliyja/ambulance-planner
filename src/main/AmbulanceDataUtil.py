from main.DatabaseUtil import get_cursor
from main.Planner import ambulances, accidents


def fetch_ambulance_data():
    while True:
        cursor = get_cursor()
        cursor.execute("SELECT * FROM Ambulance WHERE Assignment is 'Available'")
        rows = cursor.fetchall()
        for row in rows:
            ambulances.append(list(row))


def fetch_accident_data():
    while True:
        cursor = get_cursor()
        cursor.execute("SELECT * FROM Accident WHERE Time <= NOW() AND Processed is NULL")
        rows = cursor.fetchall()
        for row in rows:
            accidents.append(list(row))
            cursor.execute("UPDATE Accident SET Processed = 1 WHERE AccidentId = " + str(row[0]))
