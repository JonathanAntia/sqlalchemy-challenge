import numpy as np
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify
import datetime as dt

# create an app and pass __name__ to it
app = Flask(__name__)

# database setup
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect the existing database into a new model
Base = automap_base()

# reflect tables
Base.prepare(engine, reflect=True)

# save reference to tables
Measurement = Base.classes.measurement
Station = Base.classes.station

# Flask routes
@ app.route("/")
def homepage ():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<end>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    # create a session link from Python to the database
    session = Session(engine)

    # Design a query to retrieve the last 12 months of precipitation data and plot the results
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()

    most_recent_date = most_recent_date[0].split("-") # split the tuple into a list
    most_recent_year = int(most_recent_date[0]) # extract elements from the list as integers
    most_recent_month = int(most_recent_date[1])
    most_recent_day = int(most_recent_date[2])

    # Calculate the date 1 year ago from the last data point in the database
    one_year_ago = dt.date(most_recent_year,most_recent_month,most_recent_day) - dt.timedelta(days=365)

    # Perform a query to retrieve the data and precipitation scores
    latest_y_prcp = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date>one_year_ago).all()

    # close the session
    session.close()

    # create a dictionary from the precipitation data using date as the key and precipitation as the values
    def Convert(tup, di): 
        for a, b in tup: 
            di.setdefault(a, []).append(b) 
        return di 

    dictionary = {} 
    return jsonify(Convert(latest_y_prcp, dictionary)) 

@app.route("/api/v1.0/stations")
def stations():
    # create a session link from Python to the database
    session = Session(engine)

    # design a query to retrieve the names of all stations in the database
    stations = session.query(Station.station, Station.name).all()

    # close the session
    session.close()

    return jsonify(stations)

@app.route("/api/v1.0/tobs")
def most_active_stations():

    # create a session link from Python to the database
    session = Session(engine)

    # design a query to indentify the most active station in the database
    station_activity = session.query(Measurement.station,func.count(Measurement.station)).\
                            group_by(Measurement.station).\
                            order_by(func.count(Measurement.station).desc())
    most_active_station = station_activity.first()[0]

    # calculate the date 1 year ago from the last data point in the database
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()

    most_recent_date = most_recent_date[0].split("-") # split the tuple into a list
    most_recent_year = int(most_recent_date[0]) # extract elements from the list as integers
    most_recent_month = int(most_recent_date[1])
    most_recent_day = int(most_recent_date[2])

    one_year_ago = dt.date(most_recent_year,most_recent_month,most_recent_day) - dt.timedelta(days=365)

    # design a query to retrieve all the temperatures associated with that station
    temp_active_station = session.query(Measurement.tobs).\
                            filter(Measurement.station == most_active_station).\
                            filter(Measurement.date > one_year_ago).all()

    
    # close the session
    session.close()

    temp_active_station = list(np.ravel(temp_active_station))

    return jsonify(temp_active_station)

if __name__ == '__main__':
    app.run(debug=True)