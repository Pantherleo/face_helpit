"""
Shared Face Recognition Utilities
Provides common functions for face detection, embedding extraction, and Supabase integration
"""

import cv2
import numpy as np
from insightface.app import FaceAnalysis
from supabase import create_client
import uuid
from typing import List, Dict, Tuple, Optional

# -------- Configuration --------
SUPABASE_URL = "https://pallguhnynvborekzixi.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBhbGxndWhueW52Ym9yZWt6aXhpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI4NjU4ODcsImV4cCI6MjA4ODQ0MTg4N30.3656coe24tUYI0F5tTSbPD44A7NsXjwEVbFV0EQnumM"

# -------- Initialize Supabase --------
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------- Initialize Face Model --------
face_model = None

def initialize_face_model():
    """Initialize the face analysis model (run once)"""
    global face_model
    if face_model is None:
        print("Initializing face model...")
        face_model = FaceAnalysis(name="buffalo_l")
        face_model.prepare(ctx_id=-1, det_size=(640, 640))
        print("Face model ready!")
    return face_model


# -------- Cosine Similarity --------
def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors"""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


# -------- Extract Embeddings --------
def extract_embeddings(image: np.ndarray) -> List[np.ndarray]:
    """
    Extract face embeddings from an image
    
    Args:
        image: OpenCV image array (BGR format)
    
    Returns:
        List of normalized embedding vectors
    """
    model = initialize_face_model()
    faces = model.get(image)
    embeddings = []

    for face in faces:
        emb = face.embedding
        # Normalize embedding
        emb = emb / np.linalg.norm(emb)
        embeddings.append(emb)

    return embeddings


def extract_embeddings_from_file(image_path: str) -> List[np.ndarray]:
    """Extract embeddings from an image file"""
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    return extract_embeddings(img)


# -------- Crop Faces --------
def extract_and_crop_faces(image: np.ndarray) -> List[np.ndarray]:
    """
    Extract and crop individual faces from an image
    
    Args:
        image: OpenCV image array (BGR format)
    
    Returns:
        List of cropped face images
    """
    model = initialize_face_model()
    faces = model.get(image)
    cropped_faces = []

    for face in faces:
        bbox = face.bbox.astype(int)
        x1, y1, x2, y2 = bbox
        cropped = image[y1:y2, x1:x2]
        cropped_faces.append(cropped)

    return cropped_faces


# -------- Supabase Operations --------
def store_face_to_supabase(
    image_data: bytes,
    latitude: float = 0,
    longitude: float = 0,
    metadata: Optional[Dict] = None
) -> List[Dict]:
    """
    Store face embeddings and image to Supabase
    
    Args:
        image_data: Image bytes
        latitude: Location latitude
        longitude: Location longitude
        metadata: Additional metadata to store
    
    Returns:
        List of stored face records with IDs
    """
    # Decode image
    nparr = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image is None:
        raise ValueError("Invalid image format")
    
    # Extract embeddings
    embeddings = extract_embeddings(image)
    
    if len(embeddings) == 0:
        return []
    
    stored_faces = []
    
    # Upload image to storage
    file_name = f"{str(uuid.uuid4())}.jpg"
    supabase.storage.from_("faces").upload(file_name, image_data)
    image_url = supabase.storage.from_("faces").get_public_url(file_name)
    
    # Store each embedding
    for idx, emb in enumerate(embeddings):
        face_id = str(uuid.uuid4())
        
        face_record = {
            "id": face_id,
            "embedding": emb.tolist(),
            "latitude": latitude,
            "longitude": longitude,
            "image_url": image_url,
            "image_name": file_name
        }
        
        # Add optional metadata
        if metadata:
            face_record.update(metadata)
        
        supabase.table("faces").insert(face_record).execute()
        stored_faces.append(face_record)
    
    return stored_faces


def load_all_faces_from_supabase() -> List[Dict]:
    """Load all stored face embeddings from Supabase"""
    try:
        response = supabase.table("faces").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error loading faces: {e}")
        return []


def search_faces_in_supabase(
    image: np.ndarray,
    threshold: float = 0.45,
    max_results: Optional[int] = None
) -> List[Dict]:
    """
    Search for matching faces in Supabase database
    
    Args:
        image: OpenCV image array (BGR format)
        threshold: Similarity threshold (0-1)
        max_results: Maximum number of results to return (None for all)
    
    Returns:
        List of matching faces sorted by similarity
    """
    embeddings = extract_embeddings(image)
    
    if len(embeddings) == 0:
        return []
    
    matches = []
    db_faces = load_all_faces_from_supabase()
    
    for query_idx, query_emb in enumerate(embeddings):
        for stored_face in db_faces:
            stored_emb = np.array(stored_face["embedding"])
            sim = cosine_similarity(query_emb, stored_emb)
            
            if sim > threshold:
                match = {
                    "query_face_id": query_idx,
                    "stored_face_id": stored_face["id"],
                    "similarity": float(sim),
                    "latitude": stored_face["latitude"],
                    "longitude": stored_face["longitude"],
                    "image_url": stored_face["image_url"],
                    "image_name": stored_face.get("image_name", "")
                }
                matches.append(match)
    
    # Sort by similarity descending
    matches.sort(key=lambda x: x["similarity"], reverse=True)
    
    if max_results:
        matches = matches[:max_results]
    
    return matches


def get_database_stats() -> Dict:
    """Get statistics about the face database"""
    db_faces = load_all_faces_from_supabase()
    
    return {
        "total_faces": len(db_faces),
        "storage_used": "See Supabase dashboard",
        "ready": True
    }


def delete_face_from_supabase(face_id: str) -> bool:
    """Delete a face record from Supabase"""
    try:
        supabase.table("faces").delete().eq("id", face_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting face: {e}")
        return False
