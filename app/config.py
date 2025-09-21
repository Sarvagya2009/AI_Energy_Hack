import dotenv
import os

dotenv.load_dotenv("app\api_key.env")
tomtom_key= os.getenv("TOMTOM_KEY")

# tom tom routing api to create routes between two points for truck
route_tomtom_post= "https://api.tomtom.com/routing/1/calculateRoute/{location}/json?key={key}&travelMode=truck"
