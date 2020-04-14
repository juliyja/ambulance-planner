import csv
import datetime
import time
from math import sqrt

import joblib
import pandas as pd
import xgboost as xgb
from datetime import datetime

from main.AmbulanceDataUtil import ambulance_count
from main.DatabaseUtil import get_cursor, close_connection

accidents = []
ambulances = []
hospitals = []


def run_planner():
    print("Starting Ambulance Planner")
    while True:
        local_accidents = accidents.copy()
        local_ambulances = ambulances.copy()
        if len(local_accidents) > 0:
            now = datetime.now()
            prioritise_accidents(local_accidents)
            local_accidents = list(
                filter(lambda accident: len(local_accidents) / ambulance_count > 0.75 or accident[7] < 4,
                       local_accidents))
            # choose the accident with the highest priority
            best_accident = min(local_accidents, key=lambda accident: (accident[7], -accident[9]))
            # find best ambulance for the prioritised accident
            chosen_ambulance, ambulance_to_site, support, support_to_site = ambulance_assignment(best_accident,
                                                                                                 local_ambulances)
            chosen_hospital, site_to_hospital = hospital_assignment(best_accident)
            if support:
                save_trip(best_accident, chosen_hospital, support, support_to_site, site_to_hospital)
            save_trip(best_accident, chosen_hospital, chosen_ambulance, ambulance_to_site, site_to_hospital)
            finish_processing(best_accident)
            print("Categorised in ", datetime.now() - now)
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

    return prediction[0]


def prioritise_accidents(local_accidents):
    for accident in local_accidents:

        category = accident[3]
        start_time = accident[4]
        now = datetime.now()
        time_elapsed = (now - start_time).total_seconds()

        accident.append(time_elapsed)

        if category == "1":
            accident[7] = 1
        elif category == "2":
            # one minute
            accident[7] = 2 if time_elapsed > 60 else 6
        elif category == "3":
            # 8 minutes
            accident[7] = 3 if time_elapsed > 480 else 7
        elif category == "4":
            # 1.5 hours
            if time_elapsed > 5400:
                accident[7] = 4
                # 2 hours and 15 min
                if time_elapsed > 8100:
                    accident[7] = 3
            else:
                accident[7] = 8
        # if category is HCP and more time then 1.5 hours have elapsed from the accident increase the priority
        elif category == "HCP":
            if time_elapsed > 5400:
                accident[7] = 5
                # if more than 2.5 hours elapsed increase the priority further
                if time_elapsed > 9000:
                    accident[7] = 3
            else:
                accident[7] = 9


# find the best available ambulance that matches accident type
def ambulance_assignment(best_accident, local_ambulances):

    support_vehicle = None
    support_predicted_travel_time = None

    if best_accident[5] & 2 == 2:
        filtered_ambulances = check_types(2, local_ambulances, 4)
        support_predicted_travel_time, support_vehicle = get_ambulance_and_time(best_accident, filtered_ambulances)

    filtered_ambulances = check_types(best_accident[5] & 509, local_ambulances, 4)
    predicted_travel_time, best_ambulance = get_ambulance_and_time(best_accident, filtered_ambulances)

    return best_ambulance, predicted_travel_time, support_vehicle, support_predicted_travel_time


def get_ambulance_and_time(best_accident, filtered_ambulances):
    predicted_time, ambulance = find_best_resource(best_accident, filtered_ambulances, 2, 1)
    if ambulance is None:
        print("There was no support vehicle available to assign for this accident")

    else:
        cursor = get_cursor()
        cursor.execute("UPDATE Ambulance SET AVAILABLE = FALSE WHERE ID = " + str(ambulance[0]))
        cursor.connection.commit()
        ambulances.remove(ambulance)
    return predicted_time, ambulance


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

    predicted_travel_time, closest_hospital = find_best_resource(best_accident, filtered_hospitals, 2, 3,
                                                                 get_sort_hospitals(best_accident, filtered_hospitals))

    return closest_hospital, predicted_travel_time


def get_sort_hospitals(best_accident, hospital_list):
    hospital_type_ambulance = best_accident[5] & 508
    sorted_hospitals = check_types(hospital_type_ambulance, hospital_list, 4)
    mental_health_accident = best_accident[5] & 256 == 256

    def sort_hospitals(hospital):
        is_mental_health = hospital[5] & 256 == 256
        if hospital in sorted_hospitals:
            return distance_to_point(best_accident, hospital[2], hospital[3])
        else:
            if is_mental_health or mental_health_accident:
                return 1000000.0
            else:
                return distance_to_point(best_accident, hospital[2], hospital[3]) * 1.2

    return sort_hospitals


def find_best_resource(best_accident, filtered_list, lat_index, lon_index, sorting_method=None):
    now = datetime.now()

    if sorting_method is None:
        def sorting_method(res): return distance_to_point(best_accident, res[lat_index], res[lon_index])

    filtered_list.sort(key=sorting_method)
    filtered_list = filtered_list[:5]

    resources_with_time = []
    for resource in filtered_list:
        pred_time = get_time_between_points(
            resource[lat_index],
            resource[lon_index],
            best_accident[2],
            best_accident[1],
            distance_to_point(best_accident, resource[lat_index], resource[lon_index]))

        resources_with_time.append((resource, pred_time))

    print("Estimated in ", datetime.now() - now)
    best_resource, predicted_travel_time = min(
        resources_with_time,
        key=lambda r: r[1])
    print("Predicted in ", datetime.now() - now)

    return predicted_travel_time, best_resource


def distance_to_point(best_accident, lat_point, lon_point):
    lat_accident = best_accident[2]
    lon_accident = best_accident[1]
    distance = sqrt((lat_accident - lat_point) ** 2 + (lon_accident - lon_point) ** 2)

    return distance


# check if an item, such as ambulance or hospital, is suitable for a particular accident
# @param prioritised accident, list of items being checked
def check_types(accident_type, resource_list, index):
    filtered_list = []

    for resource in resource_list:
        resource_type = resource[index]
        # use binary and to check if checked item's type and accident's type are compatible
        if int(resource_type) & int(accident_type) == int(accident_type):
            # print(item_type, " and ", accident_type, " Types match")
            if int(resource_type) & 1 == int(accident_type) & 1:
                filtered_list.append(resource)

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
    return sqrt((float(lat_origin) - float(lat_dest)) ** 2 + (float(lon_origin) - float(lon_dest)) ** 2)
