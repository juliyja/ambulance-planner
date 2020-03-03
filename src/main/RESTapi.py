from flask import Flask, request
from flask_restful import Api, abort
import pymysql

from main.DatabaseUtil import get_cursor, close_connection

app = Flask(__name__)
api = Api(app)


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
                         req_vehicle_type + ", " + "STR_TO_DATE('" + time + "','%Y-%m-%d %H:%i:%s'), " + str(type) + ")"""
    print(mySql_insert_query)

    cursor = get_cursor()
    cursor.execute(mySql_insert_query)
    cursor.connection.commit()
    close_connection(cursor)

    return "Accident records were successfully inserted into the database"

