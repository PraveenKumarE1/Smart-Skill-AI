import csv, os, random

FEATURES = ["python", "java", "sql", "ml", "dl", "web", "cloud", "statistics", "data_visualization", "communication"]
CAREER_PROFILES = {
    "AI Engineer": [5,2,2,5,5,1,2,5,2,4],
    "ML Engineer": [5,3,4,5,4,1,3,4,2,4],
    "Data Scientist": [5,2,5,4,3,1,2,5,5,4],
    "Data Analyst": [3,2,5,2,1,1,1,5,5,4],
    "Full-Stack Developer": [3,4,2,1,1,5,2,2,2,4],
    "Cloud Engineer": [3,3,3,2,1,2,5,2,1,4],
}

def generate_dataset(path="dataset/student_career.csv", samples_per_career=100):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    random.seed(42)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(FEATURES + ["career"])
        for career, profile in CAREER_PROFILES.items():
            for _ in range(samples_per_career):
                row = [max(0, min(5, value + random.choice([-1, 0, 0, 0, 1]))) for value in profile]
                writer.writerow(row + [career])
    print(f"Generated {samples_per_career * len(CAREER_PROFILES)} samples at {path}")

if __name__ == "__main__":
    generate_dataset()
