from datetime import datetime

from flask import Flask, request
from flask_restful import Api, abort
import pymysql

app = Flask(__name__)
api = Api(app)


def get_cursor():
    db_connect = pymysql.connect(host='127.0.0.1',
                                 database='AmbulanceDB',
                                 user='root',
                                 password='on@itsiriC_96')
    cursor = db_connect.cursor()
    return cursor


def close_connection(cursor):
    if cursor.connection.open:
        connection = cursor.connection
        cursor.close()
        connection.close()


# after receiving a post request add it to database
@app.route('/accident', methods=['POST'])
def add_to_db():
    # print(request.json)
    if not request.json or 'Longitude' not in request.json or 'Latitude' not in request.json:
        abort(400)

    longitude = request.json['Longitude']
    latitude = request.json['Latitude']
    category = request.json['Category']
    req_vehicle_type = request.json['RequiredVehicle']
    time = request.json['Time']
    type = request.json['Type']

    mySql_insert_query = """INSERT INTO Accident (Longitude, Latitude, Category, RequiredVehicleType, Time, Type) 
                            VALUES 
                         (""" + str(longitude) + ", " + str(latitude) + ", " + category + ", " + \
                         req_vehicle_type + ", " + "STR_TO_DATE('" + time + "','%Y-%m-%d %H:%i:%s'), " + str(
        type) + ")"""
    print(mySql_insert_query)

    cursor = get_cursor()
    cursor.execute(mySql_insert_query)
    cursor.connection.commit()
    close_connection(cursor)

    return "Accident records were successfully inserted into the database"


# after receiving a post request add it to database
@app.route('/accidentNLP', methods=['POST'])
def add_nlp_to_db():
    # print(request.json)
    if not request.json or 'Longitude' not in request.json or 'Latitude' not in request.json:
        abort(400)

    longitude = request.json['Longitude']
    latitude = request.json['Latitude']
    # category = #tu bedzie metoda
    # req_vehicle_type = tu bedzie metoda
    time = str(datetime.now())
    # type = tu bedzie metoda
    transcript = request.json["Transcript"]

    mySql_insert_query = """INSERT INTO Accident (Longitude, Latitude, Category, RequiredVehicleType, Time, Type, Transcript) 
                            VALUES 
                         (""" + str(longitude) + ", " + str(latitude) + ", " + category + ", " + \
                         req_vehicle_type + ", " + "STR_TO_DATE('" + time + "','%Y-%m-%d %H:%i:%s'), " + str(type) + \
                         ", " + transcript + ")"""
    print(mySql_insert_query)

    cursor = get_cursor()
    cursor.execute(mySql_insert_query)
    cursor.connection.commit()
    close_connection(cursor)

    return "Accident records were successfully inserted into the database"


