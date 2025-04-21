 health_tracer_dashboard.pyimport streamlit as st
import sqlite3
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from confluent_kafka import Consumer
import threading
import time
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Health Tracker Dashboard",
    page_icon="🥗",
    layout="wide"
)

# Initialize session state for Kafka messages
if 'update_trigger' not in st.session_state:
    st.session_state.update_trigger = 0
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()
if 'recent_activities' not in st.session_state:
    st.session_state.recent_activities = []

# Database connection function
def get_db_connection():
    conn = sqlite3.connect('health_tracker.db')
    conn.row_factory = sqlite3.Row
    return conn

# Function to load users with diet plans
def load_users_with_diets():
    conn = get_db_connection()
    query = """
    SELECT u.id, u.name, u.email, d.AI_Plan, u.height, u.weight, u.age, u.gender, u.bfp
    FROM user u
    LEFT JOIN diet d ON u.id = d.user_id
    """
    users_df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Count users with diet plans
    users_with_diet = users_df.dropna(subset=['AI_Plan']).drop_duplicates(subset=['id']).shape[0]
    total_users = users_df.drop_duplicates(subset=['id']).shape[0]
    
    return users_df, users_with_diet, total_users

# Function to load meal logs
def load_meal_logs():
    conn = get_db_connection()
    query = """
    SELECT ml.*, u.name as user_name 
    FROM meal_log ml
    JOIN user u ON ml.user_id = u.id
    ORDER BY ml.id DESC
    """
    meal_logs_df = pd.read_sql_query(query, conn)
    conn.close()
    
    return meal_logs_df

# Parse diet plan JSON to extract macronutrient distribution
def extract_macros_distribution(diet_plan_json):
    if not diet_plan_json or diet_plan_json == 'null':
        return None
    
    try:
        plan_data = json.loads(diet_plan_json)
        if 'diet_plan' in plan_data and 'calorieDistribution' in plan_data['diet_plan']:
            distribution = plan_data['diet_plan']['calorieDistribution']
            return {item['category']: float(item['percentage'].strip('%')) for item in distribution}
        elif 'calorieDistribution' in plan_data:
            distribution = plan_data['calorieDistribution']
            return {item['category']: float(item['percentage'].strip('%')) for item in distribution}
    except (json.JSONDecodeError, TypeError, KeyError):
        pass
    
    return None

# Extract calorie data from meal logs
def extract_calorie_data(meal_logs_df):
    calorie_data = []
    
    for _, row in meal_logs_df.iterrows():
        try:
            meal_data = json.loads(row['user_meals'])
            if 'totalCalories' in meal_data:
                calorie_data.append({
                    'user_id': row['user_id'],
                    'user_name': row['user_name'],
                    'meal_type': row['meal_type'],
                    'calories': meal_data['totalCalories'],
                    'timestamp': datetime.now() - timedelta(minutes=len(calorie_data))  # Simulated timestamps
                })
        except (json.JSONDecodeError, KeyError):
            pass
    
    return pd.DataFrame(calorie_data) if calorie_data else pd.DataFrame()

# Kafka Consumer setup function
def setup_kafka_consumer():
    conf = {
        'bootstrap.servers': 'kafka:9092',
        'group.id': 'health_tracker_dashboard',
        'auto.offset.reset': 'latest'
    }
    
    consumer = Consumer(conf)
    consumer.subscribe(['user_updates', 'diet_updates', 'meal_log_updates'])
    
    return consumer

# Kafka message processing thread
def kafka_consumer_thread():
    try:
        consumer = setup_kafka_consumer()
        
        while True:
            msg = consumer.poll(1.0)
            
            if msg is None:
                continue
            
            if msg.error():
                print(f"Consumer error: {msg.error()}")
                continue
            
            # Process message
            try:
                message_data = json.loads(msg.value().decode('utf-8'))
                topic = msg.topic()
                
                # Add to recent activities
                activity = {
                    'topic': topic,
                    'data': message_data,
                    'timestamp': datetime.now()
                }
                
                # Keep only the 10 most recent activities
                st.session_state.recent_activities = [activity] + st.session_state.recent_activities[:9]
                
                # Trigger update
                st.session_state.update_trigger += 1
                st.session_state.last_update = datetime.now()
                
            except Exception as e:
                print(f"Error processing message: {e}")
                
    except Exception as e:
        print(f"Kafka consumer thread error: {e}")
    finally:
        # Close consumer
        if 'consumer' in locals():
            consumer.close()

# Start Kafka consumer thread if not in session state
if 'kafka_thread_started' not in st.session_state:
    try:
        thread = threading.Thread(target=kafka_consumer_thread, daemon=True)
        thread.start()
        st.session_state.kafka_thread_started = True
    except Exception as e:
        st.error(f"Failed to start Kafka consumer: {e}")
        st.session_state.kafka_thread_started = False

# Main title
st.title("🥗 Health Tracker Dashboard")
st.caption(f"Last updated: {st.session_state.last_update.strftime('%H:%M:%S')}")

# Load user data
users_df, users_with_diet, total_users = load_users_with_diets()
meal_logs_df = load_meal_logs()

# Create tabs for different dashboard sections
tab1, tab2, tab3 = st.tabs(["Diet Plan Summary", "Meal Tracking", "Real-time Activity"])

with tab1:
    st.header("Diet Plan Summary")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Users", total_users)
        
    with col2:
        st.metric("Users with Diet Plans", users_with_diet)
    
    # Progress bar showing percentage of users with diet plans
    progress_percentage = (users_with_diet / total_users * 100) if total_users > 0 else 0
    st.progress(progress_percentage / 100)
    st.caption(f"{progress_percentage:.1f}% of users have created diet plans")
    
    # Only process users with diet plans
    users_with_diets = users_df.dropna(subset=['AI_Plan']).drop_duplicates(subset=['id'])
    
    if not users_with_diets.empty:
        st.header("Macronutrient Distribution by User")
        
        # Extract macronutrient distribution for each user
        macro_data = []
        
        for _, row in users_with_diets.iterrows():
            macros = extract_macros_distribution(row['AI_Plan'])
            if macros:
                for category, percentage in macros.items():
                    macro_data.append({
                        'User': row['name'],
                        'Nutrient': category.capitalize(),
                        'Percentage': percentage
                    })
        
        if macro_data:
            # Create DataFrame for visualization
            macro_df = pd.DataFrame(macro_data)
            
            # Create grouped bar chart
            fig = px.bar(
                macro_df,
                x='User',
                y='Percentage',
                color='Nutrient',
                title="Macronutrient Distribution by User",
                labels={'Percentage': 'Percentage (%)', 'User': 'User Name'},
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # BMI Analysis
            st.header("User Health Metrics")
            
            # Calculate BMI for each user
            bmi_data = []
            for _, row in users_with_diets.iterrows():
                if row['height'] and row['weight']:
                    bmi = row['weight'] / ((row['height']/100) ** 2)
                    
                    # BMI category
                    if bmi < 18.5:
                        category = "Underweight"
                    elif bmi < 25:
                        category = "Normal"
                    elif bmi < 30:
                        category = "Overweight"
                    else:
                        category = "Obese"
                    
                    bmi_data.append({
                        'User': row['name'],
                        'BMI': round(bmi, 1),
                        'Category': category
                    })
            
            if bmi_data:
                bmi_df = pd.DataFrame(bmi_data)
                
                # Create BMI chart
                fig = px.bar(
                    bmi_df,
                    x='User',
                    y='BMI',
                    color='Category',
                    title="BMI by User",
                    color_discrete_map={
                        'Underweight': 'skyblue',
                        'Normal': 'green',
                        'Overweight': 'orange',
                        'Obese': 'red'
                    }
                )
                
                # Add reference lines for BMI categories
                fig.add_hline(y=18.5, line_dash="dash", line_color="blue", annotation_text="Underweight")
                fig.add_hline(y=25, line_dash="dash", line_color="green", annotation_text="Normal")
                fig.add_hline(y=30, line_dash="dash", line_color="red", annotation_text="Overweight")
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Couldn't extract macronutrient distribution data from any diet plans.")
    else:
        st.info("No users with diet plans found in the database.")

with tab2:
    st.header("Meal Tracking Analysis")
    
    if not meal_logs_df.empty:
        # Process meal logs to extract calorie data
        calorie_df = extract_calorie_data(meal_logs_df)
        
        if not calorie_df.empty:
            # Group by user and meal type
            user_selection = st.selectbox(
                "Select User for Detailed Analysis",
                options=["All Users"] + list(calorie_df['user_name'].unique())
            )
            
            if user_selection != "All Users":
                filtered_df = calorie_df[calorie_df['user_name'] == user_selection]
            else:
                filtered_df = calorie_df
            
            # Create calorie intake by meal type
            meal_type_calories = filtered_df.groupby('meal_type')['calories'].mean().reset_index()
            
            fig = px.bar(
                meal_type_calories,
                x='meal_type',
                y='calories',
                title=f"Average Calories by Meal Type for {user_selection}",
                color='meal_type',
                labels={'calories': 'Calories (kcal)', 'meal_type': 'Meal Type'},
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Daily calorie timeline
            if 'timestamp' in filtered_df.columns:
                filtered_df['date'] = filtered_df['timestamp'].dt.date
                daily_calories = filtered_df.groupby('date')['calories'].sum().reset_index()
                
                fig = px.line(
                    daily_calories,
                    x='date',
                    y='calories',
                    title=f"Daily Calorie Intake for {user_selection}",
                    labels={'calories': 'Total Calories (kcal)', 'date': 'Date'},
                    markers=True
                )
                
                fig.update_layout(xaxis_title="Date", yaxis_title="Total Calories (kcal)")
                st.plotly_chart(fig, use_container_width=True)
                
                # Pie chart showing calorie distribution across meal types
                meal_distribution = filtered_df.groupby('meal_type')['calories'].sum().reset_index()
                
                fig = px.pie(
                    meal_distribution,
                    values='calories',
                    names='meal_type',
                    title=f"Calorie Distribution by Meal Type for {user_selection}",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Couldn't extract calorie data from meal logs.")
    else:
        st.info("No meal logs found in the database.")

with tab3:
    st.header("Real-time Activity Monitor")
    
    # Display real-time update status
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Last Update", st.session_state.last_update.strftime("%H:%M:%S"))
    
    with col2:
        if st.session_state.kafka_thread_started:
            st.success("Real-time updates active")
        else:
            st.error("Real-time updates not available")
    
    # Display recent activities
    st.subheader("Recent Activities")
    
    if st.session_state.recent_activities:
        for i, activity in enumerate(st.session_state.recent_activities):
            topic = activity['topic'].replace('_updates', '').capitalize()
            time_str = activity['timestamp'].strftime("%H:%M:%S")
            
            if topic == 'User':
                icon = "👤"
            elif topic == 'Diet':
                icon = "🥗"
            elif topic == 'Meal_log':
                icon = "🍽️"
            else:
                icon = "📝"
            
            st.markdown(f"{icon} **{topic} update at {time_str}**")
            
            with st.expander(f"View details"):
                st.json(activity['data'])
            
            if i < len(st.session_state.recent_activities) - 1:
                st.divider()
    else:
        st.info("No recent activities detected. Updates will appear here in real-time.")
    
    # Auto-refresh button
    auto_refresh = st.checkbox("Enable auto-refresh (5s)", value=True)
    if auto_refresh:
        time.sleep(5)
        st.experimental_rerun()import streamlit as st
import sqlite3
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="Health Tracker Dashboard",
    page_icon="🥗",
    layout="wide"
)

# Database connection function
def get_db_connection():
    conn = sqlite3.connect('health_tracker.db')
    conn.row_factory = sqlite3.Row
    return conn

# Function to load users with diet plans
def load_users_with_diets():
    conn = get_db_connection()
    query = """
    SELECT u.id, u.name, u.email, d.AI_Plan
    FROM user u
    LEFT JOIN diet d ON u.id = d.user_id
    """
    users_df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Count users with diet plans
    users_with_diet = users_df.dropna(subset=['AI_Plan']).drop_duplicates(subset=['id']).shape[0]
    total_users = users_df.drop_duplicates(subset=['id']).shape[0]
    
    return users_df, users_with_diet, total_users

# Parse diet plan JSON to extract macronutrient distribution
def extract_macros_distribution(diet_plan_json):
    if not diet_plan_json or diet_plan_json == 'null':
        return None
    
    try:
        plan_data = json.loads(diet_plan_json)
        if 'diet_plan' in plan_data and 'calorieDistribution' in plan_data['diet_plan']:
            distribution = plan_data['diet_plan']['calorieDistribution']
            return {item['category']: float(item['percentage'].strip('%')) for item in distribution}
        elif 'calorieDistribution' in plan_data:
            distribution = plan_data['calorieDistribution']
            return {item['category']: float(item['percentage'].strip('%')) for item in distribution}
    except (json.JSONDecodeError, TypeError, KeyError):
        pass
    
    return None

# Main title
st.title("🥗 Health Tracker Dashboard")

# Load user data
users_df, users_with_diet, total_users = load_users_with_diets()

# Display summary metrics
st.header("Diet Plan Summary")
col1, col2 = st.columns(2)

with col1:
    st.metric("Total Users", total_users)
    
with col2:
    st.metric("Users with Diet Plans", users_with_diet)

# Progress bar showing percentage of users with diet plans
progress_percentage = (users_with_diet / total_users * 100) if total_users > 0 else 0
st.progress(progress_percentage / 100)
st.caption(f"{progress_percentage:.1f}% of users have created diet plans")

# Only process users with diet plans
users_with_diets = users_df.dropna(subset=['AI_Plan']).drop_duplicates(subset=['id'])

if not users_with_diets.empty:
    st.header("Macronutrient Distribution by User")
    
    # Extract macronutrient distribution for each user
    macro_data = []
    
    for _, row in users_with_diets.iterrows():
        macros = extract_macros_distribution(row['AI_Plan'])
        if macros:
            for category, percentage in macros.items():
                macro_data.append({
                    'User': row['name'],
                    'Nutrient': category.capitalize(),
                    'Percentage': percentage
                })
    
    if macro_data:
        # Create DataFrame for visualization
        macro_df = pd.DataFrame(macro_data)
        
        # Create grouped bar chart
        fig = px.bar(
            macro_df,
            x='User',
            y='Percentage',
            color='Nutrient',
            title="Macronutrient Distribution by User",
            labels={'Percentage': 'Percentage (%)', 'User': 'User Name'},
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        fig.update_layout(
            xaxis_title="User",
            yaxis_title="Percentage (%)",
            legend_title="Nutrient",
            barmode='group'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Also create a pie chart for each user
        st.header("Individual User Macronutrient Distributions")
        
        # Create tabs for each user
        user_tabs = st.tabs(users_with_diets['name'].tolist())
        
        for i, tab in enumerate(user_tabs):
            with tab:
                user_name = users_with_diets.iloc[i]['name']
                user_data = macro_df[macro_df['User'] == user_name]
                
                if not user_data.empty:
                    fig = px.pie(
                        user_data,
                        values='Percentage',
                        names='Nutrient',
                        title=f"{user_name}'s Macronutrient Distribution",
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"No macronutrient distribution data found for {user_name}")
    else:
        st.info("Couldn't extract macronutrient distribution data from any diet plans.")
else:
    st.info("No users with diet plans found in the database.")