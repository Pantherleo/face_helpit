#!/usr/bin/env python3
"""
Quick Fix for Supabase RLS Issue
Run this after setting up the database with supabase_setup.sql
"""

import os
import sys

def main():
    print("🔧 SUPABASE FACE RECOGNITION - QUICK FIX")
    print("=" * 50)

    print("\n📋 STEPS TO FIX:")
    print("1. Go to https://supabase.com/dashboard")
    print("2. Open your project: pallguhnynvborekzixi")
    print("3. Go to SQL Editor")
    print("4. Copy and paste the contents of supabase_setup.sql")
    print("5. Click 'Run'")

    print("\n📋 WHAT THIS DOES:")
    print("• Creates the 'faces' table if it doesn't exist")
    print("• Disables Row Level Security (RLS) for development")
    print("• Creates storage bucket 'faces' (you do this manually)")

    print("\n🧪 TEST AFTER FIXING:")
    print("python test_supabase.py")

    print("\n🚀 RUN YOUR SYSTEM:")
    print("• API: python -m uvicorn face_api:app --reload")
    print("• Notebook: jupyter notebook insight_face.ipynb")

    print("\n" + "=" * 50)
    print("❓ STILL HAVING ISSUES?")
    print("• Check Supabase dashboard for error messages")
    print("• Verify your anon key is correct")
    print("• Make sure the 'faces' bucket exists and is Public")

    input("\nPress Enter when you've run the SQL setup...")

    # Test connection after user says they ran the SQL
    print("\n🧪 Testing connection...")
    os.system("python test_supabase.py")

if __name__ == "__main__":
    main()