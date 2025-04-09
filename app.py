from flask import Flask, request, render_template_string
from ultralytics import YOLO
import cv2
import numpy as np
import os
from werkzeug.utils import secure_filename
import base64

app = Flask(__name__)
model = YOLO("perfect.pt")  # ✅ Load your trained model

# ✅ Nutrition data
nutrition_info = {
    "Chapati": {"calories": 120, "protein": 3, "fat": 3, "carbs": 20},
    "Chawali": {"calories": 220, "protein": 13, "fat": 3, "carbs": 35},
    "Curry": {"calories": 180, "protein": 5, "fat": 9, "carbs": 20},
    "Egg": {"calories": 78, "protein": 6, "fat": 5, "carbs": 0.6},
    "Rice": {"calories": 200, "protein": 4, "fat": 0.5, "carbs": 45},
    "Mixed Veg": {"calories": 150, "protein": 4, "fat": 7, "carbs": 16}
}

@app.route("/", methods=["GET", "POST"])
def upload_image():
    if request.method == "POST":
        image_file = request.files["image"]
        if image_file:
            filename = secure_filename(image_file.filename)
            os.makedirs("uploads", exist_ok=True)
            image_path = os.path.join("uploads", filename)
            image_file.save(image_path)

            # ✅ Detection
            img = cv2.imread(image_path)
            results = model(image_path)
            output_texts = []

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
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 1)

                    if class_name in nutrition_info:
                        nutrients = nutrition_info[class_name]
                        label = f"{class_name} ({conf:.2f})"
                        nutri_text = f"{nutrients['calories']}kcal | P:{nutrients['protein']}g F:{nutrients['fat']}g C:{nutrients['carbs']}g"
                    else:
                        label = f"{class_name} ({conf:.2f})"
                        nutri_text = "Nutrition: N/A"

                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.4
                    thickness = 1
                    text_color = (0, 0, 0)
                    bg_color = (255, 255, 255)

                    for idx, line in enumerate([label, nutri_text]):
                        (w, h), _ = cv2.getTextSize(line, font, font_scale, thickness)
                        y_offset = y1 - 10 - idx * (h + 6)
                        y_offset = max(y_offset, 5)

                        cv2.rectangle(img, (x1, y_offset - h), (x1 + w + 4, y_offset + 2), bg_color, -1)
                        cv2.putText(img, line, (x1 + 2, y_offset), font, font_scale, text_color, thickness, cv2.LINE_AA)

                    output_texts.append(f"{label} → {nutri_text}")

            # Convert to base64 for browser
            _, buffer = cv2.imencode('.jpg', img)
            img_str = base64.b64encode(buffer).decode('utf-8')

            return render_template_string("""
                <html>
                <head>
                    <title>Food Nutrition Results</title>
                    <style>
                        body { font-family: Arial, sans-serif; padding: 20px; text-align: center; }
                        ul { list-style: none; padding: 0; }
                        li { margin: 8px 0; font-size: 14px; }
                        img { max-width: 90%; height: auto; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.2); }
                    </style>
                </head>
                <body>
                    <h2>🍱 Nutrition Analysis Result</h2>
                    <ul>
                    {% for line in output_texts %}
                        <li>{{ line }}</li>
                    {% endfor %}
                    </ul>
                    <h3>📸 Annotated Image:</h3>
                    <img src="data:image/jpeg;base64,{{ img_str }}">
                    <br><br>
                    <a href="/">🔁 Predict Another</a>
                </body>
                </html>
            """, output_texts=output_texts, img_str=img_str)

    return '''
        <h2>Upload a Food Image for Nutrition Analysis</h2>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="image" accept="image/*" required>
            <input type="submit" value="Predict">
        </form>
    '''

# ✅ Enable external access (for Render or public servers)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # default 10000 for local testing
    app.run(host="0.0.0.0", port=port)
