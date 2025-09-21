import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from typing import List
from pydantic import BaseModel, Field


""" Assumptions """
consumption_rate = 1.2  # kWh/km
time_stoppage_at_nodes= 45 # driver takes break at each node except final destination
driving_cost_per_km = 0.05 # Driving cost per km

class State(BaseModel):
    currentTime: datetime = Field(default_factory=lambda: datetime(2025, 1, 1, 9, 0))
    currentLocation: str = ""
    currentBattery: int = 100
    totalCost: float = 0.0
    plan: List[str] = Field(default_factory=list) # A list of actions taken so far 

def pick_station_on_strategy(charging_stations, strategy= "time-optimal"):
    """ Pick strategy to select charging station to either minimize charging time or minmise cost of charging 
        Return the first row of the sorted charging stations DataFrame
    """
    if strategy == "time-optimal":
        charging_stations= charging_stations.sort_values(by="max_power_kW", ascending=False)
    elif strategy == "cost-optimal":
        charging_stations= charging_stations.sort_values(by="price_€/kWh", ascending=True)
    else:
        print("Unknown strategy, defaulting to time-optimal")
        charging_stations= charging_stations.sort_values(by="max_power_kW", ascending=False)
    return charging_stations.iloc[0]

def nearest_station(origin, distance_matrix, charging_stations, charging_station_in_path, truck_state, strategy="time-optimal"):
    # remove charging stations already in path
    charging_stations = charging_stations[~charging_stations['station_name'].isin(charging_station_in_path)]
    charging_stations['dist_to_origin'] = charging_stations['station_name'].apply(
        lambda x: distance_matrix.loc[origin, x]
    )
    # filter out stations that are at origin or unreachable given the current charge
    charging_stations = charging_stations[(charging_stations['dist_to_origin'] <= (truck_state.currentBattery / consumption_rate)) & (charging_stations['dist_to_origin'] > 0)]
    if charging_stations.empty:
        raise Exception("Infeasible route: No reachable charging stations available.")
    return pick_station_on_strategy(charging_stations, strategy)

def compute_schedule(distance_matrix: pd.DataFrame, 
                     charging_stations: pd.DataFrame, 
                     origin: str,
                     stops: List[str], tour: List, truck_spec) -> dict:
    """ Compute the schedule for the truck to visit all stops and return to origin
        distance_matrix: pd.DataFrame with distances between all points (including charging stations)
        charging_stations: pd.DataFrame with charging station details (latitude,longitude,max_power_kW,price_€/kWh,source)
        origin: starting point of the truck
        stops: list of stops to visit
        tour: ordered list of locations to visit (including origin and stops)
        truck_spec: dict with truck specifications (battery capacity, consumption rate, etc.)
    """
    charging_stations.rename(columns={"ID": "station_name"}, inplace=True)
    locations= [origin] + stops
    for row in charging_stations.itertuples():
        locations.append(row.station_name)
    charging_station_in_path = []
    time_matrix= distance_matrix / 80 * 60  # average speed 80 km/h
    battery_capacity = truck_spec['Battery_capacity_80%_kWh'] # charging to 80% only for battery health
    battery_min = truck_spec['Battery_capacity_kWh'] * 0.1  # 10% minimum battery
    truck_state= State()
    truck_state.plan.append({
                'action': 'Start',
                'from': "",
                'to': origin,
                'start': truck_state.currentTime.strftime("%H:%M"),
                'end': truck_state.currentTime.strftime("%H:%M"),
                'SOC_kWh': truck_state.currentBattery,
                'distance_km': 0,
                'cost_€': 0
            })
    for i in range(len(tour) - 1):
        origin = tour[i]
        truck_state.currentLocation = origin
        dest = tour[i + 1]

        # Distance and time
        dist = distance_matrix.loc[origin, dest]
        travel_time = time_matrix.loc[origin, dest]
        energy_needed = dist * consumption_rate
        leg_cost = dist * driving_cost_per_km

        # Battery check
        while truck_state.currentBattery - energy_needed < battery_min:
            # Pick nearest station
            station = nearest_station(origin, distance_matrix, charging_stations, charging_station_in_path, truck_state, strategy="time-optimal")
            charging_station_in_path.append(station['station_name'])
            detour_dist = distance_matrix.loc[origin, station['station_name']]
            detour_energy = detour_dist * consumption_rate
            detour_cost = detour_dist * driving_cost_per_km
            travel_time_to_charger = time_matrix.loc[origin, station['station_name']]

            # Drive to charger
            truck_state.plan.append({
                'action': 'drive_to_charger',
                'from': origin,
                'to': station['station_name'],
                'start': truck_state.currentTime.strftime("%H:%M"),
                'end': (truck_state.currentTime + timedelta(minutes=travel_time_to_charger)).strftime("%H:%M"),
                'SOC_kWh': truck_state.currentBattery - detour_energy,
                'distance_km': detour_dist,
                'cost_€': detour_cost
            })
            truck_state.currentBattery -= detour_energy
            truck_state.currentTime += timedelta(minutes=travel_time_to_charger)

            # Charging
            # TODO charges to full for simplicity. Adapt to need (check how much needed to reach next station or till end destination)
            charge_needed = battery_capacity - truck_state.currentBattery
            charge_time_min = (charge_needed / station['max_power_kW']) * 60
            charging_cost = charge_needed * station['price_€/kWh']
            truck_state.currentBattery = battery_capacity

            truck_state.plan.append({
                'action': 'charging',
                'from': station['station_name'],
                'to': station['station_name'],
                'start': truck_state.currentTime.strftime("%H:%M"),
                'end': (truck_state.currentTime + timedelta(minutes=charge_time_min)).strftime("%H:%M"),
                'SOC_kWh': truck_state.currentBattery,
                'distance_km': np.nan,
                'cost_€': charging_cost
            })
            truck_state.currentTime += timedelta(minutes=charge_time_min)
            origin = station['station_name']
            truck_state.currentLocation = origin
            energy_needed= distance_matrix.loc[origin, dest]* consumption_rate
    
        truck_state.plan.append({
            'action': 'drive_to_load/unload',
            'from': origin,
            'to': dest,
            'start': truck_state.currentTime.strftime("%H:%M"),
            'end': (truck_state.currentTime + timedelta(minutes=travel_time)).strftime("%H:%M"),
            'SOC_kWh': truck_state.currentBattery - energy_needed,
            'distance_km': dist,
            'cost_€': leg_cost
        })
        charging_station_in_path= [] # once the truck drives to a customer location, it can pick the same charging stations again
        truck_state.currentBattery -= energy_needed
        if dest== tour[-1]:  # if last destination, no need to add stoppage time
            truck_state.currentTime += timedelta(minutes=travel_time)
        else:
            truck_state.currentTime += timedelta(minutes=travel_time)+ timedelta(minutes=time_stoppage_at_nodes)
    return truck_state



if __name__ == "__main__":
    # Example usage
    distance_matrix = pd.DataFrame({
        'Ingolstadt': {'Ingolstadt': 0, 'Halle': 300, 'StationA': 50, 'StationB': 150},
        'Halle': {'Ingolstadt': 300, 'Halle': 0, 'StationA': 250, 'StationB': 100},
        'StationA': {'Ingolstadt': 50, 'Halle': 250, 'StationA': 0, 'StationB': 120},
        'StationB': {'Ingolstadt': 150, 'Halle': 100, 'StationA': 120, 'StationB': 0},
    })
    charging_stations = pd.DataFrame([
        {'ID': 'StationA', 'latitude': 48.5, 'longitude': 11.5, 'max_power_kW': 150, 'price_€/kWh': 0.30},
        {'ID': 'StationB', 'latitude': 49.0, 'longitude': 11.0, 'max_power_kW': 350, 'price_€/kWh': 0.40},
    ])
    truck_spec = {
        'Model': 'Mercedes eActros',
        'Battery_capacity_kWh': 400,
        'Battery_capacity_80%_kWh': 320,
        'Consumption_rate_kWh_per_km': consumption_rate,
        'Max_range_km': 320 / consumption_rate
    }
    plan = compute_schedule(distance_matrix, charging_stations, origin='Ingolstadt', stops=['Halle'], tour=['Ingolstadt', 'Halle', 'Ingolstadt'], truck_spec=truck_spec)
    for action in plan:
        print(action)