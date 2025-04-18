from flask import Flask, request, render_template_string, send_from_directory, jsonify
from werkzeug.utils import secure_filename
import os
import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO
import cloudinary
import cloudinary.uploader
import uuid
import json
import urllib.request

# === Cloudinary Config ===
cloudinary.config(
    cloud_name="da4mdjezu",
    api_key="493281977135412",
    api_secret="P5xxU64uEjNZy6wITFM5pD5Qu54"
)

app = Flask(__name__)
model = YOLO("perfect.pt")

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

@app.route("/", methods=["GET", "POST"])
def upload_image():
    if request.method == "POST":
        image_file = request.files["image"]
        if not image_file:
            return "<script>alert('Please upload a valid image!'); window.location.href='/'</script>"

        filename = secure_filename(image_file.filename)
        os.makedirs("uploads", exist_ok=True)
        image_path = os.path.join("uploads", filename)

        img = Image.open(image_file.stream)
        img = img.resize((800, 600))
        img.save(image_path)

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
                cv2.putText(img_cv, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

                if class_name in nutrition_info:
                    detected_items[class_name] = detected_items.get(class_name, 0) + 1

        if not detected_items:
            return "<script>alert('No recognizable food item detected. Please upload a valid food image.'); window.location.href='/'</script>"

        # Save and upload image to Cloudinary
        annotated_name = "annotated_" + filename
        annotated_path = os.path.join("uploads", annotated_name)
        cv2.imwrite(annotated_path, img_cv)

        uploaded = cloudinary.uploader.upload(annotated_path)
        cloud_url = uploaded["secure_url"]

        # Quantity input form
        quantity_form = ""
        for item in detected_items:
            if nutrition_info[item]["type"] == "count":
                quantity_form += f'<label>{item} (count):</label><input type="number" name="{item}" min="0" value="{detected_items[item]}"><br>'
            else:
                quantity_form += f'<label>{item} (grams):</label><input type="number" name="{item}" min="0" value="100"><br>'

        return render_template_string(f"""
            <html>
            <head><title>Confirm Quantities</title></head>
            <body style="font-family:sans-serif;text-align:center;">
                <h2>Confirm Quantity for Detected Items</h2>
                <form action="/calculate" method="POST">
                    {quantity_form}
                    <input type="hidden" name="image_url" value="{cloud_url}">
                    <br><input type="submit" value="Calculate Nutrition">
                </form>
                <img src="{cloud_url}" width="80%">
            </body>
            </html>
        """)

    return '''
        <h2>Upload a Food Image for Nutrition Analysis</h2>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="image" accept="image/*" required>
            <input type="submit" value="Predict">
        </form>
    '''

@app.route("/calculate", methods=["POST"])
def calculate_nutrition():
    total_nutrition = {"calories": 0, "protein": 0, "fat": 0, "carbs": 0}
    cloud_url = request.form["image_url"]
    food_data = {}

    for item in nutrition_info:
        qty = request.form.get(item)
        if qty:
            try:
                qty = float(qty)
                info = nutrition_info[item]
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
            except:
                continue

    total_calories = round(total_nutrition["calories"], 1)

    # Download annotated image
    response = urllib.request.urlopen(cloud_url)
    img_array = np.asarray(bytearray(response.read()), dtype=np.uint8)
    image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    # Annotate with total calories
    cv2.putText(image, f"Total Calories: {total_calories} kcal", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

    # Save final image
    os.makedirs("uploads", exist_ok=True)
    final_path = os.path.join("uploads", f"final_{uuid.uuid4().hex}.jpg")
    cv2.imwrite(final_path, image)

    # Upload final image to Cloudinary
    final_uploaded = cloudinary.uploader.upload(final_path)
    final_url = final_uploaded["secure_url"]

    # Build final JSON
    result = {
        "annotated_image_url": final_url,
        "nutritional_summary": food_data,
        "total": {
            "calories": total_calories,
            "protein": round(total_nutrition["protein"], 1),
            "fat": round(total_nutrition["fat"], 1),
            "carbs": round(total_nutrition["carbs"], 1)
        }
    }

    # Save JSON locally and upload to Cloudinary
    json_filename = f"nutrition_{uuid.uuid4().hex}.json"
    json_path = os.path.join("uploads", json_filename)
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2)

    uploaded_json = cloudinary.uploader.upload(json_path, resource_type="raw")
    json_url = uploaded_json["secure_url"]
    result["nutrition_json_url"] = json_url

    return jsonify(result)

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory("uploads", filename)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
