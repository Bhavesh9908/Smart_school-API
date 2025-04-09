from ultralytics import YOLO
import cv2

# ✅ Load your trained object detection model
model = YOLO("C:\Users\Devesh\Desktop\smart_school_api\perfect.pt")

# ✅ Nutrition metadata for each class (per serving)
nutrition_info = {
    "Chapati": {"calories": 120, "protein": 3, "fat": 3, "carbs": 20},
    "Chawali": {"calories": 220, "protein": 13, "fat": 3, "carbs": 35},
    "Curry": {"calories": 180, "protein": 5, "fat": 9, "carbs": 20},
    "Egg": {"calories": 78, "protein": 6, "fat": 5, "carbs": 0.6},
    "Rice": {"calories": 200, "protein": 4, "fat": 0.5, "carbs": 45},
    "Mixed Veg": {"calories": 150, "protein": 4, "fat": 7, "carbs": 16}
}

# ✅ Load the test image
image_path = "C:/Users/ADMIN/Desktop/PM Poshan/thali2.jpg"
img = cv2.imread(image_path)

# ✅ Run inference
results = model(image_path)

# ✅ Extract and overlay predictions
output_texts = []

for result in results:
    boxes = result.boxes
    names = result.names

    for box in boxes:
        cls_id = int(box.cls[0].item())
        conf = box.conf[0].item()
        class_name = names.get(cls_id, "Unknown")

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # ✅ Get nutrition info if available
        if class_name in nutrition_info:
            nutrients = nutrition_info[class_name]
            label = f"{class_name} ({conf:.2f})"
            nutri_text = f"{nutrients['calories']}kcal | P:{nutrients['protein']}g F:{nutrients['fat']}g C:{nutrients['carbs']}g"
        else:
            label = f"{class_name} ({conf:.2f})"
            nutri_text = "Nutritional Info: N/A"

        # ✅ Overlay text on image
        cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.putText(img, nutri_text, (x1, y2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        output_texts.append(f"{label}\n{nutri_text}")

# ✅ Resize image if too large
max_display_width = 1800
height, width = img.shape[:2]
if width > max_display_width:
    scaling_factor = max_display_width / width
    img = cv2.resize(img, (int(width * scaling_factor), int(height * scaling_factor)))

# ✅ Print results to console
for text in output_texts:
    print(text)
    print("-" * 40)

# ✅ Display final annotated image
cv2.imshow("Prediction with Nutrition Info", img)
cv2.waitKey(0)
cv2.destroyAllWindows()
