from main.AmbulanceDataUtil import fetch_ambulance_data, fetch_accident_data
from main.NaturalLanguageProcessor import categorize_accident
from main.RESTapi import app
from main.XGboost import XGBoost
from main.Planner import run_planner
import _thread


def main():
    print("Starting XGBoost...")
    # XGBoost.train_data()
    # _thread.start_new_thread(fetch_accident_data, ())
    # _thread.start_new_thread(fetch_ambulance_data, ())
    # _thread.start_new_thread(run_planner, ())
    app.run()
    print("Application closed")


if __name__ == "__main__":
    main()
