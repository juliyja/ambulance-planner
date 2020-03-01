from main.RESTapi import app, close_connection
from main.XGboost import XGBoost


def main():
    print("Starting XGBoost...")
    XGBoost.train_data()
    app.run(port='5002')
    print("Starting Ambulance Planner")

    print("Closing connection with the database...")
    close_connection()

if __name__ == "__main__":
    main()