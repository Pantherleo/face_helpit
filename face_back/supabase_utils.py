"""from supabase import create_client

SUPABASE_URL = "https://pallguhnynvborekzixi.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBhbGxndWhueW52Ym9yZWt6aXhpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI4NjU4ODcsImV4cCI6MjA4ODQ0MTg4N30.3656coe24tUYI0F5tTSbPD44A7NsXjwEVbFV0EQnumM"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load any variables from a .env file in the current working directory.
# This makes it easy to keep secrets out of source control and still
# have them available during local development or in Docker containers.
load_dotenv()

# Read credentials; getenv returns None if the variable is missing.
url: str | None = os.getenv("SUPABASE_URL")
key: str | None = os.getenv("SUPABASE_KEY")

if not url or not key:
    # Make the failure loud – trying to create the client with None would
    # raise an obscure error later.  A clear message helps debugging.
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_KEY must be configured in environment "
        "variables or defined in a .env file."
    )

# finally create the client
supabase: Client = create_client(url, key)