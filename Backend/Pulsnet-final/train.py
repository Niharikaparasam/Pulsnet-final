# train.py
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
from app.config import MATCH_MODEL_PATH

DATA = Path("data/train_pairs.csv")
if not DATA.exists():
    print("Place labeled pairs at data/train_pairs.csv with columns: donor_blood_group,recipient_blood_group,label")
    raise SystemExit

df = pd.read_csv(DATA)
cat_features = ["donor_blood_group","recipient_blood_group"]
X = df[cat_features]
y = df["label"]

preproc = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), cat_features)])
clf = Pipeline([("preproc", preproc), ("clf", RandomForestClassifier(n_estimators=200, random_state=42))])

X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=0.2, random_state=42, stratify=y)
clf.fit(X_train, y_train)
preds = clf.predict(X_test)
print("Accuracy:", accuracy_score(y_test,preds))
print(classification_report(y_test,preds))
joblib.dump(clf, MATCH_MODEL_PATH)
print("Saved model to", MATCH_MODEL_PATH)
