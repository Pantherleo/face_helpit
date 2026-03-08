'''import numpy as np
import ast
import cv2
from typing import List, Dict, Optional
from supabase_utils import supabase
from face_utils import extract_embeddings

def load_faces_from_supabase() -> List[Dict]:
    """Fetch all stored face embeddings, newest first."""
    try:
        # Ordering by created_at DESC ensures the first match we encounter for any 
        # duplicate person is the most recent one.
        response = supabase.table("faces").select("*").order("created_at", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error loading faces: {e}")
        return []

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def parse_embedding(embedding_data) -> np.ndarray:
    if isinstance(embedding_data, str):
        embedding_data = ast.literal_eval(embedding_data)
    return np.array(embedding_data, dtype=np.float32)

def search_face_in_supabase(
    image_path: str, 
    threshold: float = 0.45,
    verbose: bool = False
) -> List[Dict]:
    """
    Returns ALL unique people matched, showing only their LATEST sighting/timestamp.
    """
    try:
        # 1. Extract query embeddings
        embeddings = extract_embeddings(image_path)
        if not embeddings:
            if verbose: print("No face detected")
            return []
        
        # Normalize the first face found in the query
        query_emb = embeddings[0]
        query_emb = query_emb / np.linalg.norm(query_emb)
        
        # 2. Fetch all data from Supabase
        db_faces = load_faces_from_supabase()
        if not db_faces:
            return []
        
        # 3. Use a dictionary to store only the BEST/LATEST match for each unique identity
        # Key: A unique identifier (like person_id or name), Value: Match data
        unique_results = {}

        for stored_face in db_faces:
            try:
                stored_emb = parse_embedding(stored_face["embedding"])
                stored_emb = stored_emb / np.linalg.norm(stored_emb)
                
                sim = cosine_similarity(query_emb, stored_emb)

                if sim > threshold:
                    # Logic: If your DB has a 'person_name' or 'person_id', use that as the key.
                    # If not, we use 'id' (which makes every record unique).
                    # Assuming you want to group by a person's identity:
                    person_key = stored_face.get("person_id", stored_face["id"])

                    match_data = {
                        "similarity": round(float(sim), 4),
                        "id": stored_face["id"],
                        "created_at": stored_face.get("created_at"),
                        "latitude": stored_face.get("latitude", 0),
                        "longitude": stored_face.get("longitude", 0),
                        "image_url": stored_face.get("image_url"),
                    }

                    # Because load_faces_from_supabase is ordered by NEWEST first,
                    # we only add the person if they haven't been seen yet.
                    if person_key not in unique_results:
                        unique_results[person_key] = match_data
                    # OR: if you want the HIGHEST similarity instead of NEWEST, 
                    # you would check if sim > unique_results[person_key]["similarity"]
            except:
                continue
        
        # Convert dictionary back to a list
        final_list = list(unique_results.values())
        
        # Sort by similarity so the most likely matches are at the top
        final_list.sort(key=lambda x: x["similarity"], reverse=True)

        if verbose: print(f"Found {len(final_list)} unique matches above threshold.")
        return final_list
        
    except Exception as e:
        print(f"Search error: {e}")
        return []'''

'''import numpy as np
import ast
from typing import List, Dict
from supabase_utils import supabase
from face_utils import extract_embeddings

def load_faces_from_supabase() -> List[Dict]:
    """
    Fetch all stored face embeddings.
    Strictly ordered by created_at DESC to ensure latest images come first.
    """
    try:
        # We order by created_at descending at the database level.
        # This is faster than sorting in Python.
        response = supabase.table("faces") \
            .select("*") \
            .order("created_at", desc=True) \
            .execute()
        
        return response.data if response.data else []
    except Exception as e:
        print(f"Error loading faces: {e}")
        return []

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate similarity score (0 to 1)"""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0: return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

def search_face_in_supabase(image_path: str, threshold: float = 0.45) -> List[Dict]:
    """
    Returns ALL matching images ordered by the LATEST timestamp first.
    """
    try:
        # 1. Extract query face
        embeddings = extract_embeddings(image_path)
        if not embeddings:
            return []
        
        query_emb = embeddings[0]
        
        # 2. Get DB data (Already sorted by Newest -> Oldest)
        db_faces = load_faces_from_supabase()
        
        results = []

        # 3. Filter by similarity
        for face in db_faces:
            # Convert stored string/list to numpy array
            stored_emb = np.array(
                ast.literal_eval(face["embedding"]) if isinstance(face["embedding"], str) else face["embedding"]
            )
            
            sim = cosine_similarity(query_emb, stored_emb)
            
            # Only keep it if it's a match
            if sim > threshold:
                # Add the similarity score to the record
                face["similarity_score"] = round(sim, 4)
                
                # Remove the heavy embedding vector before returning to the UI
                face_output = {k: v for k, v in face.items() if k != "embedding"}
                
                results.append(face_output)

        # IMPORTANT: We DO NOT sort by similarity here. 
        # If we sort by similarity, we break your "Latest Image First" rule.
        # The list 'results' is already in chronological order from Step 2.
        
        return results
        
    except Exception as e:
        print(f"Search error: {e}")
        return []'''

import numpy as np
import ast
from supabase_utils import supabase
from face_utils import extract_embeddings

def search_face_in_supabase(image_path: str, threshold: float = 0.45):
    """
    Returns EVERY match found in Supabase, ordered by the latest sighting first.
    """
    try:
        # 1. Extract query embedding
        embeddings = extract_embeddings(image_path)
        if not embeddings:
            return []
        
        query_emb = embeddings[0]
        query_emb = query_emb / np.linalg.norm(query_emb)

        # 2. Fetch from Supabase - ORDER BY created_at DESC is the key!
        response = supabase.table("faces")\
            .select("*")\
            .order("created_at", desc=True)\
            .execute()
        
        db_faces = response.data if response.data else []
        results = []

        # 3. Iterate through every single record in the DB
        for face in db_faces:
            try:
                # Parse and normalize stored embedding
                stored_emb = np.array(
                    ast.literal_eval(face["embedding"]) if isinstance(face["embedding"], str) else face["embedding"]
                )
                stored_emb = stored_emb / np.linalg.norm(stored_emb)
                
                # Calculate similarity
                sim = float(np.dot(query_emb, stored_emb))

                if sim > threshold:
                    # Capture every match. Do NOT check for duplicates here.
                    match_data = {
                        "similarity": round(sim, 4),
                        "id": face["id"],
                        "created_at": face.get("created_at"),
                        "latitude": face.get("latitude"),
                        "longitude": face.get("longitude"),
                        "image_url": face.get("image_url")
                    }
                    results.append(match_data)
            except Exception:
                continue

        # Because db_faces was already sorted by DESC created_at, 
        # 'results' is now naturally ordered from newest sighting to oldest.
        return results
        
    except Exception as e:
        print(f"Search error: {e}")
        return []