import logging
import pickle
import os
from typing import Dict, Tuple
from config import Config

logger = logging.getLogger(__name__)


class PredictionService:
    """
    ML prediction service
    Manages model loading and inference
    """

    _model = None
    _vectorizer = None

    @classmethod
    def initialize(cls, model_path: str = None) -> Tuple[bool, str]:
        """
        Load model and vectorizer from pickle file
        Called once on application startup

        Args:
            model_path: Path to model.pkl file

        Returns:
            Tuple: (success, message)
        """
        if model_path is None:
            model_path = Config.MODEL_PATH

        # Make path absolute
        if not os.path.isabs(model_path):
            model_path = os.path.join(Config.BASE_DIR, model_path)

        try:
            if not os.path.exists(model_path):
                msg = f"Model file not found: {model_path}"
                logger.error(msg)
                return False, msg

            logger.info(f"Loading model from: {model_path}")

            with open(model_path, "rb") as f:
                cls._model, cls._vectorizer = pickle.load(f)

            logger.info("Model and vectorizer loaded successfully")
            return True, "Model loaded"

        except Exception as e:
            msg = f"Failed to load model: {str(e)}"
            logger.error(msg)
            return False, msg

    @classmethod
    def predict(cls, text: str) -> Dict:
        """
        Predict fake/real news from text

        Args:
            text: Input text

        Returns:
            Dict with prediction and confidence
        """
        if cls._model is None or cls._vectorizer is None:
            return {
                "success": False,
                "error": "Model not initialized. Call PredictionService.initialize() first",
                "prediction": None,
                "confidence": None,
            }

        if not text or not text.strip():
            return {
                "success": False,
                "error": "Empty input text",
                "prediction": None,
                "confidence": None,
            }

        try:
            # Vectorize text
            vector = cls._vectorizer.transform([text])

            # Get prediction
            prediction = cls._model.predict(vector)[0]

            # Get prediction probability (confidence)
            probability = cls._model.predict_proba(vector)[0]
            confidence = float(max(probability))

            # Map prediction to label
            label = "Real News" if prediction == 1 else "Fake News"

            logger.info(f"Prediction: {label} (confidence: {confidence:.4f})")

            return {
                "success": True,
                "prediction": label,
                "prediction_code": int(prediction),
                "confidence": round(confidence, 4),
                "probabilities": {
                    "fake": round(float(probability[0]), 4),
                    "real": round(float(probability[1]), 4),
                },
            }

        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "prediction": None,
                "confidence": None,
            }

    @classmethod
    def predict_batch(cls, texts: list) -> Dict:
        """
        Predict multiple texts at once

        Args:
            texts: List of text strings

        Returns:
            Dict with predictions for each text
        """
        if cls._model is None or cls._vectorizer is None:
            return {"success": False, "error": "Model not initialized"}

        try:
            # Filter empty texts
            valid_texts = [t for t in texts if t and t.strip()]

            if not valid_texts:
                return {"success": False, "error": "No valid input texts"}

            # Vectorize all texts
            vectors = cls._vectorizer.transform(valid_texts)

            # Get predictions
            predictions = cls._model.predict(vectors)
            probabilities = cls._model.predict_proba(vectors)

            # Format results
            results = []
            for i, text in enumerate(valid_texts):
                pred = int(predictions[i])
                probs = probabilities[i]
                label = "Real News" if pred == 1 else "Fake News"
                confidence = float(max(probs))

                results.append(
                    {
                        "text": text[:100] + "..." if len(text) > 100 else text,
                        "prediction": label,
                        "confidence": round(confidence, 4),
                        "probabilities": {
                            "fake": round(float(probs[0]), 4),
                            "real": round(float(probs[1]), 4),
                        },
                    }
                )

            logger.info(f"Batch prediction completed for {len(results)} texts")

            return {"success": True, "count": len(results), "results": results}

        except Exception as e:
            logger.error(f"Batch prediction failed: {str(e)}")
            return {"success": False, "error": str(e)}

    @classmethod
    def get_model_info(cls) -> Dict:
        """Get model information"""
        if cls._model is None:
            return {"loaded": False, "message": "Model not initialized"}

        return {
            "loaded": True,
            "model_type": cls._model.__class__.__name__,
            "vectorizer_type": cls._vectorizer.__class__.__name__,
            "feature_names_count": (
                len(cls._vectorizer.get_feature_names_out())
                if hasattr(cls._vectorizer, "get_feature_names_out")
                else 0
            ),
        }
