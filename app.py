from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO
import cloudinary
import cloudinary.uploader
import uuid
import urllib.request

# Cloudinary Config
cloudinary.config(
    cloud_name="da4mdjezu",
    api_key="493281977135412",
    api_secret="P5xxU64uEjNZy6wITFM5pD5Qu54"
)

app = Flask(__name__)

# Load Models with error handling
try:
    model = YOLO("perfect.pt")
    quality_model = YOLO("good-bad.pt")
except Exception as e:
    print("❌ Model loading failed:", e)

# Nutrition info
nutrition_info = {
    "Rice": {"calories": 200, "protein": 4, "fat": 0.5, "carbs": 45, "type": "gram"},
    "Curry": {"calories": 180, "protein": 5, "fat": 9, "carbs": 20, "type": "gram"},
    "Chapati": {"calories": 120, "protein": 3, "fat": 3, "carbs": 20, "type": "count"},
    "Boiled Egg": {"calories": 70, "protein": 6, "fat": 5, "carbs": 1, "type": "count"},
    "Mixed Veg": {"calories": 150, "protein": 4, "fat": 7, "carbs": 16, "type": "gram"},
    "Chavvali": {"calories": 160, "protein": 8, "fat": 2, "carbs": 30, "type": "gram"},
    "Watana": {"calories": 140, "protein": 7, "fat": 1, "carbs": 25, "type": "gram"},
}

@app.route("/healthz")
def health_check():
    return "OK", 200

@app.route("/", methods=["GET", "POST"])
def upload_image():
    if request.method == "POST":
        image_file = request.files.get("image")
        if not image_file:
            return jsonify({"error": "No image uploaded"}), 400

        filename = secure_filename(image_file.filename)
        os.makedirs("uploads", exist_ok=True)
        image_path = os.path.join("uploads", filename)

        try:
            img = Image.open(image_file.stream)
            img.save(image_path)
        except Exception as e:
            return jsonify({"error": "Failed to read image"}), 500

        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        results = model(image_path)
        detected_items = {}

        for result in results:
            boxes = result.boxes
            names = result.names
            for box in boxes:
                cls_id = int(box.cls[0].item())
                conf = box.conf[0].item()
                if conf < 0.5:
                    continue

                class_name = names.get(cls_id, "Unknown")
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(img_cv, (x1, y1), (x2, y2), (0, 255, 0), 2)
                label = f"{class_name} ({conf:.2f})"
                cv2.putText(img_cv, label, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

                if class_name in nutrition_info:
                    detected_items[class_name] = detected_items.get(class_name, 0) + 1

        if not detected_items:
            return jsonify({"error": "No recognizable food detected"}), 400

        annotated_path = os.path.join("uploads", "annotated_" + filename)
        cv2.imwrite(annotated_path, img_cv)
        uploaded = cloudinary.uploader.upload(annotated_path)
        cloud_url = uploaded["secure_url"]

        total_nutrition = {"calories": 0, "protein": 0, "fat": 0, "carbs": 0}
        food_data = {}

        for item in detected_items:
            info = nutrition_info[item]
            qty = detected_items[item] if info["type"] == "count" else 100
            scale = qty if info["type"] == "count" else qty / 100

            food_data[item] = {
                "calories": round(info["calories"] * scale, 1),
                "protein": round(info["protein"] * scale, 1),
                "fat": round(info["fat"] * scale, 1),
                "carbs": round(info["carbs"] * scale, 1),
                "quantity": qty,
                "unit": info["type"]
            }

            total_nutrition["calories"] += info["calories"] * scale
            total_nutrition["protein"] += info["protein"] * scale
            total_nutrition["fat"] += info["fat"] * scale
            total_nutrition["carbs"] += info["carbs"] * scale

        quality_result = quality_model(image_path)[0]
        names = quality_result.names

        if hasattr(quality_result, "probs") and quality_result.probs is not None:
            confs = quality_result.probs.data.cpu().numpy()
            cls_id = int(np.argmax(confs))
            conf = float(confs[cls_id])
            class_name = names[cls_id].lower() if isinstance(names, list) else names.get(cls_id, "").lower()
            quality_label = "Good" if class_name == "good" and conf > 0.5 else "Bad"
        else:
            quality_label = "Bad"

        result = {
            "annotated_image_url": cloud_url,
            "food_quality": quality_label,
            "nutritional_summary": food_data,
            "total": {
                "calories": round(total_nutrition["calories"], 1),
                "protein": round(total_nutrition["protein"], 1),
                "fat": round(total_nutrition["fat"], 1),
                "carbs": round(total_nutrition["carbs"], 1)
            }
        }

        return jsonify(result)

    return '''
        <h2>Upload a Food Image</h2>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="image" accept="image/*" required>
            <input type="submit" value="Analyze">
        </form>
    '''

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory("uploads", filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)  # Debug=True temporarily to catch crashes
