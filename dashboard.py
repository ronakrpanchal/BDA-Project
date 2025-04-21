import streamlit as st
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