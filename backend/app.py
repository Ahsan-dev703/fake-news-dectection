from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import os

app = Flask(__name__)
CORS(app)

# Load trained model
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_path = os.path.join(BASE_DIR, "models", "model.pkl")

model, vectorizer = pickle.load(open(model_path, "rb"))


@app.route("/")
def home():
    return jsonify({"status": "API Running"})


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    text = data["text"]

    # transform text
    vector = vectorizer.transform([text])

    # prediction
    prediction = model.predict(vector)[0]

    result = "Real News" if prediction == 1 else "Fake News"

    return jsonify({"prediction": result})


if __name__ == "__main__":
    app.run(debug=True)
