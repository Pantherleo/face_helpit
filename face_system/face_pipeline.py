import cv2
from insightface.app import FaceAnalysis

print("Program started")

# Load face analysis model
app = FaceAnalysis(name="buffalo_l")
print("Model object created")

# ctx_id=0 uses GPU
app.prepare(ctx_id=0)
print("Model loaded successfully")


def process_image(image_path):

    print("Loading image...")

    image = cv2.imread(image_path)

    print("Image loaded:", image is not None)

    faces = app.get(image)

    print("Faces detected:", len(faces))

    results = []

    for i, face in enumerate(faces):

        bbox = face.bbox.astype(int)
        embedding = face.embedding

        results.append({
            "face_id": i,
            "bbox": bbox.tolist(),
            "embedding": embedding.tolist()
        })

    return results


if __name__ == "__main__":

    print("Starting pipeline")

    faces = process_image("photo_bts_face_recog.jpg")

    print("Faces detected:", len(faces))

    for f in faces:
        print("\nFace ID:", f["face_id"])
        print("Bounding Box:", f["bbox"])
        print("Embedding Length:", len(f["embedding"]))