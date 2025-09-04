import requests
from Model import fn

url = "http://127.0.0.1:5000/api/predict"
image_path = "Foods/chapati/0b59806867.jpg"

with open(image_path, "rb") as f:
    files = {"file": f}
    response = requests.post(url, files=files)

if response.status_code == 200:
    data = response.json()
    print(f"Prediction: {data['prediction']}")
    print(f"Confidence: {data['confidence']:.2f}")
    print(f"Nutrition: {fn[data['prediction']]}")
else:
    print("Error:", response.json())
