import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

DATA_PATH = "dataset/student_career.csv"
MODEL_PATH = "model/career_model.pkl"
FEATURES = ["python", "java", "sql", "ml", "dl", "web", "cloud", "statistics", "data_visualization", "communication"]

def train_model():
    os.makedirs("dataset", exist_ok=True)
    os.makedirs("model", exist_ok=True)
    if not os.path.exists(DATA_PATH):
        from generate_dataset import generate_dataset
        generate_dataset(DATA_PATH)
    df = pd.read_csv(DATA_PATH)
    X, y = df[FEATURES], df["career"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    model = RandomForestClassifier(n_estimators=250, max_depth=8, random_state=42)
    model.fit(X_train, y_train)
    print(f"Validation accuracy: {accuracy_score(y_test, model.predict(X_test)):.2%}")
    return model

if __name__ == "__main__":
    train_model()
