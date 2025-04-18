from flask import Flask, request, render_template_string, send_from_directory
from werkzeug.utils import secure_filename
import os
import numpy as np
import cv2
from ultralytics import YOLO
from PIL import Image

app = Flask(__name__)
model = YOLO("perfect.pt")

# Nutrition values per 100g or per count
nutrition_info = {
    "Rice": {"calories": 200, "protein": 4, "fat": 0.5, "carbs": 45, "type": "gram"},
    "Curry": {"calories": 180, "protein": 5, "fat": 9, "carbs": 20, "type": "gram"},
    "Chapati": {"calories": 120, "protein": 3, "fat": 3, "carbs": 20, "type": "count"},
    "Boiled Egg": {"calories": 70, "protein": 6, "fat": 5, "carbs": 1, "type": "count"},
    "Mixed Veg": {"calories": 150, "protein": 4, "fat": 7, "carbs": 16, "type": "gram"},
    "Chavvali": {"calories": 160, "protein": 8, "fat": 2, "carbs": 30, "type": "gram"},
    "Watana": {"calories": 140, "protein": 7, "fat": 1, "carbs": 25, "type": "gram"},
}

# Maximum allowed image size for processing
MAX_IMAGE_SIZE = (640, 640)  # Resize the image to this fixed size

def resize_image(image):
    """Resizes the image to the desired size (MAX_IMAGE_SIZE)."""
    return image.resize(MAX_IMAGE_SIZE)

@app.route("/", methods=["GET", "POST"])
def upload_image():
    if request.method == "POST":
        image_file = request.files["image"]
        if not image_file:
            return "<script>alert('Please upload a valid image!'); window.location.href='/'</script>"

        filename = secure_filename(image_file.filename)
        os.makedirs("uploads", exist_ok=True)
        image_path = os.path.join("uploads", filename)
        image_file.save(image_path)

        # Open and resize the image using PIL (Pillow)
        img = Image.open(image_path)
        img = resize_image(img)
        img.save(image_path)  # Save the resized image back

        # Convert the image back to OpenCV format
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        results = model(image_path)
        output_texts = []
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
                cv2.rectangle(img_cv, (x1, y1), (x2, y2), (0, 255, 0), 1)

                label = f"{class_name} ({conf:.2f})"
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.4
                thickness = 1
                text_color = (0, 0, 0)
                bg_color = (255, 255, 255)

                cv2.rectangle(img_cv, (x1, y1 - 15), (x1 + 100, y1), bg_color, -1)
                cv2.putText(img_cv, class_name, (x1 + 2, y1 - 2), font, font_scale, text_color, thickness, cv2.LINE_AA)

                if class_name in nutrition_info:
                    detected_items[class_name] = detected_items.get(class_name, 0) + 1

        if not detected_items:
            return "<script>alert('No recognizable food item detected. Please upload a valid food image.'); window.location.href='/'</script>"

        # Save annotated image
        annotated_path = os.path.join("uploads", "annotated_" + filename)
        cv2.imwrite(annotated_path, img_cv)

        # Create quantity form
        quantity_form = ''
        for item in detected_items:
            if nutrition_info[item]["type"] == "count":
                quantity_form += f'<label>{item} (count):</label><input type="number" name="{item}" min="0" value="{detected_items[item]}"><br>'
            else:
                quantity_form += f'<label>{item} (grams):</label><input type="number" name="{item}" min="0" value="100"><br>'

        return render_template_string("""
            <html>
            <head>
                <title>Confirm Quantities</title>
                <style>
                    body { font-family: Arial; padding: 30px; text-align: center; }
                    img { max-width: 90%%; margin-top: 20px; border-radius: 12px; box-shadow: 0 0 12px rgba(0,0,0,0.2); }
                    form input[type='number'] { width: 80px; margin: 5px; padding: 5px; }
                    form input[type='submit'] { padding: 8px 16px; background: #28a745; color: white; border: none; border-radius: 6px; cursor: pointer; }
                </style>
            </head>
            <body>
                <h2>Detected Items: Confirm Quantity</h2>
                <form action="/calculate" method="POST">
                    %s
                    <input type="hidden" name="image_filename" value="%s">
                    <input type="submit" value="Calculate Nutrition">
                </form>
                <img src="/uploads/%s">
            </body>
            </html>
        """ % (quantity_form, "annotated_" + filename, "annotated_" + filename))

    return '''
        <h2>Upload a Food Image for Nutrition Analysis</h2>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="image" accept="image/*" required>
            <input type="submit" value="Predict">
        </form>
    '''

@app.route("/calculate", methods=["POST"])
def calculate_nutrition():
    total = {"calories": 0, "protein": 0, "fat": 0, "carbs": 0}
    summary_lines = []

    for item in nutrition_info:
        qty = request.form.get(item)
        if qty:
            try:
                qty = float(qty)
                data = nutrition_info[item]
                scale = qty if data["type"] == "count" else qty / 100

                cal = data["calories"] * scale
                pro = data["protein"] * scale
                fat = data["fat"] * scale
                carb = data["carbs"] * scale

                summary_lines.append(f"{item} → {cal:.1f}kcal | P:{pro:.1f}g F:{fat:.1f}g C:{carb:.1f}g")

                total["calories"] += cal
                total["protein"] += pro
                total["fat"] += fat
                total["carbs"] += carb
            except:
                continue

    image_filename = request.form["image_filename"]

    return render_template_string("""
        <html>
        <head>
            <title>Nutrition Summary</title>
            <style>
                body { font-family: Arial; padding: 30px; text-align: center; }
                ul { list-style: none; padding: 0; font-size: 15px; }
                li { margin: 6px 0; }
                .total { margin-top: 25px; font-weight: bold; }
                img { max-width: 90%%; border-radius: 12px; margin-top: 20px; box-shadow: 0 0 12px rgba(0,0,0,0.2); }
            </style>
        </head>
        <body>
            <h2>🍱 Final Nutrition Summary</h2>
            <ul>
            {% for line in summary_lines %}
                <li>{{ line }}</li>
            {% endfor %}
            </ul>
            <div class="total">
                🔥 Total: {{ total['calories'] | round(1) }} kcal |
                P: {{ total['protein'] | round(1) }}g |
                F: {{ total['fat'] | round(1) }}g |
                C: {{ total['carbs'] | round(1) }}g
            </div>
            <img src="/uploads/{{ image_filename }}">
            <br><br><a href="/">🔄 Predict Another</a>
        </body>
        </html>
    """, summary_lines=summary_lines, total=total, image_filename=image_filename)

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory("uploads", filename)

if __name__ == "__main__":
    app.run(debug=True, port=10000)
