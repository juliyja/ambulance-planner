from main.DatabaseUtil import get_cursor
from main.Planner import ambulances, accidents, hospitals
import time

time_fetched_hospitals = 0
fetched_hospitals_interval = 3600
ambulance_count = 0


def fetch_ambulance_data():

    ambulances_temp = []
    cursor = get_cursor()
    cursor.execute("SELECT * FROM Ambulance WHERE AVAILABLE = TRUE")
    rows = cursor.fetchall()
    for row in rows:
        ambulances_temp.append(list(row))
    ambulances.clear()
    ambulances.extend(ambulances_temp)


def count_ambulances():
    cursor = get_cursor()
    cursor.execute("SELECT COUNT(*) FROM AMBULANCE")
    global ambulance_count
    ambulance_count = cursor.fetchone()[0]


def fetch_accident_data():

    cursor = get_cursor()
    cursor.execute("SELECT * FROM Accident WHERE Time <= NOW() AND Processed IS NULL")
    rows = cursor.fetchall()
    for row in rows:
        accidents.append(list(row))
        cursor.execute("UPDATE Accident SET Processed = 0 WHERE ID = " + str(row[0]))
    cursor.connection.commit()


def fetch_hospital_data():
    hospitals_temp = []
    cursor = get_cursor()
    cursor.execute("SELECT * FROM Hospital")
    rows = cursor.fetchall()
    for row in rows:
        hospitals_temp.append(list(row))
    hospitals.clear()
    hospitals.extend(hospitals_temp)


def refresh_variables():

    global time_fetched_hospitals

    count_ambulances()

    while True:
        fetch_accident_data()
        fetch_ambulance_data()

        # check hospitals once in an hour
        if time_fetched_hospitals + fetched_hospitals_interval < time.time():
            fetch_hospital_data()
            time_fetched_hospitals = time.time()

        time.sleep(10.0)
