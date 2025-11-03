import os
import cv2
import time
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS # Import CORS
from dotenv import load_dotenv
from google.cloud import aiplatform
import google.generativeai as genai
import google.cloud.storage as storage

load_dotenv()

app = Flask(__name__, static_folder='../frontend', static_url_path='/frontend')
CORS(app) # Enable CORS for all routes

# Configure Google Cloud AI Platform (Only for GCS, not for Gemini API directly)
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1") # Default to us-central1
# aiplatform.init(project=PROJECT_ID, location=LOCATION) # Remove aiplatform.init for direct genai usage

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-2.5-flash') # Updated to an available multimodal model

# Configure Google Cloud Storage
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
storage_client = storage.Client(project=PROJECT_ID) # PROJECT_ID is still needed for GCS
bucket = storage_client.bucket(GCS_BUCKET_NAME)

def extract_frames(video_path, frames_dir, interval=1):
    """Extracts frames from a video at a given interval."""
    if not os.path.exists(frames_dir):
        os.makedirs(frames_dir)

    vidcap = cv2.VideoCapture(video_path)
    fps = vidcap.get(cv2.CAP_PROP_FPS)
    frame_count = 0
    success, image = vidcap.read()
    extracted_frame_paths = []

    while success:
        if frame_count % (int(fps) * interval) == 0:
            frame_filename = os.path.join(frames_dir, f"frame_{frame_count:04d}.jpg")
            cv2.imwrite(frame_filename, image)
            extracted_frame_paths.append(frame_filename)
        success, image = vidcap.read()
        frame_count += 1
    vidcap.release()
    return extracted_frame_paths

def upload_to_gcs(file_path, destination_blob_name):
    """Uploads a file to Google Cloud Storage."""
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(file_path)
    return f"gs://{GCS_BUCKET_NAME}/{destination_blob_name}"

def delete_gcs_blob(blob_name):
    """Deletes a blob from Google Cloud Storage."""
    blob = bucket.blob(blob_name)
    blob.delete()

@app.route('/')
def serve_index():
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def serve_static(path):
    if path.startswith('frontend/'):
        return app.send_static_file(path.replace('frontend/', ''))
    return app.send_static_file(path)

@app.route('/list-models')
def list_models():
    try:
        models = genai.list_models()
        model_names = [{"name": m.name, "supported_generation_methods": m.supported_generation_methods} for m in models]
        return jsonify(model_names)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analyze-video', methods=['POST'])
def analyze_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video_file = request.files['video']
    if video_file.filename == '':
        return jsonify({"error": "No selected video file"}), 400

    session_id = str(uuid.uuid4())
    temp_dir = os.path.join("/tmp", session_id)
    os.makedirs(temp_dir, exist_ok=True)
    video_path = os.path.join(temp_dir, video_file.filename)
    video_file.save(video_path)

    gcs_uris = []
    uploaded_blob_names = []
    try:
        # Extract frames
        frames_dir = os.path.join(temp_dir, "frames")
        extracted_frame_paths = extract_frames(video_path, frames_dir, interval=2) # Extract a frame every 2 seconds

        # Upload frames to GCS
        for frame_path in extracted_frame_paths:
            blob_name = f"{session_id}/{os.path.basename(frame_path)}"
            gcs_uri = upload_to_gcs(frame_path, blob_name)
            gcs_uris.append(gcs_uri)
            uploaded_blob_names.append(blob_name)

        if not gcs_uris:
            return jsonify({"error": "No frames extracted or uploaded"}), 500

        # Prepare content for Gemini
        prompt_parts = [
            "Analyze the following video frames for potential risk situations. Specifically, determine if a 'fall', 'collapse', or 'seizure' is detected. Respond with 'DETECTED: [risk_type]' if a risk is found, otherwise respond with 'NO_RISK'. Provide a brief explanation if a risk is detected.",
        ]
        local_frame_paths = []
        for uri in gcs_uris:
            # Download GCS image to a local temporary file
            blob_name = uri.split(f"gs://{GCS_BUCKET_NAME}/")[1]
            local_frame_path = os.path.join(temp_dir, os.path.basename(blob_name))
            bucket.blob(blob_name).download_to_filename(local_frame_path)
            local_frame_paths.append(local_frame_path)
            prompt_parts.append(genai.upload_file(local_frame_path))

        # Call Gemini API
        response = model.generate_content(prompt_parts)

        # Parse Gemini's response
        analysis_result = {
            "status": "success",
            "potential_risk": "low",
            "details": "특정 위험 감지 안됨."
        }

        response_text = response.text.upper() # Convert to uppercase for consistent parsing
        if "DETECTED: FALL" in response_text or "DETECTED: COLLAPSE" in response_text:
            analysis_result["potential_risk"] = "high"
            analysis_result["details"] = "떨어짐 또는 쓰러짐 감지됨."
        elif "DETECTED: SEIZURE" in response_text:
            analysis_result["potential_risk"] = "high"
            analysis_result["details"] = "발작 감지됨."
        # If no specific DETECTED tag, it's NO_RISK by default, or we can include Gemini's full response if it's not NO_RISK
        elif "NO_RISK" not in response_text:
            analysis_result["details"] = response.text # Include Gemini's full response if it's not explicitly NO_RISK

        return jsonify(analysis_result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up temporary files
        if os.path.exists(temp_dir):
            for root, dirs, files in os.walk(temp_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(temp_dir)

        # Clean up local temporary frame files
        for local_path in local_frame_paths:
            if os.path.exists(local_path):
                os.remove(local_path)

        # Clean up GCS objects
        for blob_name in uploaded_blob_names:
            try:
                delete_gcs_blob(blob_name)
            except Exception as e:
                print(f"Error deleting GCS blob {blob_name}: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
