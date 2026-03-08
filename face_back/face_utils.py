# face_utils.py
import cv2
import numpy as np
import insightface

# Pre-load the model once
model = insightface.app.FaceAnalysis(name="buffalo_l")
model.prepare(ctx_id=0)

def extract_embeddings(image_path):
    # 1. Read the file into memory as bytes
    with open(image_path, "rb") as f:
        chunk = f.read()
    
    # 2. Convert bytes to a numpy array (The file handle is now CLOSED)
    nparr = np.frombuffer(chunk, np.uint8)
    
    # 3. Decode the array into an OpenCV image format
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        print(f"Error: Could not decode image at {image_path}")
        return []

    # 4. Run InsightFace on the image in memory
    faces = model.get(img)

    embeddings = []
    for face in faces:
        embeddings.append(face.embedding)

    return embeddings