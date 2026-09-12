from flask import Flask, render_template, request
import joblib
import os

app = Flask(__name__)

MODEL_PATH = os.path.join("model", "career_model.pkl")
model = joblib.load(MODEL_PATH)

CAREER_INFO = {
    "AI Engineer": {"skills": ["Python", "Machine Learning", "Deep Learning", "TensorFlow/PyTorch", "Math"], "roadmap": ["Python fundamentals", "NumPy & Pandas", "Machine Learning", "Deep Learning", "Computer Vision/NLP", "Build AI projects"]},
    "ML Engineer": {"skills": ["Python", "Scikit-learn", "Machine Learning", "SQL", "Model Deployment"], "roadmap": ["Python", "Statistics", "Scikit-learn", "ML algorithms", "MLOps basics", "Deploy models with Flask"]},
    "Data Scientist": {"skills": ["Python", "Statistics", "Pandas", "SQL", "Machine Learning", "Data Visualization"], "roadmap": ["Python", "Statistics", "SQL", "EDA", "Machine Learning", "Portfolio projects"]},
    "Data Analyst": {"skills": ["Excel", "SQL", "Python", "Statistics", "Power BI/Tableau"], "roadmap": ["Excel", "SQL", "Statistics", "Power BI", "Python for analytics", "Dashboard projects"]},
    "Full-Stack Developer": {"skills": ["HTML", "CSS", "JavaScript", "Backend", "Database", "Git"], "roadmap": ["HTML/CSS", "JavaScript", "Frontend framework", "Backend APIs", "Database", "Deploy a full-stack app"]},
    "Cloud Engineer": {"skills": ["Linux", "Networking", "Cloud", "Docker", "Git", "Security"], "roadmap": ["Linux", "Networking", "Git", "AWS/Azure/GCP", "Docker", "Cloud deployment"]}
}

FEATURES = ["python", "java", "sql", "ml", "dl", "web", "cloud", "statistics", "data_visualization", "communication"]

def build_features(form):
    return [[int(form.get(feature, 0)) for feature in FEATURES]]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    features = build_features(request.form)
    career = model.predict(features)[0]
    info = CAREER_INFO[career]
    strengths = [name.replace("_", " ").title() for name, value in request.form.items() if name in FEATURES and int(value) >= 4]
    return render_template("result.html", career=career, strengths=strengths, skills=info["skills"], roadmap=info["roadmap"])

if __name__ == "__main__":
    app.run(debug=True)
