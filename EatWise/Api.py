from flask import Flask, request, jsonify
from flask_restful import Resource, Api
import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np
import io

app = Flask(__name__)
api = Api(app)

model = tf.keras.models.load_model("resfood.h5")

cidxes={0:'adhirasam',1:'biryani',2:'chapati', 3:'jalebi',4:'lassi',5:'rasgulla'}

IMG_SIZE = 224

def preprocess_image(img_bytes):
    img = image.load_img(io.BytesIO(img_bytes), target_size=(IMG_SIZE, IMG_SIZE))
    img_array = image.img_to_array(img)
    img_array = img_array / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

class FoodPrediction(Resource):
    def post(self):
        if 'file' not in request.files:
            return {"error": "No file provided"}, 400

        file = request.files['file']
        img_bytes = file.read()
        img_array = preprocess_image(img_bytes)

        preds = model.predict(img_array)
        class_id = np.argmax(preds, axis=1)[0]
        print(class_id)
        class_name = cidxes.get(class_id, "Unknown")
        confidence = float(np.max(preds))

        if confidence<0.3:
            return "Coudn't Predict"
        else:
            return {"prediction": class_name,"confidence": confidence}, 200

api.add_resource(FoodPrediction, '/api/predict')

if __name__ == "__main__":
    app.run(debug=True,port=3000)
