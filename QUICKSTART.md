# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Verify Supabase Setup
Check that you have in Supabase:
- ✅ Table named `faces` with columns: id, embedding, latitude, longitude, image_url, image_name
- ✅ Storage bucket named `faces` (set to Public)

### Step 2: Test in Jupyter Notebook

Open `insight_face.ipynb` and run:

```python
# Import utilities
from face_utils import store_face_to_supabase, search_faces_in_supabase

# Store a face
with open("photo_bts_face_recog.jpg", "rb") as f:
    result = store_face_to_supabase(f.read(), latitude=28.6139, longitude=77.2090)
    print(f"✅ Stored! ID: {result[0]['id']}")

# Search for similar faces
import cv2
query = cv2.imread("photo_bts_face_recog.jpg")
matches = search_faces_in_supabase(query, threshold=0.45)
print(f"✅ Found {len(matches)} matches!")
for m in matches:
    print(f"  Similarity: {m['similarity']:.4f} at {m['latitude']}, {m['longitude']}")
```

### Step 3: Start API Server

```bash
cd e:\Face_recog_Detec\face_system
python -m uvicorn face_api:app --reload
```

Server runs at: `http://localhost:8000`

### Step 4: Test API Endpoints

**Upload a face:**
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@photo_bts_face_recog.jpg" \
  -F "latitude=28.6139" \
  -F "longitude=77.2090"
```

**Search for faces:**
```bash
curl -X POST "http://localhost:8000/search?threshold=0.45" \
  -F "file=@photo_bts_face_recog.jpg"
```

**Check database:**
```bash
curl "http://localhost:8000/stats"
```

---

## 📁 Key Files Created

| File | Purpose |
|------|---------|
| **face_utils.py** | Shared utility module (store, search, extract) |
| **face_api.py** | FastAPI server (uses face_utils) |
| **insight_face.ipynb** | Jupyter notebook (uses face_utils) |

---

## 🔑 Important Credentials

Located in `face_utils.py`:
```python
SUPABASE_URL = "https://pallguhnynvborekzixi.supabase.co"
SUPABASE_KEY = "your_key_here"
```

⚠️ For production, use environment variables or a `.env` file.  See
`supabase_utils.py` which now calls `python-dotenv` automatically.

---

## 💾 Data Flow

```
Image (JPG/PNG)
    ↓
[Extract Embeddings via InsightFace]
    ↓
[Store in Supabase Database] + [Upload to Storage]
    ↓
Query Image → [Compare similarity] → Show matches
```

---

## ✅ Checklist

- [ ] Supabase table `faces` created
- [ ] Supabase bucket `faces` created (Public)
- [ ] face_utils.py imported in notebook
- [ ] face_api.py can start without errors
- [ ] `/upload` endpoint works
- [ ] `/search` endpoint returns results
- [ ] Embeddings visible in Supabase dashboard

---

## 🆘 Troubleshooting

| Error | Solution |
|-------|----------|
| `No face detected` | Use clear, front-facing images (100x100 px min) |
| `Connection refused` | Check SUPABASE_URL/KEY in face_utils.py |
| `ModuleNotFoundError: face_utils` | Make sure you're in face_system directory |
| `API won't start` | Run `pip install insightface opencv-python supabase fastapi uvicorn` |

---

## 📊 API Endpoints Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/upload` | Store face + embeddings |
| POST | `/search` | Find similar faces |
| GET | `/stats` | Database statistics |
| GET | `/health` | Server health check |

---

## 💡 Example: Full Workflow

```python
# 1. Upload 5 faces to database
from pathlib import Path
for img in Path(".").glob("*.jpg"):
    with open(img, "rb") as f:
        store_face_to_supabase(f.read(), 28.6139, 77.2090)

# 2. Search for matches
matches = search_faces_in_supabase(cv2.imread("query.jpg"), 0.45)

# 3. Filter by location
nearby = [m for m in matches if abs(m['latitude'] - 28.6139) < 0.01]

# 4. Get best match
best = max(matches, key=lambda x: x['similarity'])
print(f"Best match: {best['similarity']:.4f} at {best['image_url']}")
```

---

See **INTEGRATION_GUIDE.md** for detailed documentation.
