# Build Instructions

## Database Creation
Since the project uses a localy created database, such database will first need to be created on the machine used

1. Download or/and install MySQL on the machine used.
   The link to mysql download page can be found here:
   [MySQL](https://dev.mysql.com/downloads/mysql/)
   
2. Start MySQL, making sure that MySQL instance status is running 
   (if runnng through terminal make sure that mysql has been installed here too)
   
3. Set the user and password used when creating MySQL database as enviorment variables.
   Set API_USER=user and API_PASSWORD=password

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

## Download Google gensim model
In order for the NaturalLanguageProcessor.py to work correctly, a Google gensim model needs to be added to the same directory (main)

1. Download the model from here [Google-gensim](https://github.com/mmihaltz/word2vec-GoogleNews-vectors)

2. unzip the model

3. add it to main folder


## Application running
This instruction 

1. Navigate to the ambulance directory, where the project was saved.

2. Run: `src/setup.py install` with python3 in order to download all packages used in the project

3. Run: `src/application.py` with python3 to start the application

There will be no accident or trip records in the database at this point. In order to send accident record a curl can be used. An example curl for adding an accident has been provided below:

```
curl --location --request POST '127.0.0.1:5000/accident' \
--header 'Content-Type: application/json' \
--data-raw '{"Longitude":"-0.086944", "Latitude":"51.5033", "Category":"'\''1'\''", "Login":"kcl", "Password":"pass", "Type":"11", "Casualties": "1"} 
'
```
In order to send an accident record that needs to be categorised longitude, latitude, credentials, casualities and transcript needs to be provided. An example curl has been provided below:
```
curl --location --request POST '127.0.0.1:5000/accidentNLP' \
--header 'Content-Type: application/json' \
--data-raw '{"Longitude":"-0.086944", "Latitude":"51.5033", "Login":"kcl", "Password":"pass", "Transcript": "O: Oklahoma City 911 C: Yeah, I just saw somebody have an accident on Memorial Road and Midwest Blvd. just south of the intersection. O: Memorial and Midwest just south? Do you know if there are injuries? C: I don'\''t know, I just saw it from about a quarter-mile away. I haven'\''t driven up on it yet. I am about to go do that..... It looked pretty bad, I'\''m gonna drive up on it now. It looks like an SUV, kind of a dark color SUV, black. O: Black SUV. What'\''s the other vehicle? C: It was a single vehicle accident. It looks like they just hit the side... it looks like a Tahoe and it looks pretty rough. The accident looks pretty bad. It looks like they hit the side of - do you know where the turnpike crosses over Midwest Blvd?- it looks like they hit that. The car looks like it might be on fire. O: Did they hit a barrier or what? C: They went under the... there'\''s an underpass on Midwest Blvd. that goes under the turnpike. It looks like they swerved and hit that. O: Let me know if you are able to tell how many people might be inside. What'\''s your name? C: My name is [removed]. O: You think the car is on fire? C: Yeah, I do see the car is on fire. O: Ok, we got a lot of help that way. C: Ok, you might definitely want to send an ambulance and a fire truck as well. O: Yeah, they are on the way. If you find out that maybe there are several injured, like needing more than one ambulance, call us right back, ok? And pull your vehicle safely out of the way, right? C: Yeah, I'\''m off the side of the road. O: Ok, thank you."} 
'
```
Accident that needed categorisation will not be processed until confirmation is sent. In order to send a confirmation a curl with the accident id and status should be sent. Accident id must match one existing in the database. An example curl has been provided below:
```
curl --location --request POST '127.0.0.1:5000/confirmation' \
--header 'Content-Type: application/json' \
--data-raw '{"status":"ok", "Login":"kcl", "Password":"pass", "accident_id":"1"}
'
```

In order to confirm trip end Trip_id, longitude, latitude and credentials need to be provided. Below an example curl has been provided. Trip_id needs to be replaced with a valid Trip_id from the database. 

```
curl --location --request POST '127.0.0.1:5000/tripdone' \
--header 'Content-Type: application/json' \
--data-raw '{"Longitude":"-0.0702572", "Latitude":"51.4916", "Login":"kcl", "Password":"pass", "Trip_id":"1"}
' 
```

## (Simulator Running - Optional)

In order to run the simulator using the automatically generated accident records which were based on statistical data, the following can be done. The first two steps are the same as in the case of running the application:

1. Navigate to the ambulance directory, where the project was saved.

2. Run: `src/setup.py install` with python3 in order to download all packages used in the project

3. Run: `src/simulator.py` with python3 to start the application

