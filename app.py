import numpy as np
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify
import datetime as dt
from datetime import datetime

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
        f"Welcome to the Hawaiian Climate API<br/>"
        f"<br/>"
        f"Available Routes:<br/>"
        f"<br/>"
        f"1) Precipitation data for last year:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"<br/>"
        f"2) List of weather stations:<br/>"
        f"/api/v1.0/stations<br/>"
        f"<br/>"
        f"3) Temperatures recorded last year:<br/>"
        f"/api/v1.0/tobs<br/>"
        f"<br/>"
        f"4) Temperature stats from a start date (yyyy-mm-dd):<br/>"
        f"/api/v1.0/start_date<br/>"
        f"example for December 1st: /api/v1.0/2010-12-01<br/>"
        f"<br/>"
        f"5) Temperature stats from a start to end date (yyyy-mm-dd to yyyy-mm-dd):<br/>"
        f"/api/v1.0/start_date/end_date<br/>"
        f"example for December 1st to 16th: /api/v1.0/2010-12-01/2012-12-16"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    # create a session link from Python to the database
    session = Session(engine)

    # Design a query to retrieve the last 12 months of precipitation data and plot the results
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    most_recent_date = dt.datetime.strptime(most_recent_date[0], '%Y-%m-%d').date()

    # Calculate the date 1 year ago from the last data point in the database
    one_year_ago = dt.date(most_recent_date.year,most_recent_date.month,most_recent_date.day) - dt.timedelta(days=365)

    # Perform a query to retrieve the data and precipitation scores
    latest_y_prcp = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date>=one_year_ago).all()

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
    stations = session.query(Station.name).all()

    # close the session
    session.close()

    stations = list(np.ravel(stations))

    return jsonify(stations)

@app.route("/api/v1.0/tobs")
def most_active_stations():

    # create a session link from Python to the database
    session = Session(engine)

    # design a query to indentify the most active station in the database
    sel = [Measurement.station,Station.name,func.count(Measurement.station)]
    station_activity = session.query(*sel).\
                            filter(Station.station == Measurement.station).\
                            group_by(Measurement.station).\
                            order_by(func.count(Measurement.station).desc())
    most_active_station = station_activity.first()[0]

    # calculate the date 1 year ago from the last data point in the database
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    most_recent_date = dt.datetime.strptime(most_recent_date[0], '%Y-%m-%d').date()

    one_year_ago = dt.date(most_recent_date.year,most_recent_date.month,most_recent_date.day) - dt.timedelta(days=365)

    # design a query to retrieve all the temperatures associated with that station
    temp_active_station = session.query(Measurement.tobs).\
                            filter(Measurement.station == most_active_station).\
                            filter(Measurement.date >= one_year_ago).all()

    # close the session
    session.close()

    temp_active_station = list(np.ravel(temp_active_station))

    return jsonify(temp_active_station)

@app.route("/api/v1.0/<start>")
def start_date(start):
    # generate an error message if the wrong date format is entered by the user
    try:
        search_start_date = dt.datetime.strptime(start,'%Y-%m-%d').date()
    except:
        return jsonify('incorrect date format, please use yyyy-mm-dd')

    # create a session link from Python to the database
    session = Session(engine)

    # fetch the most recent date in the database
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    most_recent_date = dt.datetime.strptime(most_recent_date[0], '%Y-%m-%d').date()

    # fetch the earliest date in the database
    earliest_date = session.query(Measurement.date).order_by(Measurement.date.asc()).first()
    earliest_date = dt.datetime.strptime(earliest_date[0], '%Y-%m-%d').date()

    # generate a message if the user date is not in the database
    if search_start_date < earliest_date or search_start_date > most_recent_date:
        return jsonify({"error": f"the input date ({start}) is outside the available date ranges {earliest_date} to {most_recent_date}"}), 404

    # design a query to fetch temperature stats from start date and calculate TMIN, TAVG, and TMAX
    selection = [func.min(Measurement.tobs),func.avg(Measurement.tobs),func.max(Measurement.tobs)]
    temps_since_start = session.query(*selection).\
                            filter(Measurement.date >= search_start_date).all()
    
    # close session
    session.close()

    min_temp = temps_since_start[0][0]
    avg_temp = temps_since_start[0][1]
    max_temp = temps_since_start[0][2]

    temp_dict = {'since':search_start_date, "min_temp":min_temp, "avg_temp":avg_temp, "max_temp":max_temp}

    return jsonify(temp_dict)

@app.route("/api/v1.0/<start>/<end>")
def date_range(start,end):
    # generate an error message if the wrong date format is entered by the user
    try:
        search_start_date = dt.datetime.strptime(start,'%Y-%m-%d').date()
        search_end_date = dt.datetime.strptime(end,'%Y-%m-%d').date()
    except:
        return jsonify('incorrect date format, please use yyyy-mm-dd')

    # create a session link from Python to the database
    session = Session(engine)

    # fetch the most recent date in the database
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    most_recent_date = dt.datetime.strptime(most_recent_date[0], '%Y-%m-%d').date()

    # fetch the earliest date in the database
    earliest_date = session.query(Measurement.date).order_by(Measurement.date.asc()).first()
    earliest_date = dt.datetime.strptime(earliest_date[0], '%Y-%m-%d').date()

    # generate a message if the user date range is not in the database
    if search_start_date < earliest_date or search_end_date > most_recent_date:
        return jsonify({"error": f"date range {start} to {end} is outside the available date ranges {earliest_date} to {most_recent_date}"}), 404

    # design a query to fetch temperature stats from date range and calculate TMIN, TAVG, and TMAX
    selection = [func.min(Measurement.tobs),func.avg(Measurement.tobs),func.max(Measurement.tobs)]
    temps_in_date_range = session.query(*selection).\
                            filter(Measurement.date >= search_start_date).\
                            filter(Measurement.date <= search_end_date).all()
    
    # close session
    session.close()
    
    min_temp = temps_in_date_range[0][0]
    avg_temp = temps_in_date_range[0][1]
    max_temp = temps_in_date_range[0][2]

    temp_dict = {'from':search_start_date,"to":search_end_date, "min_temp":min_temp, "avg_temp":avg_temp, "max_temp":max_temp}
    
    return jsonify(temp_dict)

if __name__ == '__main__':
    app.run(debug=True)