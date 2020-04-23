# Build Instructions

## Database Creation
Since the project uses a localy created database, such database will first need to be created on the machine used

1. Download or/and install MySQL on the machine used.
   The link to mysql download page can be found here:
   [MySQL](https://dev.mysql.com/downloads/mysql/)
   
2. Start MySQL, making sure that MySQL instance status is running 
   (if runnng through terminal make sure that mysql has been installed here too)
   
3. Set the user in password used for MySQL database

4. Recreate database on the local MySQL server using the the scripts located in the following files
   in the order they have been listed below:

* CREATE_DATABASE.sql
* ambulanceDB_ACCIDENT.sql
* ambulanceDB_TRANSPORT_TYPE_FLAG.sql
* ambulanceDB_TRANSPORT_TYPE_MAPPING.sql
* ambulanceDB_KEYWORD.sql
* ambulanceDB_ACCIDENT_TYPE.sql
* ambulanceDB_ACCIDENT_CATEGORY.sql
* ambulanceDB_AMBULANCE.sql
* ambulanceDB_HOSPITAL.sql
* ambulanceDB_USERS.sql

## Application running
This instruction 

1. Navigate to the ambulance directory, wherever it was saved on your machine

2. Run: `src/setup.py install` with python3 in order to download all packages used in the project
   the version of setuptools

3. Run: `src/application.py`with python3 to start the application

There will be no accident or trip records in the database at this point. In order to send accident record a curl can be used. An example curl for adding an accident has been provided below:

curl --location --request POST 'localhost:5000/accident' \
--header 'Content-Type: application/json' \
--data-raw '{"Longitude":"-0.086944", "Latitude":"51.5033", "Category":"'\''1'\''", "Login":"kcl", "Password":"pass", "Type":"11", "Casualties": "1"} 
'
####################
In order to confirm trip end Trip_id, longitudae, latitude and credentials need to be provided. Below an example curl has been provided. Trip_id needs to be replaced with a valid Trip_id from the database. 

curl --location --request POST 'localhost:5000/tripdone' \
--header 'Content-Type: application/json' \
--data-raw '{"Longitude":"-0.0702572", "Latitude":"51.4916", "Login":"kcl", "Password":"pass", "Trip_id":"1"}
' 

## (Simulator Running - Optional)
