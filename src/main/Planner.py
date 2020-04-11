import csv
import datetime
import time
from math import sqrt

import joblib
import pandas as pd
import xgboost as xgb
from datetime import datetime
from main.DatabaseUtil import get_cursor, close_connection

accidents = []
ambulances = []
hospitals = []


def run_planner():
    print("Starting Ambulance Planner")
    while True:
        local_accidents = accidents.copy()
        if len(local_accidents) > 0:
            prioritise_accidents(local_accidents)
            # choose the accident with the highest priority
            best_accident = min(local_accidents, key=lambda accident: accident[7])
            # find best ambulance for the prioritised accident
            chosen_ambulance, ambulance_to_site, support, support_to_site = ambulance_assignment(best_accident)
            chosen_hospital, site_to_hospital = hospital_assignment(best_accident)
            if support:
                save_trip(best_accident, chosen_hospital, support, support_to_site, site_to_hospital)
            save_trip(best_accident, chosen_hospital, chosen_ambulance, ambulance_to_site, site_to_hospital)
            finish_processing(best_accident)

        if not local_accidents:
            time.sleep(10.0)


def finish_processing(best_accident):
    cursor = get_cursor()
    cursor.execute("UPDATE ACCIDENT SET PROCESSED = 1 WHERE ID = " + str(best_accident[0]))
    accidents.remove(best_accident)
    cursor.connection.commit()
    close_connection(cursor)


# use the model generated using XGBoost to predict travel times between two points

def get_time_between_points(lat_origin, lon_origin, lat_dest, lon_dest, distance):
    trained_xgb_model = joblib.load("results")

    model_data = {
        "lat_origin": lat_origin,
        "lon_origin": lon_origin,
        "lat_dest": lat_dest,
        "lon_dest": lon_dest,
        "distance": distance
    }
    df = pd.DataFrame([model_data], columns=model_data.keys())
    prediction = trained_xgb_model.predict(xgb.DMatrix(df))

    return prediction


def prioritise_accidents(local_accidents):
    for accident in local_accidents:

        category = accident[3]
        start_time = accident[4]
        now = datetime.now()
        time_elapsed = (now - start_time).total_seconds()

        if category == "1":
            accident[7] = 1
        elif category == "2":
            accident[7] = 2 if time_elapsed > 60 else 6
        elif category == "3":
            accident[7] = 3 if time_elapsed > 500 else 7
        elif category == "4":
            accident[7] = 4 if time_elapsed > 6000 else 8
        # if category is HCP and more time then 2.5 hours have elapsed from the accident send an ambulance
        elif category == "HCP":
            accident[7] = 5 if time_elapsed > 6000 else 9


# find the best available ambulance that matches accident type
def ambulance_assignment(best_accident):
    local_ambulances = ambulances.copy()
    support_vehicle = None
    support_predicted_travel_time = None
    if best_accident[5] & 2 == 2:
        filtered_ambulances = check_type(2, local_ambulances, 4)

        support_predicted_travel_time, support_vehicle = find_best_resource(best_accident, filtered_ambulances)

        if support_vehicle is None:
            print("There was no support vehicle available to assign for this accident")

        else:
            cursor = get_cursor()
            cursor.execute("UPDATE Ambulance SET AVAILABLE = FALSE WHERE ID = " + str(support_vehicle[0]))

    filtered_ambulances = check_type(best_accident[5] & 509, local_ambulances, 4)

    filtered_ambulances.sort(key=lambda ambulance: distance_to_point(best_accident, ambulance[2], ambulance[1]))
    filtered_ambulances = filtered_ambulances[:5]

    predicted_travel_time, best_ambulance = find_best_resource(best_accident, filtered_ambulances)

    if best_ambulance is None:
        print("There was no ambulance available to assign for this accident")

    else:
        cursor = get_cursor()
        cursor.execute("UPDATE Ambulance SET AVAILABLE = FALSE WHERE ID = " + str(best_ambulance[0]))

    return best_ambulance, predicted_travel_time, support_vehicle, support_predicted_travel_time


# FIXME: bitwise & (bitwise and) between 508 and accident type
def hospital_assignment(best_accident):
    emergency_dept_needed = None
    filtered_hospitals = []

    # if accident category is 1 or 2 the hospital needs to have an emergency department
    if best_accident[3] == "1" or best_accident[3] == "2":
        emergency_dept_needed = 1

    if emergency_dept_needed:
        for h in hospitals:
            if h[5] == 1:
                filtered_hospitals.append(h)
    else:
        filtered_hospitals = hospitals

    predicted_travel_time, closest_hospital = find_best_resource(best_accident, filtered_hospitals)

    # TODO: add for more sophisticated hospital choice
    # filtered_hospitals = check_type(best_accident, hospitals)

    return closest_hospital, predicted_travel_time


def find_best_resource(best_accident, filtered_ambulances):
    best_resource = min(
        filtered_ambulances,
        key=lambda ambulance:
        get_time_between_points(
            ambulance[2],
            ambulance[1],
            best_accident[2],
            best_accident[1],
            distance_to_point(best_accident, ambulance[2], ambulance[1])))
    support_distance = distance_to_point(best_accident, best_resource[2], best_resource[1])
    predicted_travel_time = int(
        get_time_between_points(best_resource[2], best_resource[1], best_accident[2], best_accident[1],
                                support_distance)[0])
    return predicted_travel_time, best_resource


def distance_to_point(best_accident, lat_point, lon_point):
    lat_accident = best_accident[2]
    lon_accident = best_accident[1]
    distance = sqrt((lat_accident - lat_point) ** 2 + (lon_accident - lon_point) ** 2)

    return distance


# check if an item, such as ambulance or hospital, is suitable for a particular accident
# @param prioritised accident, list of items being checked
def check_type(accident_type, item_list, index):
    filtered_list = []

    for item in item_list:
        item_type = item[index]
        # use binary and to check if checked item's type and accident's type are compatible
        if int(item_type) & int(accident_type) == int(accident_type):
            # print(item_type, " and ", accident_type, " Types match")
            filtered_list.append(item)

    return filtered_list


def save_trip(accident, hospital, ambulance, ambulance_to_scene, scene_to_hospital):
    # the estimated time it will take the ambulance to complete the trip
    avg_scene_time = 15 * 60
    predicted_trip_duration = ambulance_to_scene + scene_to_hospital + avg_scene_time

    cursor = get_cursor()

    trip_insert_query = """INSERT INTO Trip (DEPARTURE_TIME, ACCIDENT_ID, AMBULANCE_ID, HOSPITAL_ID, 
                           EST_SCENE_ARRIVAL_TIME, EST_HOSPITAL_ARRIVAL_TIME) 
                           VALUES 
                           ( UNIX_TIMESTAMP(),""" + str(accident[0]) + "," + str(ambulance[0]) + "," \
                        + str(hospital[0]) + "," + "UNIX_TIMESTAMP() +" + str(ambulance_to_scene) + "," + \
                        "UNIX_TIMESTAMP() +" + str(predicted_trip_duration) + ")"""
    print(trip_insert_query)

    cursor.execute(trip_insert_query)
    cursor.connection.commit()
    close_connection(cursor)

    return "Trip record for accident with ID: " + str(accident[0]) + "successfully added to database"


def euclidean_dist(lat_origin, lon_origin, lat_dest, lon_dest):
    return sqrt((lat_origin - lat_dest) ** 2 + (lon_origin - lon_dest) ** 2)

