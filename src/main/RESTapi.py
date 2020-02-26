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


@app.route('/accident', methods=['POST'])
def add_to_db():
    print(request.json)
    if not request.json or not 'Longitude' in request.json or not 'Latitude' in request.json:
        abort(400)

    accident_id = request.json['AccidentId']
    longitude = request.json['Longitude']
    latitude = request.json['Latitude']
    category = request.json['Category']
    req_vehicle_type = request.json['RequiredVehicle']
    time = "NOW()"
    type = request.json['Type']

    mySql_insert_query = """INSERT INTO Accident (AccidentId, Longitude, Latitude, Category, RequiredVehicleType, TimeS, Type) 
                            VALUES 
                         (""" + accident_id + ", " + longitude + ", " + latitude + ", " + category + ", " + \
                         req_vehicle_type + ", " + time + ", " + type + ")"

    cursor.execute(mySql_insert_query)
    db_connect.commit()
    print(cursor.rowcount, "Accident record was successfully inserted into the database")
    cursor.close()

    return "added successfully"


def main():
    app.run(port='5002')

    if db_connect.open:
        cursor.close()
        db_connect.close()
        print("MySQL connection is closed")


if __name__ == "__main__":
    main()
