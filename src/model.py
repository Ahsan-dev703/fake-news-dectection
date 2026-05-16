from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import pickle
import os


def train_model(X_train, y_train):
    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)
    return model


def evaluate_model(model, X_test, y_test):
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    print(f"Accuracy: {accuracy * 100:.2f}%")
    return accuracy


def save_model(model, vectorizer):
    # project root detect
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    model_dir = os.path.join(base_dir, "models")
    model_path = os.path.join(model_dir, "model.pkl")

    # create folder if not exists
    os.makedirs(model_dir, exist_ok=True)

    with open(model_path, "wb") as f:
        pickle.dump((model, vectorizer), f)

    print("✅ Model saved at:", model_path)
