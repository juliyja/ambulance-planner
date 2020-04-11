import re
import hashlib

from flask import Flask, request
from flask_restful import Api, abort

from main.DatabaseUtil import get_cursor, close_connection
from main.NaturalLanguageProcessor import categorize_accident

app = Flask(__name__)
api = Api(app)


# after receiving a post request add it to database
@app.route('/accident', methods=['POST'])
def add_to_db():

    cursor, user_exist = verify_user()
    if user_exist:
        return "Wrong password, please make sure that the credentials you entered are correct"

    # print(request.json)
    if not request.json or 'Longitude' not in request.json or 'Latitude' not in request.json:
        abort(400)

    longitude = request.json['Longitude']
    latitude = request.json['Latitude']
    category = request.json['Category']
    type = request.json['Type']
    time = request.json['Time']

    mySql_insert_query = """INSERT INTO Accident (Longitude, Latitude, Category, Time, Type) 
                            VALUES 
                         (""" + str(longitude) + ", " + str(latitude) + ", " + category + ", " + \
                         "STR_TO_DATE('" + time + "','%Y-%m-%d %H:%i:%s'), " + str(
        type) + ")"""
    print(mySql_insert_query)
    cursor.execute(mySql_insert_query)
    cursor.execute("SELECT LAST_INSERT_ID()")
    accident_id = cursor.fetchone()[0]
    cursor.connection.commit()
    close_connection(cursor)

    return "Accident record successfully inserted into the database with id: " + str(accident_id)


# after receiving a post request add it to database
@app.route('/accidentNLP', methods=['POST'])
def add_nlp_to_db():
    # print(request.json)

    cursor, user_exist = verify_user()
    if user_exist:
        return "Wrong password, please make sure that the credentials you entered are correct"

    if not request.json or 'Longitude' not in request.json or 'Latitude' not in request.json:
        abort(400)

    longitude = request.json['Longitude']
    latitude = request.json['Latitude']
    transcript = request.json['Transcript']
    transcript = re.sub(r'\"', '', transcript)
    print(transcript)
    type, category, req_transport_type = categorize_accident(transcript)
    time = request.json['Time']

    mySql_insert_query = """INSERT INTO Accident (Longitude, Latitude, Category, Time, Type, TRANSCRIPT) 
                            VALUES 
                         (""" + str(longitude) + ", " + str(latitude) + ", " + str(
        category) + ", " + "STR_TO_DATE('" + time + "','%Y-%m-%d %H:%i:%s'), \"" + str(req_transport_type) + \
                         "\", \"" + transcript + "\")"""
    print(mySql_insert_query)

    cursor.execute(mySql_insert_query)
    cursor.execute("SELECT LAST_INSERT_ID()")
    accident_id = cursor.fetchone()[0]
    cursor.connection.commit()
    close_connection(cursor)

    return "Accident record successfully inserted into the database with id: " + str(accident_id)


# TODO: make this do anything, right now it does nothing
@app.route('/confirmation', methods=['POST'])
def send_confirmation():
    status = request.json["status"]
    accident_id = request.json["accident_id"]
    if status == 'ok':
        print("Accident information has been approved")
    return "Accident records were successfully inserted into the database"


def verify_user():
    cursor = get_cursor()
    login = request.json["Login"]
    password = request.json["Password"]
    password = password.encode('utf-8')
    hash_password = hashlib.sha3_256(password).hexdigest()
    mysql_check_password_query = "SELECT * FROM USERS WHERE LOGIN = \'" + login + "\' AND HASH = \'" + hash_password + "\';"
    cursor.execute(mysql_check_password_query)
    rows = cursor.fetchall()
    user_exist = len(rows) != 1
    return cursor, user_exist
