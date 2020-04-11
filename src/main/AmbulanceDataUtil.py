from main.DatabaseUtil import get_cursor
from main.Planner import ambulances, accidents, hospitals
import time

time_fetched_hospitals = 0
fetched_hospitals_interval = 3600


def fetch_ambulance_data():

    ambulances_temp = []
    cursor = get_cursor()
    cursor.execute("SELECT * FROM Ambulance")
    rows = cursor.fetchall()
    for row in rows:
        ambulances_temp.append(list(row))
    ambulances.clear()
    ambulances.extend(ambulances_temp)


def fetch_accident_data():

    cursor = get_cursor()
    cursor.execute("SELECT * FROM Accident WHERE Time <= NOW() AND Processed IS NULL")
    rows = cursor.fetchall()
    for row in rows:
        accidents.append(list(row))
        cursor.execute("UPDATE Accident SET Processed = 0 WHERE ID = " + str(row[0]))
    cursor.connection.commit()


def fetch_hospital_data():
    cursor = get_cursor()
    cursor.execute("SELECT * FROM Hospital")
    rows = cursor.fetchall()
    for row in rows:
        hospitals.append(list(row))


def refresh_variables():

    global time_fetched_hospitals

    while True:
        fetch_accident_data()
        fetch_ambulance_data()

        # check hospitals once in an hour
        if time_fetched_hospitals + fetched_hospitals_interval < time.time():
            fetch_hospital_data()
            time_fetched_hospitals = time.time()

        time.sleep(10.0)
