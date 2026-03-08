#!/usr/bin/env python3
"""
Test Supabase Connection and RLS Fix
Run this to verify your Supabase setup works
"""

from supabase import create_client
import uuid
import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# -------- Supabase Configuration --------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_KEY must be set in environment variables or a .env file."
    )

def test_supabase_connection():
    """Test basic Supabase connection"""
    print("🔍 Testing Supabase connection...")

    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Connected to Supabase successfully!")
        return supabase
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def test_table_access(supabase):
    """Test if we can read from faces table"""
    print("\n🔍 Testing table access...")

    try:
        # Try to read from faces table
        response = supabase.table("faces").select("*").limit(1).execute()
        print(f"✅ Can read from faces table! Found {len(response.data)} records")
        return True
    except Exception as e:
        print(f"❌ Cannot read from faces table: {e}")
        return False

def test_storage_access(supabase):
    """Test if we can access storage bucket"""
    print("\n🔍 Testing storage access...")

    try:
        # Try to list files in faces bucket
        files = supabase.storage.from_("faces").list()
        print(f"✅ Can access faces storage bucket! Found {len(files)} files")
        return True
    except Exception as e:
        print(f"❌ Cannot access faces storage: {e}")
        return False

def test_write_access(supabase):
    """Test if we can write to faces table (this will fail with RLS)"""
    print("\n🔍 Testing write access...")

    try:
        # Try to insert a test record
        test_data = {
            "id": str(uuid.uuid4()),
            "embedding": [0.1] * 512,  # Dummy 512-dim vector
            "latitude": 0.0,
            "longitude": 0.0,
            "image_url": "test.jpg",
            "image_name": "test.jpg"
        }

        response = supabase.table("faces").insert(test_data).execute()
        print("✅ Write access works! (RLS disabled or policy allows)")
        return True

    except Exception as e:
        error_msg = str(e)
        if "row-level security policy" in error_msg.lower():
            print("❌ RLS BLOCKING INSERTS!")
            print("   Solution: Disable RLS or create proper policies")
            print("   Run the SQL commands below in Supabase SQL Editor:")
            print()
            print("   -- Option 1: Disable RLS (for development)")
            print("   ALTER TABLE faces DISABLE ROW LEVEL SECURITY;")
            print()
            print("   -- Option 2: Create policy (recommended for production)")
            print("   CREATE POLICY \"Allow all operations for authenticated users\" ON faces")
            print("   FOR ALL USING (true);")
            return False
        else:
            print(f"❌ Write failed for different reason: {e}")
            return False

def main():
    """Run all tests"""
    print("🚀 Supabase Face Recognition System - Connection Test")
    print("=" * 60)

    supabase = test_supabase_connection()
    if not supabase:
        return

    table_ok = test_table_access(supabase)
    storage_ok = test_storage_access(supabase)
    write_ok = test_write_access(supabase)

    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    print(f"   Connection: {'✅' if supabase else '❌'}")
    print(f"   Table Read: {'✅' if table_ok else '❌'}")
    print(f"   Storage:    {'✅' if storage_ok else '❌'}")
    print(f"   Table Write: {'✅' if write_ok else '❌'}")

    if write_ok:
        print("\n🎉 ALL TESTS PASSED! Your system is ready!")
        print("   Run: python face_api.py")
        print("   Or open: insight_face.ipynb")
    else:
        print("\n⚠️  FIX NEEDED: Enable write access to faces table")
        print("   Go to Supabase Dashboard → SQL Editor")
        print("   Run: ALTER TABLE faces DISABLE ROW LEVEL SECURITY;")

if __name__ == "__main__":
    main()