import dotenv
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, "api_key.env")

dotenv.load_dotenv(env_path)
tomtom_key = os.getenv("TOMTOM_KEY")

# tom tom routing api to create routes between two points for truck
route_tomtom_post= "https://api.tomtom.com/routing/1/calculateRoute/{location}/json?key={key}&travelMode=truck"
