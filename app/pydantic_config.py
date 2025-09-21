from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class RouteRequest(BaseModel):
    origin: str
    stops: List[str]
    start_time: str  # Format: "HH:MM"
    truck_model: str
    
class TruckModel(BaseModel):
    model: str
    battery_capacity: float  # kWh
    consumption_rate: float  # kWh/km
    max_range: float  # km


class RoutePoint(BaseModel):
    time: str
    location: str
    latitude: float
    longitude: float
    points: List[Any]   
    action: str
    duration: int
    SOC: int
    why: str

class RouteResponse(BaseModel):
    route: List[RoutePoint]  # Each dict contains time, location , lat, long, action, duration, SOC, distance
    total_distance: float  # in km
    total_duration: float  # in hours

sample_intermediate_response = {
    "route": [
        {
            "time": "08:00",
            "location": "Ingolstadt",
            "latitude": 48.766, 
            "longitude": 11.421,
            "points": [],
            "action": "drive",
            "duration": 0,
            "SOC": 100,
            "why": ""
        },
        {
            "time": "09:00",
            "location": "Charge Point 1",
            "latitude": 48.135,
            "longitude": 11.582,
            "points": [],
            "action": "charge/rest",
            "duration": 60,
            "SOC": 80,
            "why": "Needed to charge to reach next destination"
        },
        {
            "time": "09:30",
            "location": "Charge Point 1",
            "latitude": 48.135,
            "longitude": 11.582,
            "points": [],
            "action": "drive",
            "duration": 90,
            "SOC": 100,
            "why": ""
        },
        {
            "time": "10:00",
            "location": "Halle",
            "latitude": 51.4821667,
            "longitude": 11.9657958,
            "points": [],
            "action": "Load/Unload + charge/rest",
            "duration": 120,
            "SOC": 80,
            "why": "Loading/unloading + opportunistic charging"
        },
        {
            "time": "10:30",
            "location": "Halle",
            "latitude": 51.4821667,
            "longitude": 11.9657958,
            "points": [],
            "action": "drive",
            "duration": 150,
            "SOC": 80,
            "why": ""
        },
        {
            "time": "11:30",
            "location": "Ingolstadt",
            "latitude": 48.766, 
            "longitude": 11.421,
            "points": [],
            "action": "Load/Unload",
            "duration": 210,
            "SOC": 20,
            "why": "Final destination"
        },
    ],
    "total_distance": "",
    "total_duration": ""
}