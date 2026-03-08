-- =========================================
-- SUPABASE FACE RECOGNITION DATABASE SETUP
-- Run this in Supabase SQL Editor
-- =========================================

-- 1. Create the faces table (if not exists)
CREATE TABLE IF NOT EXISTS faces (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  embedding JSONB NOT NULL,
  latitude FLOAT DEFAULT 0,
  longitude FLOAT DEFAULT 0,
  image_url TEXT,
  image_name TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. DISABLE Row Level Security for development
-- WARNING: This allows anyone to read/write the table
-- For production, create proper policies instead
ALTER TABLE faces DISABLE ROW LEVEL SECURITY;

-- Alternative: Create permissive policies (safer for production)
-- Uncomment these lines instead of DISABLE RLS above:

-- CREATE POLICY "Allow all operations for anon users" ON faces
-- FOR ALL USING (true) WITH CHECK (true);

-- CREATE POLICY "Allow all operations for authenticated users" ON faces
-- FOR ALL USING (true) WITH CHECK (true);

-- 3. Create storage bucket (if not exists)
-- Note: You need to create this manually in Supabase Dashboard -> Storage
-- Bucket name: "faces"
-- Make it Public for image access

-- 4. Test the setup
-- After running this, test with:
-- python test_supabase.py

-- =========================================
-- OPTIONAL: Add indexes for better performance
-- =========================================

-- Index for faster queries (if you have many faces)
CREATE INDEX IF NOT EXISTS idx_faces_created_at ON faces(created_at DESC);

-- Index for location-based queries
CREATE INDEX IF NOT EXISTS idx_faces_location ON faces(latitude, longitude);

-- =========================================
-- VERIFICATION QUERIES
-- =========================================

-- Check if table exists and RLS status
SELECT
  schemaname,
  tablename,
  rowsecurity
FROM pg_tables
WHERE tablename = 'faces';

-- Check current policies (should be empty if RLS disabled)
SELECT * FROM pg_policies WHERE tablename = 'faces';

-- Check table structure
\d faces