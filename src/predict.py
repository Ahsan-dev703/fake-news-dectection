import pickle


def load_model():
    with open("models/model.pkl", "rb") as f:
        model, vectorizer = pickle.load(f)
    return model, vectorizer


def predict_news(text):
    model, vectorizer = load_model()
    vector = vectorizer.transform([text])
    prediction = model.predict(vector)

    return "Real News" if prediction[0] == 1 else "Fake News"