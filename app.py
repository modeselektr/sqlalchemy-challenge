import numpy as np
import pandas as pd
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify

engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# We can view all of the classes that automap found
Base.classes.keys()

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#weather app
app = Flask(__name__)

maxDate = session.query(
    func.max(func.strftime("%Y-%m-%d", Measurement.date))).all()
tempValMaxDate = list(np.ravel(maxDate))[0]
tempValMaxDate = dt.datetime.strptime(tempValMaxDate, '%Y-%m-%d')

minDate = session.query(
    func.min(func.strftime("%Y-%m-%d", Measurement.date))).all()
tempValMinDate = list(np.ravel(minDate))[0]
tempValMinDate = dt.datetime.strptime(tempValMinDate, '%Y-%m-%d')

yearAgo = tempValMaxDate - dt.timedelta(days=365)

stations = (session.query(Measurement.station, func.count(Measurement.station))
            .group_by(Measurement.station)
            .order_by(func.count(Measurement.station).desc())
            .all())

stationID = stations[0][0]


session.close()


@app.route("/")
def home():
    return (f"*** Welcome to Hawaii's Climate Data! *** <br>"
            f"Available Routes: <br>"
            f"***************************************<br>"
            f"/api/v1.0/stations <br>"
            f"/api/v1.0/precipitation <br>"
            f"/api/v1.0/temperature <br>"
            f"/api/v1.0/* <br>"
            f"/api/v1.0/*/* <br>"
            f"***************************************<br>"
            f"* - Please enter a date in <br>  YYYY-MM-DD format for the 4th and 5th options!<br>"
            f"For example /api/v1.0/2016-08-26/2016-08-30<br>"
            )


@app.route("/api/v1.0/stations")
def station():
    session = Session(engine)
    results = session.query(Station.station).all()
    session.close()

    all_stations = list(np.ravel(results))
    return jsonify(all_stations)


@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)
    results = (session.query(Measurement.date, Measurement.prcp)
                      .filter(Measurement.date > yearAgo)
                      .group_by(Measurement.date)
                      .order_by(Measurement.date)
                      .all())

    session.close()

    precipDict = {}
    for result in results:
        precipDict.update({result.date: result.prcp})

    return jsonify(precipDict)


@app.route("/api/v1.0/temperature")
def temperature():
    session = Session(engine)
    results = (session.query(Measurement.date, Measurement.tobs, Measurement.station)
                      .filter(Measurement.station == stationID)
                      .filter(Measurement.date > yearAgo)
                      .group_by(Measurement.date)
                      .order_by(Measurement.date)
                      .all())

    session.close()

    tempList = []
    for result in results:
        tempDict = {result.date: result.tobs, "Station": result.station}
        tempList.append(tempDict)

    return jsonify(tempList)


@app.route("/api/v1.0/<start>")
def start(start):
    tempValMaxDate2 = str(tempValMaxDate)
    tempValMinDate2 = str(tempValMinDate)

    if(start <= tempValMinDate2) | (start > tempValMaxDate2):
        return(f"Please choose a different date, between {minDate} and {maxDate}")

    session = Session(engine)
    select = [Measurement.date, func.min(Measurement.tobs), func.avg(
        Measurement.tobs), func.max(Measurement.tobs)]

    results = (session.query(*select)
               .filter(func.strftime("%Y-%m-%d", Measurement.date) >= start)
               .group_by(Measurement.date)
               .all())

    session.close()

    dates = []
    for result in results:
        date_dict = {}
        date_dict["Date"] = result[0]
        date_dict["Low Temp"] = result[1]
        date_dict["Avg Temp"] = result[2]
        date_dict["High Temp"] = result[3]
        dates.append(date_dict)
    return jsonify(dates)


@app.route('/api/v1.0/<start>/<end>')
def startEnd(start, end):

    tempValMaxDate2 = str(tempValMaxDate)
    tempValMinDate2 = str(tempValMinDate)

    if(start >= end):
        return (f"Beginning and End Date Mismatch:")
    if(start <= tempValMinDate2) | (end > tempValMaxDate2):
        return(f"Please choose a different date, between {minDate} and {maxDate}")

    session = Session(engine)
    select = [func.min(Measurement.tobs), func.max(
        Measurement.tobs), func.avg(Measurement.tobs)]

    results = (session.query(*select)
               .filter(func.strftime("%Y-%m-%d", Measurement.date) >= start)
               .filter(func.strftime("%Y-%m-%d", Measurement.date) <= end)
               #.group_by(Measurement.date)
               .all())

    session.close()

    something = list(np.ravel(results))
    return jsonify(something)


if __name__ == '__main__':
    app.run(debug=True)
