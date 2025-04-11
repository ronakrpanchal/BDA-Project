import json
import sqlite3
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent , AgentExecutor
from tools import create_user_tool
from py_obj import DietResponse
from langchain.memory import ConversationBufferMemory


load_dotenv()

# # ---------- Database Config ----------
DB_NAME = "health_tracker.db"

# ---------- Agent Setup ----------
def build_agent(user_id: int):
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("Missing GROQ_API_KEY environment variable")
    
    parser = PydanticOutputParser(pydantic_object=DietResponse)
    
    diet_prompt_template = """
        You are a diet planning assistant. Return the JSON response strictly following this schema:
    {format_instructions}

    Some user data is fetched from tools, others are part of the prompt.

    Example user info:
    - Height, weight, age, gender, BFP from the database
    - Goal, budget, allergies, medical conditions, calorie intake, activity level from user prompt (if provided)


        Plan Instructions:
        - Use Indian/Gujarati meals.
        - For vegetarians: avoid non-veg. For vegans: avoid dairy & non-veg.
        - Avoid allergens and food items that worsen known medical conditions.
        - Calorie target should match user's goal or intake limit.
        - All meals should have calories mentioned and use regional ingredients.
        - don't add any units in integer values.
        
    Generate a 7-day Indian/Gujarati meal plan with nutritional info. Output must strictly follow the schema.
    
    
    """
    
    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", diet_prompt_template),
        ("user", "{input}"),
        ("placeholder", "{agent_scratchpad}")
        
    ]).partial(format_instructions=parser.get_format_instructions())

    llm = ChatGroq(
        temperature=0.5,
        model_name="llama-3.3-70b-versatile",
        groq_api_key=groq_api_key
    )

    tools = [create_user_tool(user_id)]
    
    agent = create_tool_calling_agent(
        llm=llm,
        tools=tools,
        prompt=chat_prompt
    )
    
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        memory=memory
    )
    return agent_executor,parser

# ---------- Main Chat Function ----------
def chat_with_diet_agent(user_prompt: str, user_id: int):
    agent,parser = build_agent(user_id)
    response = agent.invoke({
        "input":prompt,
        # "agent_scratchpad":""
    })
    return response,parser

def store_AI_plan(user_id: int, ai_json: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO diet (user_id, AI_plan) VALUES (?, ?)",
        (user_id, ai_json)
    )

    conn.commit()
    conn.close()

# ---------- Example Usage ----------
if __name__ == "__main__":
    user_id = 1
    prompt = "Can you plan a budget-friendly high protein vegetarian diet for me?"
    
    try:
        response,parser = chat_with_diet_agent(prompt, user_id)
        print("\n--- AI Response ---\n")
        store_AI_plan(user_id=user_id, ai_json=response["output"])
        print("plan saved successfully")
        # print(response)
        # print(parser.parse(response["output"]))
    except Exception as e:
        print(f"Error: {e}")