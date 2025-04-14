import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
import os
from kafka import KafkaConsumer
from threading import Thread
import time
from collections import defaultdict

# Configure Kafka Consumer
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_TOPIC_MEAL_LOGS = 'meal-logs'

# Initialize session state to store meal data
if 'meal_data' not in st.session_state:
    st.session_state.meal_data = []

if 'running' not in st.session_state:
    st.session_state.running = True

def consume_kafka_messages():
    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC_MEAL_LOGS,
            bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
            auto_offset_reset='latest',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        
        st.sidebar.success(f"Connected to Kafka at {KAFKA_BOOTSTRAP_SERVERS}")
        
        for message in consumer:
            if not st.session_state.running:
                break
                
            meal_log = message.value
            st.session_state.meal_data.append(meal_log)
            time.sleep(0.1)  # Small delay to prevent high CPU usage
            
    except Exception as e:
        st.sidebar.error(f"Failed to connect to Kafka: {e}")

# Start Kafka consumer in a separate thread
kafka_thread = Thread(target=consume_kafka_messages, daemon=True)
kafka_thread.start()

# Streamlit App
st.title("Real-time Meal Logging Dashboard")

# Display meal data in real-time
def render_dashboard():
    # Create a placeholder for the chart
    chart_placeholder = st.empty()
    
    # Create a placeholder for the data table
    table_placeholder = st.empty()
    
    while True:
        if st.session_state.meal_data:
            # Convert to DataFrame for easier manipulation
            df = pd.DataFrame(st.session_state.meal_data)
            
            # Group data by meal type and count
            meal_counts = defaultdict(int)
            for meal in st.session_state.meal_data:
                meal_counts[meal['meal_type']] += 1
            
            # Create bar chart
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(meal_counts.keys(), meal_counts.values())
            ax.set_xlabel('Meal Type')
            ax.set_ylabel('Count')
            ax.set_title('Meal Types Distribution')
            
            # Update chart
            chart_placeholder.pyplot(fig)
            
            # Show latest data in table
            table_placeholder.dataframe(df.tail(10).sort_values('timestamp', ascending=False))
        
        # Update every second
        time.sleep(1)

# Run the dashboard
render_dashboard()

# Clean up when the app is closed
def on_shutdown():
    st.session_state.running = False

st.on_session_end(on_shutdown)
