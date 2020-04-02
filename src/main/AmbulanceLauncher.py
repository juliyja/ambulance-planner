from main.AmbulanceDataUtil import fetch_ambulance_data, fetch_accident_data
from main.NaturalLanguageProcessor import categorizeAccident
from main.RESTapi import app
from main.XGboost import XGBoost
from main.Planner import run_planner
import _thread


def main():
    print("Starting XGBoost...")
    XGBoost.train_data()
    _thread.start_new_thread(print_time, ())
    _thread.start_new_thread(run_planner, ())
    app.run(port='5002')
    print("Application closed")


if __name__ == "__main__":
    main()
