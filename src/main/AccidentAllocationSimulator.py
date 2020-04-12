import numpy
import requests
import csv
from datetime import datetime, timedelta
from main.AmbulanceDataUtil import refresh_variables
from main.RESTapi import app
from main.Planner import run_planner
import _thread
from main.DatabaseUtil import get_cursor, close_connection
import time

URL = "http://127.0.0.1:5000/accident"

# TODO: create a more accurate way of assigning vehicle type
mental_health = 256
cardiac_arrest = 128
major_trauma = 64
stroke = 32
heart_attack = 16
general_hospital = 8
neonatal = 4
support_vehicle_needed = 2
transport_needed = 1

counter = 3059

accident_density = {"1": 1530, "2": 764, "3": 459, "4": 306}

# the index in the list represents the hour and so:
# at 1 - 112 accidents, at 2am - 104 ... at 11pm - 123
list_of_accidents = [121, 112, 104, 98, 95, 94, 95, 100, 110, 125, 141, 159, 164, 163, 156, 145, 141, 142, 142, 139,
                     134, 130, 126, 123]


def create_accidents():
    # generate accidents
    now = datetime.now()
    for i in range(0, 24):
        for j in range(list_of_accidents[now.hour]):
            category = assign_category()

            accident_type = assign_type(category)
            timeS = generate_time(now).strftime('%Y-%m-%d %H:%M:%S')
            lat, lon = generate_location()
            casualties = assign_number_casualties()

            data = {"Longitude": lon, "Latitude": lat, "Category": category,
                    "Type": accident_type, "Time": timeS, "Casualties": casualties, "Login": "juliyja", "Password": "szymon",}

            requests.post(url=URL, json=data)

        now = now + timedelta(hours=1)


# TODO: create a more accurate way of assigning types
def assign_type(category):
    accident_type = 0

    if category == "1" or category == "2":
        if category == "1":
            accident_type = support_vehicle_needed
        accident_type += transport_needed

    random = numpy.random.uniform(0, 100, 1)[0]
    if random <= 5:
        accident_type += neonatal
    elif 5 < random < 40:
        accident_type = general_hospital
    elif 40 < random < 50:
        accident_type += heart_attack
    elif 50 < random < 60:
        accident_type += stroke
    elif 60 < random < 62:
        accident_type += mental_health
    elif 65 < random < 70:
        accident_type += cardiac_arrest
    # TODO: might not work
    elif int(category) > 2 and 70 < random < 72:
        accident_type += 1
    elif int(category) > 2 and 72 < random < 73:
        accident_type += 2
    else:
        accident_type += major_trauma
    return accident_type


def generate_time(time):
    minutes = int(numpy.random.uniform(0, 60, 1)[0])
    seconds = int(numpy.random.uniform(0, 60, 1)[0])
    time = time.replace(minute = minutes, second = seconds)
    return time


def assign_category():
    random = numpy.random.uniform(0, 100, 1)[0]
    if random < 12:
        category = "1"
    elif random < 74:
        category = "2"
    elif random < 96:
        category = "3"
    elif random < 97:
        category = "4"
    else:
        category = "'HCP'"

    return category


# TODO: Delete if not used
def assign_number_casualties():
    random = numpy.random.uniform(0, 100, 1)[0]
    if random < 85:
        casualties = 1
    elif random < 97:
        casualties = 2
    else:
        casualties = numpy.random.uniform(3, 10, 1)[0]

    return casualties


def generate_location():
    while True:
        accident_latitude = numpy.random.uniform(51.297844, 51.710034, 1)[0]
        accident_longitude = numpy.random.uniform(-0.478763, 0.288949, 1)[0]
        with open('accident_density.csv', mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                if float(row["3Lat"]) <= accident_latitude <= float(row["1Lat"]) and float(
                        row["1Lon"]) <= accident_longitude <= float(row["2Lon"]):
                    if accident_density[row["Density"]] > 0:
                        accident_density[row["Density"]] -= 1
                        return accident_latitude, accident_longitude


def update_ambulance_availability():
    while True:
        cursor = get_cursor()
        cursor.execute("""UPDATE AMBULANCE
                            SET AVAILABLE = TRUE
                            WHERE EXISTS(SELECT *
                                         FROM (
                                                  SELECT AMBULANCE_ID AS AMBULANCE_ID, MAX(EST_HOSPITAL_ARRIVAL_TIME) AS MAX
                                                  FROM TRIP
                                                  WHERE DEPARTURE_TIME > UNIX_TIMESTAMP() - 3600
                                                  GROUP BY AMBULANCE_ID) as AIM
                                         WHERE AMBULANCE.ID = AMBULANCE_ID
                                           AND MAX < UNIX_TIMESTAMP());""")
        close_connection(cursor)
        time.sleep(5.0)


def main():
    _thread.start_new_thread(app.run, ())
    time.sleep(10.0)
    create_accidents()
    _thread.start_new_thread(refresh_variables, ())
    time.sleep(10.0)
    run_planner()
    _thread.start_new_thread(update_ambulance_availability, ())
    print("Application closed")


if __name__ == "__main__":
    main()
