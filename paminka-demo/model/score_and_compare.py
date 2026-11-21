"""Score every appointment with the no-show model (out-of-fold = honest) and compare with the 30 % cut-off.

Run:  python score_and_compare.py <dataset.csv> <out_dir>
Writes <out_dir>/risk_scores.csv (patient_id, risk_score) for the demo.
"""
import sys
import importlib.util
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict

SRC, OUT = sys.argv[1], sys.argv[2]

# reuse make_features from the team's pipeline without running it
src = open(__file__.replace("score_and_compare.py", "train_pipeline.py"), encoding="utf-8-sig").read()
ns = {}
exec(src.split("df = pd.read_csv(SRC)")[0].replace("SRC = sys.argv[1]", "SRC = None #").replace(
    "OUT = sys.argv[2]", "OUT = None #"), ns)
make_features = ns["make_features"]

df = pd.read_csv(SRC)
fit_rows = df.appointment_status != "Cancelled"
X_all = make_features(df)
y = (df.loc[fit_rows, "appointment_status"] == "No Show").astype(int)

score = pd.Series(np.nan, index=df.index)
cv = StratifiedKFold(5, shuffle=True, random_state=0)              # same CV as the pipeline
score[fit_rows] = cross_val_predict(LogisticRegression(C=1.0, max_iter=5000), X_all[fit_rows], y,
                                    cv=cv, method="predict_proba")[:, 1]
final = LogisticRegression(C=1.0, max_iter=5000).fit(X_all[fit_rows], y)
score[~fit_rows] = final.predict_proba(X_all[~fit_rows])[:, 1]     # cancelled rows were never used for training
df["risk_score"] = score.round(4)
df[["patient_id", "risk_score"]].to_csv(f"{OUT}/risk_scores.csv", index=False)

# --- comparison on the patients the demo can call ---
callable_ = (df.appointment_type == "Scheduled") & (df.booking_to_appointment_days >= 1)
d = df[callable_].copy()
d["ns"] = d.appointment_status == "No Show"
prev = d.previous_appointments
d["no_show_pct"] = np.where(prev > 0, d.missed_previous_appointments / prev.where(prev > 0) * 100, np.nan)

cut = d[d.no_show_pct >= 30]
n = len(cut)
top = d.nlargest(n, "risk_score")
high = d[d.risk_score >= 0.20]
print(f"callable appointments: {len(d)}, overall no-show {d.ns.mean()*100:.1f}%, total no-shows {d.ns.sum()}")
for name, s in [("30% cut-off", cut), (f"model top {n}", top), ("model High band (>=0.20)", high)]:
    print(f"{name:26s} n={len(s):5d}  no-show {s.ns.mean()*100:5.1f}%  catches {s.ns.sum():4d} "
          f"({s.ns.sum()/d.ns.sum()*100:4.1f}% of no-shows)")
print("overlap cut-off vs model top:", len(set(cut.patient_id) & set(top.patient_id)))
