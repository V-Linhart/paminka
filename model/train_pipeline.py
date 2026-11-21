"""No-show risk pipeline. Target: appointment_status == 'No Show' (Cancelled rows excluded)."""
import pandas as pd, numpy as np, json, joblib, sys
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.metrics import roc_auc_score, average_precision_score, roc_curve, brier_score_loss

SRC = sys.argv[1] if len(sys.argv)>1 else '/mnt/user-data/uploads/smart_hospital_appointment_dataset.csv'
OUT = sys.argv[2] if len(sys.argv)>2 else '/mnt/user-data/outputs'

FEATURES = ['lead_days','lead_gt14','lead_gt21','missed_prev','missed_ge4','prev_appts',
            'sev_low','sev_high','type_walkin','type_emergency']

def make_features(d):
    """Only information known at booking time (no bills, waiting time or satisfaction)."""
    X = pd.DataFrame(index=d.index)
    X['lead_days']   = d.booking_to_appointment_days
    X['lead_gt14']   = (d.booking_to_appointment_days > 14).astype(int)
    X['lead_gt21']   = (d.booking_to_appointment_days > 21).astype(int)
    X['missed_prev'] = d.missed_previous_appointments
    X['missed_ge4']  = (d.missed_previous_appointments >= 4).astype(int)
    X['prev_appts']  = d.previous_appointments
    X['sev_low']     = (d.severity_level == 'Low').astype(int)
    X['sev_high']    = (d.severity_level == 'High').astype(int)
    X['type_walkin'] = (d.appointment_type == 'Walk-in').astype(int)
    X['type_emergency'] = (d.appointment_type == 'Emergency').astype(int)
    return X[FEATURES]

df = pd.read_csv(SRC)
print('rows', len(df), df.appointment_status.value_counts().to_dict())
d = df[df.appointment_status != 'Cancelled'].copy()
d['ns'] = (d.appointment_status == 'No Show').astype(int)
X, y = make_features(d), d.ns
print('modelling rows', len(d), 'no-show rate %.3f' % y.mean())

Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=.2, stratify=y, random_state=42)
cv = StratifiedKFold(5, shuffle=True, random_state=0)
lr   = LogisticRegression(C=1.0, max_iter=5000)
tree = DecisionTreeClassifier(max_depth=3, min_samples_leaf=100, random_state=0)

res = {}
for n, m in [('logistic', lr), ('tree_depth3', tree)]:
    oof = cross_val_predict(m, Xtr, ytr, cv=cv, method='predict_proba')[:,1]
    m.fit(Xtr, ytr); p = m.predict_proba(Xte)[:,1]
    res[n] = dict(cv_auc=roc_auc_score(ytr, oof), test_auc=roc_auc_score(yte, p),
                  test_ap=average_precision_score(yte, p), test_brier=brier_score_loss(yte, p))
    print(n, {k: round(v,3) for k,v in res[n].items()})
print('baseline AP (prevalence) %.3f' % yte.mean())
print(export_text(tree, feature_names=FEATURES))

# out-of-fold scores on ALL data for lift / bands (honest, every row scored by a model that didn't see it)
oof_all = cross_val_predict(LogisticRegression(C=1.0, max_iter=5000), X, y, cv=cv, method='predict_proba')[:,1]
r = pd.DataFrame({'p': oof_all, 'y': y.values}).sort_values('p', ascending=False).reset_index(drop=True)
base = r.y.mean(); lift = []
for frac in [.05,.10,.20,.30,.50]:
    top = r.iloc[:int(len(r)*frac)]
    lift.append(dict(top_pct=int(frac*100), noshow_rate=top.y.mean(), lift=top.y.mean()/base, captured=top.y.sum()/r.y.sum()))
print(pd.DataFrame(lift).round(3).to_string(index=False))

# risk bands
LOW, HIGH = 0.10, 0.20
r['band'] = pd.cut(r.p, [-1, LOW, HIGH, 2], labels=['Low','Medium','High'])
bands = r.groupby('band', observed=True).agg(n=('y','size'), actual_rate=('y','mean'), mean_pred=('p','mean'))
bands['share'] = bands.n/len(r); print(bands.round(3))

# final model on all data -> export
final = LogisticRegression(C=1.0, max_iter=5000).fit(X, y)
model = dict(features=FEATURES, intercept=float(final.intercept_[0]), coef=dict(zip(FEATURES, map(float, final.coef_[0]))),
             band_low=LOW, band_high=HIGH, base_rate=float(base))
import os; os.makedirs(OUT, exist_ok=True)
json.dump(model, open(f'{OUT}/model.json','w'), indent=2)
joblib.dump(dict(model=final, features=FEATURES, band_low=LOW, band_high=HIGH), f'{OUT}/noshow_model.joblib')
print(json.dumps({k: round(v,3) for k,v in model['coef'].items()}, indent=1), 'intercept', round(model['intercept'],3))
json.dump(dict(results=res, lift=lift, bands=bands.reset_index().assign(band=lambda t:t.band.astype(str)).to_dict('records')),
          open(f'{OUT}/metrics.json','w'), indent=1, default=float)

# figures
fig, ax = plt.subplots(2, 2, figsize=(12, 9)); plt.rcParams.update({'font.size': 10})
g = d.groupby(pd.cut(d.booking_to_appointment_days, [-1,0,7,14,21,30], labels=['same day','1-7','8-14','15-21','22-29'])).ns.mean()*100
ax[0,0].bar(g.index.astype(str), g.values, color='#3b6fb6'); ax[0,0].axhline(base*100, ls='--', c='gray'); ax[0,0].set_title('No-show rate by booking lead time (days)'); ax[0,0].set_ylabel('%')
m = d.groupby(d.missed_previous_appointments.clip(upper=6)).ns.mean()*100
ax[0,1].bar([str(i) if i<6 else '6+' for i in m.index], m.values, color='#c0504d'); ax[0,1].axhline(base*100, ls='--', c='gray'); ax[0,1].set_title('No-show rate by past missed appointments'); ax[0,1].set_ylabel('%')
fpr, tpr, _ = roc_curve(yte, lr.predict_proba(Xte)[:,1]); fpr2, tpr2, _ = roc_curve(yte, tree.predict_proba(Xte)[:,1])
ax[1,0].plot(fpr, tpr, label=f"Logistic (AUC {res['logistic']['test_auc']:.2f})"); ax[1,0].plot(fpr2, tpr2, label=f"Tree d3 (AUC {res['tree_depth3']['test_auc']:.2f})"); ax[1,0].plot([0,1],[0,1],'k:'); ax[1,0].legend(); ax[1,0].set_title('ROC, held-out 20%')
orr = np.exp(pd.Series(model['coef'])).sort_values()
ax[1,1].barh(orr.index, orr.values, color=['#c0504d' if v>1 else '#3b6fb6' for v in orr.values]); ax[1,1].axvline(1, c='k'); ax[1,1].set_title('Odds ratios (per unit / vs. reference)')
plt.tight_layout(); plt.savefig(f'{OUT}/eda_and_model.png', dpi=110)

