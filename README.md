# AI E-Truck Dispatcher

An intelligent FastAPI-based route optimization system for electric trucks that automatically plans optimal routes, manages battery consumption, and schedules charging stops.

## 🚛 Overview

The AI E-Truck Dispatcher is a comprehensive solution designed to solve the complex logistics challenges of electric truck fleet management. The system considers battery capacity, charging station availability, route optimization, and real-time energy consumption to provide optimal delivery routes.

### Key Features

- **Smart Route Optimization**: Calculates optimal routes between multiple stops using advanced algorithms
- **Battery Management**: Monitors State of Charge (SOC) and predicts energy consumption based on distance
- **Intelligent Charging**: Automatically schedules charging stops when battery levels are insufficient
- **Multiple Truck Models**: Supports various electric truck specifications (Mercedes eActros, MAN eGTX)
- **Real-time Planning**: Considers start times and provides detailed scheduling
- **Cost Optimization**: Balances between time-optimal and cost-optimal charging strategies
- **Geographic Coverage**: Supports German cities and European charging networks

## 🏗️ Architecture

```
AI_Energy_Hack/
├── app/
│   ├── main.py                 # FastAPI application and endpoints
│   ├── brain.py               # Core optimization algorithms and scheduling logic
│   ├── Matrix_data_process.py # Distance matrix generation and data processing
│   ├── pydantic_config.py     # API models and request/response schemas
│   └── config.py              # Configuration and API keys
├── data/
│   ├── city_choices.json      # Available cities with coordinates
│   ├── truck_specs.json       # Electric truck specifications
│   └── combined_charge_points.csv # Charging station database
├── test_api.py                # API testing script
└── requirements.txt           # Python dependencies
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- TomTom API key (for route calculation)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Sarvagya2009/AI_Energy_Hack.git
   cd AI_Energy_Hack
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up TomTom API key**
   Create a file `app/api_key.env` with your TomTom API key:
   ```
   TOMTOM_KEY=your_tomtom_api_key_here
   ```

4. **Start the server**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## 📡 API Reference

### Main Endpoint

#### `POST /optimize-route`

Optimizes the route for an electric truck considering battery constraints and charging needs.

**Request Body:**
```json
{
  "origin": "Ingolstadt",
  "stops": ["Halle"],
  "start_time": "08:00",
  "truck_model": "Mercedes eActros"
}
```

**Response:**
```json
{
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
      "time": "09:30",
      "location": "Charge Point 1",
      "latitude": 48.135,
      "longitude": 11.582,
      "points": [],
      "action": "charge/rest",
      "duration": 60,
      "SOC": 80,
      "why": "Needed to charge to reach next destination"
    }
  ],
  "total_distance": 250.5,
  "total_duration": 4.5
}
```

#### `GET /health`

Health check endpoint to verify API status.

**Response:**
```json
{
  "status": "healthy",
  "message": "AI E-Truck Dispatcher API is running"
}
```

## 🔧 Configuration

### Supported Cities

The system currently supports the following German cities:
- Großbeeren, Ingolstadt, Hermsdorf, Halle, Zuffenhausen
- Bamberg, Świebodzin, Grünheide, Schwandorf, Pentling, Arnstadt

### Truck Models

| Model | Battery (kWh) | Range (km) | Consumption (kWh/km) |
|-------|---------------|------------|---------------------|
| Mercedes eActros | 600 | 500 | 1.2 |
| MAN eGTX | 480 | 400 | 1.2 |

### Charging Strategy

The system supports two charging optimization strategies:
- **Time-optimal**: Prioritizes charging stations with highest power output
- **Cost-optimal**: Prioritizes charging stations with lowest cost per kWh

## 🧠 Core Algorithms

### Route Optimization
- Uses Traveling Salesman Problem (TSP) approach for multi-stop routes
- Integrates with TomTom Routing API for accurate distance and time calculations
- Considers traffic patterns and truck-specific routing constraints

### Battery Management
- Monitors real-time State of Charge (SOC)
- Predicts energy consumption based on distance and truck specifications
- Maintains minimum 10% battery level for safety
- Optimizes charging to 80% capacity for battery health

### Charging Station Selection
- Filters stations within truck range using Haversine distance formula
- Considers charging power, cost, and location accessibility
- Implements intelligent scheduling to minimize total travel time

## 🔬 Testing

### Manual Testing

Run the provided test script:
```bash
python test_api.py
```

### API Testing

Use the interactive documentation at http://localhost:8000/docs to test endpoints directly.

### Example Test Request

```bash
curl -X POST "http://localhost:8000/optimize-route" \
     -H "Content-Type: application/json" \
     -d '{
       "origin": "Halle",
       "stops": ["Zuffenhausen"],
       "start_time": "08:00",
       "truck_model": "Mercedes eActros"
     }'
```

## 📊 Data Sources

- **Charging Stations**: Combined database of public charging infrastructure
- **City Coordinates**: GPS coordinates for supported German cities
- **Truck Specifications**: Real-world electric truck performance data
- **Route Data**: TomTom API for accurate routing and distance calculation

## 🛠️ Development

### Code Structure

- **`main.py`**: FastAPI application setup and endpoint definitions
- **`brain.py`**: Core optimization logic and scheduling algorithms
- **`Matrix_data_process.py`**: Distance calculations and data preprocessing
- **`pydantic_config.py`**: Data models and validation schemas

### Key Functions

- `compute_schedule()`: Main optimization algorithm
- `validate_input()`: Input validation and data loading
- `input_from_user()`: Distance matrix generation
- `transform()`: Data transformation for API responses

## 🔍 Troubleshooting

### Common Issues

1. **TomTom API Key Missing**
   ```
   Error: Could not load TomTom API key
   ```
   Solution: Ensure `app/api_key.env` exists with valid `TOMTOM_KEY`

2. **Invalid City Names**
   ```
   ValueError: Invalid city choice
   ```
   Solution: Use only supported cities from `data/city_choices.json`

3. **Connection Errors**
   ```
   Error: Could not connect to API
   ```
   Solution: Ensure the server is running with `uvicorn app.main:app --reload`

### Debug Mode

Run the server in debug mode for detailed logging:
```bash
uvicorn app.main:app --reload --log-level debug
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add type hints to all functions
- Include docstrings for new modules and functions
- Test new features with sample data
- Update documentation for API changes

## 📄 License

This project is part of an AI Energy Hackathon and is intended for educational and research purposes.

## 🙏 Acknowledgments

- TomTom API for routing services
- Open charging station databases
- FastAPI framework for rapid API development
- Electric truck manufacturers for specifications

## 📞 Support

For questions and support, please create an issue in the GitHub repository.

---

*Built with ❤️ for sustainable logistics and the future of electric transportation.*