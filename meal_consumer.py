import json
import os
from confluent_kafka import Consumer, KafkaError
from prometheus_client import start_http_server, Gauge

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
MEAL_LOG_TOPIC = "meal-logs"

# Prometheus metrics
CALORIES_GAUGE = Gauge('meal_calories_total', 'Total calories per meal', ['user_id', 'meal_type'])
PROTEIN_GAUGE = Gauge('meal_protein_total', 'Total protein per meal', ['user_id', 'meal_type'])
CARBS_GAUGE = Gauge('meal_carbs_total', 'Total carbs per meal', ['user_id', 'meal_type'])
FATS_GAUGE = Gauge('meal_fats_total', 'Total fats per meal', ['user_id', 'meal_type'])

def process_message(msg_value):
    try:
        data = json.loads(msg_value)
        user_id = str(data.get('user_id', 'unknown'))
        meal_type = data.get('mealType', 'unknown')
        
        # Update Prometheus metrics
        CALORIES_GAUGE.labels(user_id=user_id, meal_type=meal_type).set(data.get('totalCalories', 0))
        
        if 'macronutrients' in data:
            PROTEIN_GAUGE.labels(user_id=user_id, meal_type=meal_type).set(data['macronutrients'].get('proteins', 0))
            CARBS_GAUGE.labels(user_id=user_id, meal_type=meal_type).set(data['macronutrients'].get('carbohydrates', 0))
            FATS_GAUGE.labels(user_id=user_id, meal_type=meal_type).set(data['macronutrients'].get('fats', 0))
            
        print(f"Processed meal log for user {user_id}, meal type: {meal_type}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except Exception as e:
        print(f"Error processing message: {e}")

def start_consumer():
    # Configure Consumer
    conf = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': 'meal-metrics-group',
        'auto.offset.reset': 'earliest'
    }
    
    consumer = Consumer(conf)
    consumer.subscribe([MEAL_LOG_TOPIC])
    
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition event
                    print(f"Reached end of partition {msg.partition()}")
                else:
                    print(f"Error: {msg.error()}")
            else:
                process_message(msg.value())
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()

if __name__ == "__main__":
    # Start Prometheus metrics server
    start_http_server(8001)
    print("Prometheus metrics server started on port 8001")
    
    # Start Kafka consumer
    print("Starting Kafka consumer...")
    start_consumer()