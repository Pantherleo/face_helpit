import os
import uuid
import shutil
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional

# Importing your logic files
from upload_store import store_face_to_supabase
from search_query import search_face_in_supabase
import glob
# Kill all ghost files on startup
for ghost in glob.glob("*.jpg"):
    if "query_" in ghost or "upload_" in ghost:
        try:
            os.remove(ghost)
        except:
            pass

# Setup basic logging to see deletions in your console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Face Recognition API",
    description="API for storing and searching face embeddings using InsightFace and Supabase",
    version="1.1.0"
)

# --- Helper Functions ---

def cleanup_file(path: str):
    """Function to delete the temporary file after the response is sent."""
    try:
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"Successfully deleted temporary file: {path}")
    except Exception as e:
        logger.error(f"Failed to delete {path}: {e}")

# --- API Endpoints ---

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "Face Recognition API is running",
        "docs": "/docs"
    }

@app.post("/upload-face", status_code=201)
async def upload_face(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    latitude: float = 0.0,
    longitude: float = 0.0
):
    """
    Uploads an image, extracts faces, and stores them in Supabase.
    The local file is deleted immediately after processing.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    # Generate a unique absolute path to avoid Windows permission/path issues
    file_ext = os.path.splitext(file.filename)[1] or ".jpg"
    temp_filename = f"upload_{uuid.uuid4()}{file_ext}"
    temp_path = os.path.abspath(temp_filename)

    try:
        # Save the uploaded file to disk
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # CRITICAL: Close the FastAPI file handle so the OS can delete it later
        await file.close()

        # Call your logic to process and store in Supabase
        # (This should return the list of faces it found and saved)
        stored_faces = store_face_to_supabase(temp_path, latitude, longitude)

        # Add deletion to background tasks so the user doesn't have to wait
        background_tasks.add_task(cleanup_file, temp_path)

        return {
            "status": "success",
            "message": f"Processed {len(stored_faces) if stored_faces else 0} faces.",
            "data": stored_faces
        }

    except Exception as e:
        # If something fails, attempt to clean up before raising error
        cleanup_file(temp_path)
        logger.error(f"Upload Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@app.post("/search-face")
async def search_face(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    threshold: float = 0.45
):
    """
    Takes an image, finds matches in Supabase, and returns the best results.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    file_ext = os.path.splitext(file.filename)[1] or ".jpg"
    temp_filename = f"query_{uuid.uuid4()}{file_ext}"
    temp_path = os.path.abspath(temp_filename)

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        await file.close()

        # Perform the search
        results = search_face_in_supabase(temp_path, threshold=threshold)

        background_tasks.add_task(cleanup_file, temp_path)

        return {
            "status": "success",
            "match_count": len(results),
            "matches": results
        }

    except Exception as e:
        cleanup_file(temp_path)
        logger.error(f"Search Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search execution failed: {str(e)}")

@app.get("/health")
def health():
    """Endpoint for monitoring services (Render/HuggingFace use this)."""
    return {"status": "healthy"}