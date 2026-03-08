# Face Recognition System - Integration Guide

## Overview
Your face recognition system now has **full Supabase integration** with a shared utility module connecting your Jupyter notebook and FastAPI server.

---

## Architecture

### Components

1. **face_utils.py** (Shared Module)
   - Core functions for embedding extraction
   - Supabase operations (store, search, load, delete)
   - Face cropping utilities
   - Cosine similarity matching

2. **face_api.py** (FastAPI Server)
   - REST API endpoints for upload & search
   - Uses face_utils for all operations
   - Lightweight and maintainable

3. **insight_face.ipynb** (Jupyter Notebook)
   - Interactive face testing & exploration
   - Uses face_utils for consistency
   - Direct Supabase database operations

---

## Setup Instructions

### 1. Supabase Database Setup

Create a table called `faces` with these columns:

```sql
CREATE TABLE faces (
  id UUID PRIMARY KEY,
  embedding VECTOR(512) OR JSONB,  -- 512-dim vectors from InsightFace
  latitude FLOAT,
  longitude FLOAT,
  image_url TEXT,
  image_name TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

**Alternative if using JSONB:**
```sql
CREATE TABLE faces (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  embedding JSONB NOT NULL,
  latitude FLOAT DEFAULT 0,
  longitude FLOAT DEFAULT 0,
  image_url TEXT,
  image_name TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Storage Bucket Setup

1. Go to Supabase Dashboard → Storage
2. Create a bucket named `faces`
3. Set it to **Public** (for image access)

### 3. Update Credentials

Credentials are already in `face_utils.py`:
```python
SUPABASE_URL = "https://pallguhnynvborekzixi.supabase.co"
SUPABASE_KEY = "your_key_here"
```

⚠️ **Security Note**: Move credentials to environment variables for production.
The helper module now automatically loads a `.env` file if present, so you
can create one inside `face_back` or `face_system` containing:

```
SUPABASE_URL="https://..."
SUPABASE_KEY="your_service_role_key"
```

Alternatively set the variables in your shell before starting Python:

```bash
set SUPABASE_URL=https://...
set SUPABASE_KEY=...
```

---

## Usage Examples

### Using the Jupyter Notebook

```python
# Import utilities
from face_utils import (
    store_face_to_supabase,
    search_faces_in_supabase,
    load_all_faces_from_supabase,
    extract_embeddings_from_file
)

# Store a face
with open("photo.jpg", "rb") as f:
    image_data = f.read()

stored = store_face_to_supabase(
    image_data,
    latitude=28.6139,
    longitude=77.2090
)
print(f"Stored {len(stored)} faces")

# Search for similar faces
import cv2
query_image = cv2.imread("query.jpg")
matches = search_faces_in_supabase(query_image, threshold=0.45)

for match in matches:
    print(f"Similarity: {match['similarity']:.4f}")
    print(f"Location: {match['latitude']}, {match['longitude']}")
    print(f"Image: {match['image_url']}")
```

### Using the FastAPI Server

```bash
# Start server
cd e:\Face_recog_Detec\face_system
python -m uvicorn face_api:app --reload
```

**API Endpoints:**

#### 1. Upload Face (Store embeddings + image)
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@photo.jpg" \
  -F "latitude=28.6139" \
  -F "longitude=77.2090"
```

Response:
```json
{
  "success": true,
  "faces_detected": 2,
  "faces_stored": 2,
  "details": [...]
}
```

#### 2. Search Faces
```bash
curl -X POST "http://localhost:8000/search?threshold=0.45" \
  -F "file=@query.jpg"
```

Response:
```json
{
  "success": true,
  "matches_found": 3,
  "threshold": 0.45,
  "matches": [
    {
      "similarity": 0.87,
      "latitude": 28.6139,
      "longitude": 77.2090,
      "image_url": "https://..."
    }
  ]
}
```

#### 3. Get Statistics
```bash
curl "http://localhost:8000/stats"
```

Response:
```json
{
  "success": true,
  "total_faces": 15,
  "storage_used": "See Supabase dashboard",
  "ready": true
}
```

#### 4. Health Check
```bash
curl "http://localhost:8000/health"
```

---

## Key Functions in face_utils.py

### Store Operations
```python
# Store face from bytes
store_face_to_supabase(image_bytes, latitude, longitude, metadata=None)

# Extract & crop faces
extract_and_crop_faces(image)

# Extract embeddings only
extract_embeddings(image)
extract_embeddings_from_file(image_path)
```

### Search Operations
```python
# Search in database
search_faces_in_supabase(image, threshold=0.45, max_results=None)

# Load all faces
load_all_faces_from_supabase()

# Get database stats
get_database_stats()
```

### Utility Functions
```python
# Calculate similarity between two vectors
cosine_similarity(a, b)

# Delete a face
delete_face_from_supabase(face_id)

# Initialize model (auto-called)
initialize_face_model()
```

---

## Workflow Examples

### Example 1: Add Face to Database (Notebook)
```python
# In Jupyter notebook

# Method 1: From file path
embeddings = extract_embeddings_from_file("photo_bts_face_recog.jpg")

# Method 2: With geolocation
with open("photo_bts_face_recog.jpg", "rb") as f:
    result = store_face_to_supabase(
        f.read(),
        latitude=28.6139,
        longitude=77.2090,
        metadata={"person_name": "BTS Members"}
    )
```

### Example 2: Search & Retrieve (Notebook)
```python
# Search for similar faces
query_image = cv2.imread("query_photo.jpg")
matches = search_faces_in_supabase(query_image, threshold=0.5)

# Display results
for i, match in enumerate(matches):
    print(f"Match {i+1}:")
    print(f"  Similarity: {match['similarity']:.4f}")
    print(f"  Location: {match['latitude']}, {match['longitude']}")
    print(f"  Image URL: {match['image_url']}")
```

### Example 3: Batch Upload (API via Python)
```python
import requests
from pathlib import Path

api_url = "http://localhost:8000"

# Upload all JPGs in a folder
for image_path in Path("./faces").glob("*.jpg"):
    with open(image_path, "rb") as f:
        files = {"file": f}
        data = {
            "latitude": 28.6139,
            "longitude": 77.2090
        }
        response = requests.post(f"{api_url}/upload", files=files, data=data)
        print(f"{image_path.name}: {response.json()}")
```

---

## Configuration & Customization

### Change Similarity Threshold
```python
# Default is 0.45, adjust based on your needs:
matches = search_faces_in_supabase(image, threshold=0.5)  # More strict
matches = search_faces_in_supabase(image, threshold=0.35)  # More lenient
```

### Use Different Face Model
In `face_utils.py`, change the model name:
```python
# Current: buffalo_l (recommended)
face_model = FaceAnalysis(name="buffalo_l")

# Alternatives:
face_model = FaceAnalysis(name="antelopev2")
face_model = FaceAnalysis(name="buffalo_m")
```

### GPU Acceleration
```python
# In face_utils.py, change:
face_model.prepare(ctx_id=-1, det_size=(640,640))  # CPU only

# To:
face_model.prepare(ctx_id=0, det_size=(640,640))   # GPU (if available)
```

---

## Troubleshooting

### Issue: "No face detected"
- **Cause**: Face not clear or too small
- **Solution**: Use face images with clear, front-facing faces (minimum 100x100 px)

### Issue: "Connection refused" error
- **Cause**: Supabase credentials wrong or no internet
- **Solution**: Verify SUPABASE_URL and SUPABASE_KEY in `face_utils.py`

### Issue: Slow search with many faces
- **Cause**: All embeddings loaded into memory
- **Solution**: Implement pagination or vector database (pgvector extension)

### Issue: Low similarity matches
- **Cause**: Threshold set too high or different lighting/angles
- **Solution**: Adjust threshold down, or ensure consistent image quality

### Issue: API won't start
- **Cause**: Model initialization fails
- **Solution**: Check GPU/CPU availability, ensure insightface installed

---

## File Structure

```
face_system/
├── face_api.py              ← FastAPI server (uses face_utils)
├── face_utils.py            ← Shared utilities module ✨ NEW
├── insight_face.ipynb       ← Jupyter notebook (uses face_utils)
├── face_pipeline.py
├── __pycache__/
└── db_keys/
```

---

## Next Steps

1. ✅ Create Supabase table and bucket (see Setup section)
2. ✅ Test in Jupyter: Run `store_face_to_supabase()` with a test image
3. ✅ Test API: Start server and use `/upload` endpoint
4. ✅ Verify: Check Supabase dashboard for stored embeddings
5. ✅ Search: Use `/search` endpoint or notebook search function

---

## Summary

| Feature | Notebook | API |
|---------|----------|-----|
| Store faces | ✅ | ✅ |
| Search faces | ✅ | ✅ |
| View database | ✅ | ✅ |
| Image storage | ✅ | ✅ |
| Geolocation | ✅ | ✅ |
| Interactive | ✅ | - |
| REST API | - | ✅ |
| Scalable | Good | Better |

---

**Questions?** Check face_utils.py docstrings or Supabase documentation.
