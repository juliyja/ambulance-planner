import datetime

import joblib
import pandas as pd
import xgboost as xgb
from datetime import datetime

from main.DatabaseUtil import get_cursor

accidents = []
ambulances = []
hospitals = []


def run_planner():
    print("Starting Ambulance Planner")
    while True:
        local_accidents = accidents.copy()
        if len(local_accidents) > 0:
            test = get_time_between_points(0.123155, 51.480202, -0.256472, 51.467222)
            prioritise_accidents(local_accidents)
            # choose the accident with the highest priority
            best_accident = min(local_accidents, key=lambda accident: accident[7])
            # find best ambulance for the prioritised accident
            ambulance_assignment(best_accident)
            # print(best_accident)


# use the model generated using XGBoost to predict travel times between two points

def get_time_between_points(pickup_long, pickup_lat, dropoff_long, dropoff_lat):
    trained_xgb_model = joblib.load("results")

    model_data = {
        "pickup_longitude": pickup_long,
        "pickup_latitude": pickup_lat,
        "dropoff_longitude": dropoff_long,
        "dropoff_latitude": dropoff_lat
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
    best_ambulance = None
    # 31536000 = 365 days in seconds
    min_time = 31536000

    filtered_ambulances = check_type(best_accident, local_ambulances)
    print("FILTERED LIST", filtered_ambulances)

    for ambulance in filtered_ambulances:
        pred_time = get_time_between_points(ambulance[1], ambulance[2], best_accident[1], best_accident[2])
        if pred_time < min_time:
            min_time = pred_time
            best_ambulance = ambulance

    if best_ambulance is None:
        print("There was no ambulance available to assign for this accident")
    else:
        cursor = get_cursor()
        cursor.execute("UPDATE Ambulance SET Assignment = 'Unavailable' WHERE AmbulanceId = " + str(best_ambulance[0]))

    return best_ambulance


def hospital_assignment(best_accident):

    filtered_hospitals = check_type(best_accident, hospitals)

    for hospital in filtered_hospitals:
        print("nothing yet")



# check if an item, such as ambulance or hospital, is suitable for a particular accident
# @param prioritised accident, list of items being checked
def check_type(best_accident, item_list):

    filtered_list = []

    for item in item_list:
        item_type = item[4]
        accident_type = best_accident[5]
        # use binary and to check if checked item's type and accident's type are compatible
        if int(item_type) & int(accident_type) == int(accident_type):
            # print(item_type, " and ", accident_type, " Types match")
            filtered_list.append(item)

    return filtered_list


def save_trip():
    return
