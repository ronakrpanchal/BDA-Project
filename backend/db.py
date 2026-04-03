""" Module to handle database interactions with Supabase. """
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# You must set these in your .env file
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables.")

# Create a single supabase client instance
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
