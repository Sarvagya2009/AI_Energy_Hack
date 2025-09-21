
import requests
import json

# Test request payload
test_request = {
    "origin": "Halle",
    "stops": ["Zuffenhausen"],
    "start_time": "08:00",
    "truck_model": "Mercedes eActros",
}

def test_api():
    """Test the FastAPI endpoint"""
    url = "http://localhost:8000/optimize-route"

    try:
        response = requests.post(url, json=test_request)

        if response.status_code == 200:
            result = response.json()

            # Extract key metrics
            print(f"\nRoute Summary:")
            print(result["route"])
            print(f"Total Distance: {result['total_distance']} km")
            print(f"Total Time: {result['total_duration']} hours")
            #print(f"Number of Steps: {len(result['steps'])}")

        else:
            print(f"Error: {response.status_code}")
            print(response.text)

    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API. Make sure the FastAPI server is running.")
        print("Run: uvicorn main:app --reload")

if __name__ == "__main__":
    test_api()
