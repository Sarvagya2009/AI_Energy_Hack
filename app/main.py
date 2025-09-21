import json
import pandas as pd
import httpx
import asyncio
from app.Matrix_data_process import filter_stations, validate_input, haversine, create_matrix_new, transform
from app.config import route_tomtom_post, tomtom_key
from fastapi import FastAPI
from app.pydantic_config import RouteRequest, TruckModel, RouteResponse, sample_intermediate_response
from app.brain import compute_schedule

app = FastAPI(title="AI E-Truck Dispatcher", description="API for e-truck route optimization")

def get_route(origin, destination):
    url = route_tomtom_post.format(location=f"{origin}:{destination}", key=tomtom_key)
    headers = {
    "accept": "*/*",
    "Content-Type": "application/json",
    }
    with httpx.Client() as client:
        response = client.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()["routes"][0]
            return data["legs"][0]["summary"], data["legs"][0]["points"]
        else:
            print(f"Failed to fetch route. Status code: {response}")
            return None

@app.post("/optimize-route", response_model=RouteResponse)
async def optimize_route(request: RouteRequest) -> RouteResponse:
    print("Received request: ", request)
    origin = request.origin
    stops = request.stops
    start_time = request.start_time
    truck_model = request.truck_model

    # step 1. call matrix api
    origin, stop, truck_model, start_time, city_choices, combined_charge_points = validate_input(origin, stops[0], truck_model, start_time)
    distance_matrix, charging_stations = await input_from_user(origin, stop, city_choices, combined_charge_points)
    
    # step 2. call waypoint api for TSP 


    # step 3. call our algo for schedule 
    truck_state= compute_schedule(distance_matrix, charging_stations, origin, stops, tour= [origin]+ stops + [origin], truck_spec=truck_model)
    df=pd.DataFrame(truck_state.plan)
    df.to_csv("Halle-ZufenHausen.csv", index=False)
    brain_response= (transform(raw_data=truck_state.plan, city_choices=city_choices, combined_charge_points=combined_charge_points))
    # For now, return the sample intermediate response
    total_distance = 0
    total_duration = 0
    for ind,sample in enumerate(brain_response["route"]):
        # get lat and long from each stop if previous element does not have the same lat and long (sample_intermediate_response do not have a prev_lat and prev_long key)
        if ind == 0:
            continue
        if (sample["latitude"] != brain_response["route"][ind-1]["latitude"] or sample["longitude"] != brain_response["route"][ind-1]["longitude"]):
            origin= f"{brain_response['route'][ind-1]['latitude']},{brain_response['route'][ind-1]['longitude']}"
            destination= f"{sample['latitude']},{sample['longitude']}"
            summary, points= (get_route(origin, destination))
            total_distance += summary["lengthInMeters"]
            total_duration += summary["travelTimeInSeconds"]
            sample["points"]= points
    return RouteResponse(
        route=brain_response["route"],
        total_distance= total_distance/1000,  # convert to km
        total_duration= total_duration/3600  # convert to hours
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "AI E-Truck Dispatcher API is running"}

async def input_from_user(origin, stop, city_choices, combined_charge_points):
        
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
    combined_charge_points= filter_stations(origins, combined_charge_points, max_distance=320)
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

    matrix = []
    for o_lat, o_lon in origins_input:
        row = []
        for d_lat, d_lon in destinations_input:
            row.append(haversine(o_lat, o_lon, d_lat, d_lon))
        matrix.append(row)
    df_dist = create_matrix_new(matrix, origin, stop, combined_charge_points)
    return df_dist, combined_charge_points
    