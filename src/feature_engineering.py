from sklearn.feature_extraction.text import TfidfVectorizer


def vectorize_text(train_text, test_text):
    vectorizer = TfidfVectorizer(max_features=5000, stop_words="english")

    X_train = vectorizer.fit_transform(train_text)
    X_test = vectorizer.transform(test_text)

    return X_train, X_test, vectorizer
