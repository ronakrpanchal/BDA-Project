# BDA-Project

# Health Tracker with Real-time Meal Logging

This project implements a health tracking system with real-time meal logging using Kafka, all containerized with Docker.

## Features

- FastAPI backend for health tracking
- Real-time meal logging with Kafka
- Streamlit dashboard for visualizing meal data in real-time
- Docker containerization for easy deployment

## Getting Started

### Prerequisites

- Docker and Docker Compose

### Running the Application

1. Build and start all services:

```bash
docker-compose up -d --build
```

2. Access the services:
   - FastAPI backend: http://localhost:8000
   - Streamlit dashboard: http://localhost:8501

## How It Works

1. When a user logs a meal via the `/meal_log` endpoint, the data is stored in the SQLite database
2. Simultaneously, the meal data is sent to a Kafka topic (`meal-logs`)
3. The Streamlit dashboard consumes messages from the Kafka topic and updates the graph in real-time

## API Endpoints

### POST /meal_log

Log a meal for a user:

```json
{
  "user_id": 1,
  "meal_type": "breakfast",
  "user_meals": {
    "food": "oatmeal",
    "calories": 350,
    "protein": 15
  }
}
```

## Architecture

- **FastAPI**: Backend API service
- **Kafka**: Message broker for real-time data streaming
- **Zookeeper**: Required for Kafka
- **Streamlit**: Dashboard for real-time visualization
