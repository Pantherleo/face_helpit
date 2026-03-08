"""
Facial Recognition Pipeline using InsightFace
Face Detection, Extraction & Similarity Search System with Geotag Tracking
InsightFace provides superior face detection and embedding extraction
"""

import numpy as np
import pandas as pd
import cv2
from PIL import Image
from PIL.ExifTags import TAGS
import os
from pathlib import Path
import pickle
import json
from typing import List, Tuple, Dict, Optional
from datetime import datetime
from scipy.spatial.distance import cosine
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# InsightFace imports
try:
    import insightface
    print("✓ InsightFace available")
except ImportError:
    print("Installing insightface...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "insightface"])
    import insightface
    print("✓ InsightFace installed")


class FacialRecognitionPipelineInsightFace:
    """
    Facial recognition pipeline with InsightFace for superior face detection
    and embedding extraction with geotag tracking
    """

    def __init__(self, database_dir: str = "./face_database_insightface"):
        """
        Initialize the InsightFace pipeline

        Args:
            database_dir: Directory to store face embeddings and metadata
        """
        self.database_dir = database_dir
        
        # Use DataFrame for structured storage: 512 embedding columns + metadata
        embedding_cols = [f'embedding_{i}' for i in range(512)]
        metadata_cols = ['latitude', 'longitude', 'altitude', 'timestamp', 'filename', 'person_id', 'face_location', 'confidence']
        self.faces_db = pd.DataFrame(columns=embedding_cols + metadata_cols)

        # Initialize InsightFace
        print("Initializing InsightFace models...")
        self.detector = insightface.app.FaceAnalysis(providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
        self.detector.prepare(ctx_id=0, det_size=(640, 640))
        print("✓ InsightFace detector ready (includes detection & embedding)")

        Path(database_dir).mkdir(exist_ok=True)
        self.db_file = os.path.join(database_dir, 'faces_database.pkl')
        self.metadata_file = os.path.join(database_dir, 'metadata.json')

        self.load_database()

    def extract_geotag(self, image_path: str) -> Dict:
        """
        Extract geotag (GPS coordinates) from image EXIF data

        Args:
            image_path: Path to the image file

        Returns:
            Dictionary with latitude, longitude, timestamp, and location info
        """
        geotag = {
            'latitude': None,
            'longitude': None,
            'altitude': None,
            'timestamp': None,
            'filename': os.path.basename(image_path)
        }

        try:
            image = Image.open(image_path)
            exif_data = image._getexif()

            if exif_data is not None:
                for tag_id, value in exif_data.items():
                    tag_name = TAGS.get(tag_id, tag_id)

                    # Extract GPS info
                    if tag_name == 'GPSInfo':
                        gps_data = {}
                        for t in value:
                            sub_tag_name = TAGS.get(t, t)
                            gps_data[sub_tag_name] = value[t]

                        if 'GPSLatitude' in gps_data and 'GPSLongitude' in gps_data:
                            geotag['latitude'] = self._convert_to_degrees(gps_data['GPSLatitude'])
                            geotag['longitude'] = self._convert_to_degrees(gps_data['GPSLongitude'])

                        if 'GPSAltitude' in gps_data:
                            geotag['altitude'] = float(gps_data['GPSAltitude'])

                    # Extract timestamp
                    elif tag_name == 'DateTime':
                        geotag['timestamp'] = str(value)

        except Exception as e:
            print(f"Warning: Could not extract EXIF data: {e}")

        # Add current timestamp if not found in EXIF
        if geotag['timestamp'] is None:
            geotag['timestamp'] = datetime.now().isoformat()

        return geotag

    @staticmethod
    def _convert_to_degrees(value):
        """Convert GPS coordinates to degrees"""
        d, m, s = value
        return d + (m / 60.0) + (s / 3600.0)

    def _extract_face_embeddings(self, image_path: str) -> List[Dict]:
        """
        Extract face embeddings using InsightFace WITHOUT adding to database
        Used for search/query operations

        Args:
            image_path: Path to the image file

        Returns:
            List of dictionaries containing face embeddings and geotag
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Extract geotag
        geotag = self.extract_geotag(image_path)

        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not read image: {image_path}")

        # Detect faces using InsightFace
        faces = self.detector.get(image)
        print(f"DEBUG: extracted {len(faces)} face(s) from query image {image_path}")
        if len(faces) > 0:
            face_bboxes = [(f.bbox[0], f.bbox[1], f.bbox[2]-f.bbox[0], f.bbox[3]-f.bbox[1]) for f in faces]
            print(f"  bboxes: {face_bboxes}")

        face_data_list = []

        for idx, face in enumerate(faces):
            try:
                # InsightFace already computed the embedding (512D vector)
                embedding = face.embedding
                
                # Extract face region for storage
                bbox = face.bbox
                x, y, w, h = int(bbox[0]), int(bbox[1]), int(bbox[2]-bbox[0]), int(bbox[3]-bbox[1])
                face_img = image[y:y+h, x:x+w]

                face_record = {
                    'embedding': embedding,
                    'face_image': face_img,
                    'geotag': geotag,
                    'face_location': (x, y, w, h),
                    'confidence': float(face.det_score)  # Detection confidence from InsightFace
                }

                face_data_list.append(face_record)

            except Exception as e:
                print(f"Warning: Could not process face {idx} in {image_path}: {e}")
                continue

        print(f"✓ Extracted {len(face_data_list)} face(s) from {image_path}")
        print(f"  Location: {geotag['latitude']}, {geotag['longitude']}")

        return face_data_list

    def detect_and_extract_faces(self, image_path: str, person_id: str = None) -> List[Dict]:
        """
        Detect faces using InsightFace and extract their embeddings
        Adds faces to the database for registration

        Args:
            image_path: Path to the image file
            person_id: Identifier for the person (optional)

        Returns:
            List of dictionaries containing face data and geotag
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Extract geotag
        geotag = self.extract_geotag(image_path)

        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not read image: {image_path}")

        # Detect faces using InsightFace
        faces = self.detector.get(image)
        print(f"DEBUG: registration detected {len(faces)} face(s) in {image_path}")
        if len(faces) > 0:
            face_bboxes = [(f.bbox[0], f.bbox[1], f.bbox[2]-f.bbox[0], f.bbox[3]-f.bbox[1]) for f in faces]
            print(f"  bboxes: {face_bboxes}")

        face_data_list = []

        for idx, face in enumerate(faces):
            try:
                # InsightFace already computed the embedding (512D vector)
                embedding = face.embedding

                # Extract face region
                bbox = face.bbox
                x, y, w, h = int(bbox[0]), int(bbox[1]), int(bbox[2]-bbox[0]), int(bbox[3]-bbox[1])
                face_img = image[y:y+h, x:x+w]

                # Create row data for DataFrame
                row_data = {}
                for i in range(512):
                    row_data[f'embedding_{i}'] = embedding[i]

                row_data.update({
                    'latitude': geotag['latitude'],
                    'longitude': geotag['longitude'],
                    'altitude': geotag['altitude'],
                    'timestamp': datetime.now().isoformat(),
                    'filename': geotag['filename'],
                    'person_id': person_id or f"person_{len(self.faces_db)}",
                    'face_location': (x, y, w, h),
                    'confidence': float(face.det_score)  # Detection confidence from InsightFace
                })

                # Add to DataFrame
                self.faces_db = pd.concat([self.faces_db, pd.DataFrame([row_data])], ignore_index=True)

                face_record = {
                    'embedding': embedding,
                    'face_image': face_img,
                    'geotag': geotag,
                    'person_id': row_data['person_id'],
                    'face_location': row_data['face_location'],
                    'timestamp': row_data['timestamp'],
                    'confidence': row_data['confidence']
                }

                face_data_list.append(face_record)

            except Exception as e:
                print(f"Warning: Could not process face {idx} in {image_path}: {e}")
                continue

        print(f"✓ Found and processed {len(face_data_list)} face(s) in {image_path}")
        print(f"  Location: {geotag['latitude']}, {geotag['longitude']}")

        return face_data_list

    def search_similar_faces(self, query_image_path: str, similarity_threshold: float = 0.4) -> List[Dict]:
        """
        Search for similar faces in database

        Args:
            query_image_path: Path to query image
            similarity_threshold: Cosine similarity threshold (0-1, higher = more similar)

        Returns:
            List of matching faces with their geotags and similarity scores
        """
        if self.faces_db.empty:
            print("Database is empty! Please register faces first.")
            return []

        # Extract faces from query image (without adding to database)
        query_faces = self._extract_face_embeddings(query_image_path)

        if not query_faces:
            print("No faces detected in query image")
            return []

        results = []

        for query_face in query_faces:
            query_embedding = query_face['embedding']
            matches = []

            # Compare with all faces in database
            for idx, db_row in self.faces_db.iterrows():
                db_embedding = np.array([db_row[f'embedding_{i}'] for i in range(512)])

                # Calculate cosine similarity (1 - cosine distance)
                similarity = 1 - cosine(query_embedding, db_embedding)

                if similarity >= similarity_threshold:
                    matches.append({
                        'similarity_score': float(similarity),
                        'person_id': db_row['person_id'],
                        'geotag': {
                            'latitude': db_row['latitude'],
                            'longitude': db_row['longitude'],
                            'altitude': db_row['altitude'],
                            'timestamp': db_row['timestamp'],
                            'filename': db_row['filename']
                        },
                        'last_seen': db_row['timestamp'],
                        'face_location': db_row['face_location']
                    })

            # Sort by similarity score
            matches.sort(key=lambda x: x['similarity_score'], reverse=True)

            result = {
                'query_face': query_face,
                'matches': matches,
                'match_count': len(matches)
            }
            results.append(result)

        return results

    def save_database(self):
        """Save database to disk"""
        try:
            self.faces_db.to_pickle(self.db_file)

            # Save metadata separately
            metadata = {
                'total_faces': len(self.faces_db),
                'last_updated': datetime.now().isoformat(),
                'persons': self.faces_db['person_id'].unique().tolist() if not self.faces_db.empty else [],
                'detector': 'InsightFace'
            }
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            print(f"✓ Database saved with {len(self.faces_db)} faces (InsightFace)")
        except Exception as e:
            print(f"Error saving database: {e}")

    def load_database(self):
        """Load database from disk"""
        if os.path.exists(self.db_file):
            try:
                self.faces_db = pd.read_pickle(self.db_file)
                print(f"✓ Loaded {len(self.faces_db)} faces from database (InsightFace)")
            except Exception as e:
                print(f"Error loading database: {e}")

    def get_person_geotags(self, person_id: str) -> pd.DataFrame:
        """
        Get all geotags for a specific person

        Args:
            person_id: ID of the person

        Returns:
            DataFrame with geotag history
        """
        person_faces = self.faces_db[self.faces_db['person_id'] == person_id]

        if person_faces.empty:
            return pd.DataFrame()

        geotag_history = person_faces[['latitude', 'longitude', 'timestamp', 'filename', 'altitude']].copy()
        return geotag_history

    def visualize_results(self, results: List[Dict], max_matches: int = 8):
        """Visualize search results"""
        for idx, result in enumerate(results):
            query_face = result['query_face']
            matches = result['matches'][:max_matches]

            print(f"\n{'='*60}")
            print(f"Query Face {idx+1}: Found {result['match_count']} match(es)")
            print(f"{'='*60}")
            
            # Show query image's geotag (where the photo was uploaded from)
            print(f"\n[Query Photo Location]")
            print(f"  File: {query_face['geotag']['filename']}")
            print(f"  Latitude: {query_face['geotag']['latitude']}")
            print(f"  Longitude: {query_face['geotag']['longitude']}")
            print(f"  Altitude: {query_face['geotag']['altitude']}")
            print(f"  Timestamp: {query_face['geotag']['timestamp']}")
            print(f"  Detection Confidence: {query_face['confidence']:.4f}")

            if not matches:
                print(f"\nNo matching faces found in database")
                continue

            print(f"\n{'-'*60}")
            print(f"Matching Faces in Database:")
            print(f"{'-'*60}")

            for rank, match in enumerate(matches, 1):
                print(f"\n[Match {rank}]")
                print(f"  Similarity: {match['similarity_score']:.4f} ({match['similarity_score']*100:.2f}%)")
                print(f"  Person ID: {match['person_id']}")
                print(f"  Last Seen Location:")
                print(f"    Latitude: {match['geotag']['latitude']}")
                print(f"    Longitude: {match['geotag']['longitude']}")
                print(f"    Altitude: {match['geotag']['altitude']}")
                print(f"    Timestamp: {match['geotag']['timestamp']}")
                print(f"    File: {match['geotag']['filename']}")


if __name__ == "__main__":
    print("✓ InsightFace Pipeline module loaded successfully!")
    print("\nFeatures:")
    print("  - Superior face detection (handles multiple faces, angles, scales)")
    print("  - Automatic face alignment & embedding")
    print("  - 512D embeddings optimized for face recognition")
    print("  - Geographic tagging from EXIF data")
    print("  - Cosine similarity matching")
