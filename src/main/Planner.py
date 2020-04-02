import datetime

import joblib
import pandas as pd
import xgboost as xgb
from datetime import datetime

from main.DatabaseUtil import get_cursor

accidents = []
ambulances = []


def run_planner():
    print("Starting Ambulance Planner")
    while True:
        if len(accidents) > 0:
            test = get_time_between_points(0.123155, 51.480202, -0.256472, 51.467222)
            prioritise_accidents()
            best_accident = min(accidents, key=lambda accident: accident[8])
            print(best_accident)


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


def prioritise_accidents():
    for accident in accidents:

        category = accident[3]
        start_time = accident[5]
        now = datetime.now()
        time_elapsed = (now - start_time).total_seconds()

        if category == "1":
            accident[8] = 1
        elif category == "2":
            accident[8] = 2 if time_elapsed > 60 else 6
        elif category == "3":
            accident[8] = 3 if time_elapsed > 500 else 7
        elif category == "4":
            accident[8] = 4 if time_elapsed > 6000 else 8
        # if category is HCP and more time then 2.5 hours have elapsed from the accident send an ambulance
        elif category == "HCP":
            accident[8] = 5 if time_elapsed > 6000 else 9


def ambulance_assignment(best_accident):
    best_ambulance = None
    for ambulance in ambulances:
        ambulance_cat = ambulance[3]
        accident_cat = best_accident[4]

        min_time = 31500000

        #TODO: Add ambulance filtering
        if int(ambulance_cat) & int(accident_cat) != int(accident_cat):
            print("Not Same")
        else:
            print("Same")
            pred_time = get_time_between_points(ambulance[1], ambulance[2], best_accident[1], best_accident[2])
            if pred_time < min_time:
                min_time = pred_time
                best_ambulance = ambulance

    if best_ambulance is None:
        print("There was no ambulance available to assign for this accident")

    else:
        cursor = get_cursor()
        cursor.execute("UPDATE Ambulance SET Assignment = Unavailable")

    return best_ambulance

#def hospital_assignment(best_accident):
