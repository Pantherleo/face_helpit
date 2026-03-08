# upload_store.py

'''import uuid
from face_utils import extract_embeddings
from supabase_utils import supabase


# Store face with embeddings to Supabase (image + metadata)
def store_face_to_supabase(image_path, latitude, longitude):
    """Extract face embeddings and store both image and embeddings in Supabase"""
    
    # Read image
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    # Extract embeddings
    embeddings = extract_embeddings(image_path)
    
    if len(embeddings) == 0:
        print("No faces detected in image")
        return []
    
    stored_faces = []
    
    for idx, emb in enumerate(embeddings):

        # Generate unique ID for this face
        face_id = str(uuid.uuid4())
        
        # Upload image to Supabase storage
        image_name = f"{face_id}_{idx}.jpg"
        supabase.storage.from_("faces").upload(image_name, image_data)
        image_url = supabase.storage.from_("faces").get_public_url(image_name)
        
        # Store embedding metadata in database
        face_record = {
            "id": face_id,
            "embedding": emb.tolist(),
            "latitude": latitude,
            "longitude": longitude,
            "image_url": image_url
        }
        
        supabase.table("faces").insert(face_record).execute()
        stored_faces.append(face_record)

        print(f"Stored face {idx + 1} with ID: {face_id}")
    
    return stored_faces'''
# upload_store.py

import uuid
from face_utils import extract_embeddings
from supabase_utils import supabase
from get_location import get_location


# Store face with embeddings to Supabase (image + metadata)
def store_face_to_supabase(image_path, latitude=None, longitude=None):
    """Extract face embeddings and store both image and embeddings in Supabase"""

    # If location not provided, try to detect
    if latitude is None or longitude is None:
        latitude, longitude = get_location()

    # Read image
    with open(image_path, 'rb') as f:
        image_data = f.read()

    # Extract embeddings
    embeddings = extract_embeddings(image_path)

    if len(embeddings) == 0:
        print("No faces detected in image")
        return []

    stored_faces = []

    for idx, emb in enumerate(embeddings):

        # Generate unique ID for this face
        face_id = str(uuid.uuid4())

        # Upload image to Supabase storage
        image_name = f"{face_id}_{idx}.jpg"
        supabase.storage.from_("faces").upload(image_name, image_data)

        image_url = supabase.storage.from_("faces").get_public_url(image_name)

        # Store embedding metadata in database
        face_record = {
            "id": face_id,
            "embedding": emb.tolist(),
            "latitude": latitude,
            "longitude": longitude,
            "image_url": image_url
        }

        supabase.table("faces").insert(face_record).execute()

        stored_faces.append(face_record)

        print(f"Stored face {idx + 1} with ID: {face_id}")

    return stored_faces