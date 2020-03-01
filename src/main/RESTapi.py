from flask import Flask, request
from flask_restful import Api, abort
import pymysql

app = Flask(__name__)
api = Api(app)
db_connect = pymysql.connect(host='127.0.0.1',
                                     database='AmbulanceDB',
                                     user='root',
                                     password='on@itsiriC_96')
cursor = db_connect.cursor()

print("MySQL connection is open")

# after receiving a post request add it to database
@app.route('/accident', methods=['POST'])
def add_to_db():
    # print(request.json)
    if not request.json or not 'Longitude' in request.json or not 'Latitude' in request.json:
        abort(400)

    longitude = request.json['Longitude']
    latitude = request.json['Latitude']
    category = request.json['Category']
    req_vehicle_type = request.json['RequiredVehicle']
    time = "NOW()"
    type = request.json['Type']

    mySql_insert_query = """INSERT INTO Accident (Longitude, Latitude, Category, RequiredVehicleType, Time, Type) 
                            VALUES 
                         (""" + str(longitude) + ", " + str(latitude) + ", " + category + ", " + \
                         req_vehicle_type + ", " + time + ", " + str(type) + ")"""

    cursor.execute(mySql_insert_query)
    db_connect.commit()
    # print(cursor.rowcount, "Accident record was successfully inserted into the database")

    return "Records added successfully into the database"


def close_connection():
    if db_connect.open:
        cursor.close()
        db_connect.close()
        print("MySQL connection is closed")
