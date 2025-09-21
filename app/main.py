import json
import pandas as pd
import httpx
import asyncio
from app.Matrix_data_process import validate_input, input_from_user, transform
from app.config import route_tomtom_post, tomtom_key
from fastapi import FastAPI
from app.pydantic_config import RouteRequest, TruckModel, RouteResponse, sample_intermediate_response
from app.brain import compute_schedule

app = FastAPI(title="AI E-Truck Dispatcher", description="API for e-truck route optimization")

def get_route(origin, destination):
    """ Get route details between origin and destination using TomTom Routing API
    """
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
    """ Endpoint to optimize the route for an electric truck given origin, stops, truck model, and start time
    """
    print("Received request: ", request)
    origin = request.origin
    stops = request.stops
    start_time = request.start_time
    truck_model = request.truck_model

    # step 1. calculate approximate distance between origin, stops and filter charging stations within truck range using haversine distance
    origin, stop, truck_model, start_time, city_choices, combined_charge_points = validate_input(origin, stops[0], truck_model, start_time)
    distance_matrix, charging_stations = await input_from_user(origin, stop, city_choices, combined_charge_points, truck_model)

    # step 2. call waypoint api for TSP
    # TODO calculate a simple TSP route between input origins and stops if there is more than 1 stop. (Otherwise route is origin -> stop -> origin)
    tour= [origin]+ stops + [origin]

    # step 3. call our algo for schedule 
    scheduled_truck_state= compute_schedule(distance_matrix, charging_stations, origin, stops, tour= tour, truck_spec=truck_model)
    # df=pd.DataFrame(scheduled_truck_state.plan)
    # df.to_csv("Fahr Plan.csv", index=False)
    brain_response= transform(raw_data=scheduled_truck_state.plan, city_choices=city_choices, combined_charge_points=combined_charge_points)
    total_distance = 0
    total_duration = 0
    for ind,sample in enumerate(brain_response["route"]):
        # if previous element does not have the same lat and long, compute points of fastest route between the 2 elements and populate "points"
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