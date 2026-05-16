import pandas as pd


def load_data(fake_path, true_path):
    fake = pd.read_csv(fake_path)
    true = pd.read_csv(true_path)

    fake["label"] = 0  # Fake = 0
    true["label"] = 1  # True = 1

    df = pd.concat([fake, true], axis=0)
    df = df.sample(frac=1).reset_index(drop=True)  # shuffle

    return df


def clean_data(df):
    df = df.dropna()

    # Combine title + text (important for accuracy)
    df["content"] = df["title"] + " " + df["text"]

    return df[["content", "label"]]
