import math
import pandas as pd
import json
from datetime import datetime
import numpy as np
from app.pydantic_config import RouteResponse


def validate_input(origin, stop, truck_model, start_time):
    """ 1. Validate if input parameters are valid as per the city and truck model specifications
        2. Return the city choices, truck specifications and combined charge points datasets
    """
    city_choices= json.load(open("./data/city_choices.json"))
    if origin not in city_choices.keys() or stop not in city_choices.keys():
        print("Invalid city choice. Please choose from the available cities.")
        raise ValueError("Invalid city choice. Please choose from the available cities.")
    truck_spec = json.load(open("./data/truck_specs.json"))

    combined_charge_points = pd.read_csv("./data/combined_charge_points.csv")
    truck_model = truck_spec[truck_model]

    today_date = datetime.now().date()
    start_time = pd.to_datetime(f"{today_date} {start_time}", format="%Y-%m-%d %H:%M")
    return origin, stop, truck_model, start_time, city_choices, combined_charge_points

def haversine(lat1, lon1, lat2, lon2):
    """ haversine formula """
    # distance between latitudes and longitudes
    dLat = (lat2 - lat1) * math.pi / 180.0
    dLon = (lon2 - lon1) * math.pi / 180.0

    # convert to radians
    lat1 = (lat1) * math.pi / 180.0
    lat2 = (lat2) * math.pi / 180.0

    # apply formulae
    a = (pow(math.sin(dLat / 2), 2) + 
         pow(math.sin(dLon / 2), 2) * 
             math.cos(lat1) * math.cos(lat2))
    rad = 6371
    c = 2 * math.asin(math.sqrt(a))
    return rad * c

def filter_stations(origins, df, max_distance):
    """
    Filter stations within `max_distance` km of any origin based on haversine distance. 
    """
    filtered_stations = []

    for index, row in df.iterrows():
        station_lat, station_lon = row["latitude"], row["longitude"]

        # Check against all origins
        for origin in origins:
            o_lat = origin["point"]["latitude"]
            o_lon = origin["point"]["longitude"]
            distance = haversine(o_lat, o_lon, station_lat, station_lon)

            if distance <= max_distance:
                filtered_stations.append(row)
                break  # No need to check other origins for this station

    return pd.DataFrame(filtered_stations).reset_index(drop=True)

def create_matrix_new(matrix, origin, stop, filtered_station_df):
    """ Matrix (list of lists) having distances mapped into a dataframe with origin, stop and filtered stations as index and columns
    """
    num_origins = len(matrix)
    num_destinations = len(matrix[0])
    distance_matrix = [[None for _ in range(num_destinations)] for _ in range(num_origins)]
    # Populate the matrix with the response data
    for i in range(num_origins):    
        for j in range(num_destinations):
            distance_matrix[i][j] = matrix[i][j]       

    return pd.DataFrame(distance_matrix, index=[origin, stop] + [int(row['ID']) for _, row in filtered_station_df.iterrows()], 
                        columns=[origin, stop] + [int(row['ID']) for _, row in filtered_station_df.iterrows()])

async def input_from_user(origin, stop, city_choices, combined_charge_points, truck_model):
    """ 1. Filter stations within truck range
        2. Create distance matrix with origin, stop and filtered stations based on haversine distance
    """ 
    # Combine stop time with today's date
    origins= []
    origins.append({
        "point": {  "latitude": city_choices[origin][0], "longitude": city_choices[origin][1]}
    })
    origins.append({
        "point": {  "latitude": city_choices[stop][0], "longitude": city_choices[stop][1]}
    })

    # Combine stop time with today's date
    destinations= []
    destinations.append({
        "point": {  "latitude": city_choices[origin][0], "longitude": city_choices[origin][1]}
    })
    destinations.append({
        "point": {  "latitude": city_choices[stop][0], "longitude": city_choices[stop][1]}
    })

    # filter stations within truck range
    combined_charge_points= filter_stations(origins, combined_charge_points, max_distance=truck_model["Range_80%_km"])

    for index, row in combined_charge_points.iterrows():
        origins.append({
            "point": {
                "latitude": row["latitude"],
                "longitude": row["longitude"]
            }
        })
        destinations.append({
            "point": {
                "latitude": row["latitude"],
                "longitude": row["longitude"]
            }
        })

    origins_input = [(o["point"]["latitude"], o["point"]["longitude"]) for o in origins]
    destinations_input = [(d["point"]["latitude"], d["point"]["longitude"]) for d in destinations]

    # compute haversine distance between origins and destinations
    matrix = []
    for o_lat, o_lon in origins_input:
        row = []
        for d_lat, d_lon in destinations_input:
            row.append(haversine(o_lat, o_lon, d_lat, d_lon))
        matrix.append(row)
    
    df_dist = create_matrix_new(matrix, origin, stop, combined_charge_points)
    return df_dist, combined_charge_points


def parse_duration(start, end):
    """Convert HH:MM start/end to duration in minutes"""
    fmt = "%H:%M"
    t1, t2 = datetime.strptime(start, fmt), datetime.strptime(end, fmt)
    return int((t2 - t1).total_seconds() // 60)


def transform(raw_data, city_choices, combined_charge_points) -> RouteResponse:
    """ Transform raw_data from compute_schedule to RouteResponse format
    """
    route = []
    for step in raw_data:
        station = combined_charge_points[combined_charge_points["ID"] == step["to"]]
        if station.empty:
            # if the current step is at a customer stop
            lat, lon = city_choices.get(step["to"], (None, None))
        else:
            # if the current step is at a charging station
            lat = station.iloc[0]["latitude"]
            lon = station.iloc[0]["longitude"]
        route.append(
            {
                "time": step["start"],
                "location": str(step["to"]),  # you may map ID → station name/coords
                "latitude": lat,             # fill from station lookup if available
                "longitude": lon,
                "points": [],
                "action": step["action"],
                "duration": parse_duration(step["start"], step["end"]),
                "SOC": round((step["SOC_kWh"])),
                "why": "",  # optionally add explainable logic
            }
        )
    return {
        "route": route,
        "total_distance": 0,
        "total_duration": 0,
    }

if __name__ == "__main__":

    df= pd.read_csv("./data/combined_charge_points.csv")
    df["price_€/kWh"] = (
    df["price_€/kWh"]
    .str.replace("€", "", regex=False)   # remove euro symbol
    .astype(float))                    # convert to float
    df.to_csv("./data/combined_charge_points.csv", index=False)