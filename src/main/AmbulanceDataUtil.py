from main.DatabaseUtil import get_cursor
from main.Planner import ambulances


def fetch_ambulance_data():
    while True:
        cursor = get_cursor()
        cursor.execute("SELECT * FROM Ambulance WHERE Assignment is 'Available'")
        rows = cursor.fetchall()
        for row in rows:
            ambulances.append(list(row))
