from fastapi import FastAPI, UploadFile, File
import cv2
import numpy as np
from face_utils import (
    initialize_face_model,
    extract_embeddings,
    cosine_similarity,
    store_face_to_supabase,
    search_faces_in_supabase,
    load_all_faces_from_supabase,
    get_database_stats
)

# -------- FastAPI --------
app = FastAPI()

# Initialize face model on startup
@app.on_event("startup")
async def startup():
    """Initialize face model when API starts"""
    initialize_face_model()
    print("API Ready!")


# -------- Upload Face --------
@app.post("/upload")
async def upload_face(
    file: UploadFile = File(...),
    latitude: float = 0,
    longitude: float = 0
):
    """
    Upload a face image and store embeddings in Supabase
    - Extracts face embeddings from the image
    - Stores image in Supabase storage bucket
    - Stores embeddings and metadata in Supabase database
    """
    try:
        contents = await file.read()
        
        # Store to Supabase
        stored_faces = store_face_to_supabase(
            contents,
            latitude=latitude,
            longitude=longitude
        )

        return {
            "success": True,
            "faces_detected": len(stored_faces),
            "faces_stored": len(stored_faces),
            "details": stored_faces
        }
    except Exception as e:
        return {"error": str(e)}


# -------- Search Face --------
@app.post("/search")
async def search_face(file: UploadFile = File(...), threshold: float = 0.45):
    """
    Search for matching faces in the database
    - Extracts face embeddings from the query image
    - Compares against all stored embeddings using cosine similarity
    - Returns matches above the similarity threshold
    """
    try:
        contents = await file.read()

        # Decode image
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return {"error": "Invalid image format"}

        # Search
        matches = search_faces_in_supabase(image, threshold=threshold)

        return {
            "success": True,
            "matches_found": len(matches),
            "threshold": threshold,
            "matches": matches
        }
    except Exception as e:
        return {"error": str(e)}


# -------- Get Database Stats --------
@app.get("/stats")
async def get_stats():
    """Get statistics about stored faces in the database"""
    try:
        stats = get_database_stats()
        return {
            "success": True,
            **stats
        }
    except Exception as e:
        return {"error": str(e)}


# -------- Health Check --------
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Face Recognition API"
    }