# SmartSkill AI 🎯

AI-Based Student Skill & Career Prediction System.

SmartSkill AI uses a Random Forest machine-learning model to analyze a student's technical and soft skills, predict a suitable career domain, identify strengths, and provide a learning roadmap.

## Features
- Career prediction using Random Forest
- Skill-based profile analysis
- Strength identification
- Recommended skills for the predicted career
- Personalized learning roadmap
- Responsive Flask web interface
- Automatic synthetic dataset generation
- Training/validation pipeline

## Tech Stack
Python, Flask, Pandas, Scikit-learn, HTML, CSS

## Project Structure
```text
Smart-Skill-AI/
├── app.py
├── train_model.py
├── generate_dataset.py
├── requirements.txt
├── README.md
├── .gitignore
├── dataset/
│   └── student_career.csv   # generated on first run if missing
├── model/                    # model output directory
├── templates/
│   ├── index.html
│   └── result.html
└── static/
    └── style.css
```

## Run Locally
```bash
python -m venv venv
```
Windows:
```bash
venv\Scripts\activate
```
Install dependencies:
```bash
pip install -r requirements.txt
```
Generate the dataset (optional; the app also does this automatically):
```bash
python generate_dataset.py
```
Train/check the model:
```bash
python train_model.py
```
Start the app:
```bash
python app.py
```
Open `http://127.0.0.1:5000` in your browser.

## Note
The training data is synthetic and intended for education/demo purposes. Career recommendations are suggestions, not professional career counseling.
