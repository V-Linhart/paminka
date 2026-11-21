# Påminka – 2-minute pitch

**[0:00 – Hook, 15 s]**
Every year about **one million** booked visits in Sweden are simply missed [5].
At the same time, **1 in 4 patients** waits longer than the guaranteed 90 days for a first specialist visit [4].
Empty chairs, full queues.

**[0:15 – Problem, 15 s]**
Today, hospitals send the same SMS reminder to everyone. But no-shows are not random: some patients miss again and again – and an SMS alone doesn't change that.

**[0:30 – Solution, 20 s]**
**Påminka** predicts each patient's **no-show risk** from what is known at booking – how far ahead it was booked, past missed visits, severity.
Patients with **risk ≥ 20 %** get a **short phone call from Påminka's AI agent** a week before their visit – it says it is an AI, helps solve what stops them from coming, and hands over to staff when a visit needs rebooking.

**[0:50 – DEMO, 40 s]**
*[Press ▶ Start calls → the AI agent calls on 16 lines live, counters run (~2 min, keep it running) → click a ★ patient → "View call transcript".]*
In our dataset of 10,000 appointments, the patients our model flags miss **twice as often** as average – and with the same number of calls it reaches **47 % more** of the patients who would miss than a simple history rule.

**[1:30 – Evidence & money, 20 s]**
This is not a guess: in a randomized trial at a Spanish public hospital, calling high-risk specialist patients a week ahead cut no-shows by **39–51 %** [2]. We assume only a cautious **22 %** [3].
An AI call costs about **4 kronor**. Priced with real Swedish costs per specialty visit [1], 1,055 AI calls cost about **4,000 SEK** and save the healthcare system about **370,000 SEK** in otherwise wasted visits.
Scaled to Sweden: a healthcare system saving of roughly **500 million SEK a year**, and about **100,000 visit slots** freed for patients in the queue –
enough to lift the share seen within the 90-day guarantee from **74 % to about 80 %**.

**[1:50 – Close, 10 s]**
**Påminka** – an AI call for the patients who need it.
**Fewer empty chairs – shorter queues.**

---

## Q&A – cost

**1. Where does 4 kr per AI call come from?**
It is our estimate (E1): ~1.5 kr per minute for phone line, speech-to-text, text-to-speech and language model × a 2–3 minute call – not a vendor quote. A contact would have to cost about **350 kr** before it stops paying off (370,000 SEK ÷ 1,055 contacts). Even at 10× our estimate (40 kr) the saving is still ~9× the cost.

**2. Is 370,000 SEK real money saved?**
No – it is recovered capacity: the booked slot is used instead of wasted, so more patients are treated with the same staff. Swedish regions value missed visits the same way: VGR estimates ~550 MSEK a year for its missed hospital visits [6].

**3. What about development, integration and running costs?**
Not included in the demo: connection to the booking/journal system, 1177 integration, phone platform, maintenance and compliance. Even a platform cost of a few million SEK a year leaves a large margin against ~500 MSEK nationally. We would measure real costs in a pilot.

**4. You also call people who would have come anyway – isn't that wasted money?**
It is included: all 1,055 contacts are counted as cost; only 72 of them bring money back.

**5. Patients already get an SMS – aren't you double-counting?**
No. We use the 22 % effect from the trial where the call came on top of a standard reminder [3], not the 39–51 % measured against no reminder at all [2].

**6. Will the freed slot really be filled?**
A rescued patient keeps and uses their slot. For rebooked patients we count 0 SEK, although their freed slot could go to someone in the queue – so that part is conservative.

**7. Why the DRG price and not the hospital's real cost?**
The Södra price list is cost-based (KPP, self-cost principle) and uses Socialstyrelsen's national weights [1].

**8. Regions charge no-show fees – don't they lose that income?**
Slightly (no-show fees are typically 250–600 SEK), but a patient who attends pays the normal visit fee instead, and the visit itself is worth ~5,100 SEK.

**9. Where do the 16 lines and the hand-over cost come from?**
Assumptions: 16 parallel AI lines in the demo (can be scaled) and 30 SEK of staff time per rebooking (E2).

## Q&A – other likely questions

- **Do AI calls work as well as staff calls?** Not yet proven – the trials used staff calls [2, 3]. That is one reason we assume only 22 % [3].
- **Is it legal / will patients trust it?** The agent says it is an AI (EU AI Act transparency rule [12]), never asks for BankID, personal number or payment, offers to let the patient hang up and call the clinic via 1177.se, confirms it is the right person before giving details, and never mentions symptoms or diagnoses. Scammers already pretend to be clinics [7], so this is built in from the first sentence.
- **Do patients like reminders?** In a trial of 6,450 patients, none felt disturbed and three in four wanted reminders as standard [10].
- **Calls or SMS?** On average about equal [9]; the benefit comes from targeting high-risk patients with a call [8].

## Background notes

- Only scheduled appointments booked ≥1 day ahead are called (no emergency, walk-in or dental). The calls in the demo are simulated on a synthetic demo dataset; impossible combinations were removed (pregnancy checkups kept only for women aged 16–49).
- **Visit value:** the Swedish cost of an outpatient doctor's visit in that specialty, 3,075–7,090 SEK (avg ~5,100) – Södra sjukvårdsregionen 2025, NordDRG öppenvård läkarbesök, column "övriga sjukhus", 85,419 SEK per point × Socialstyrelsen weight [1].
- **Model:** logistic regression on booking-time data only (lead time, missed visits, severity, appointment type); test AUC 0.72 on a held-out 20 %; out-of-fold scores in the demo; flags risk ≥ 20 %. About the same number of calls (1,055 vs 1,025) reaches 267 future no-shows vs 181 with a 30 % history cut-off (49 % vs 33 % of all no-shows).
- **Simulation:** only patients who actually missed in the data (~25 % of those called) can be rescued – by a call (22 % [3], credited to the ~65 % who answer, E3) or by SMS (9 % [8]); patients who would have come anyway = 0 SEK.
- **500 MSEK / year** is a rough national extrapolation: ~1 M missed visits [5] × ~49 % reached by the model × 22 % effect [3] × a cautious 4,700 SEK per missed visit [6], minus ~4 SEK per AI call.
- **74 % → ~80 %** (range 78–82 %) assumes 25–50 % of freed slots become specialist first visits for patients waiting >90 days (queue ~458,000, ~159,000 >90 days, Aug 2026 [11]).
- **Why 22 % and not 39–51 %:** in [2] the control group got no reminder; Swedish patients already get an SMS, so we use the effect of a call on top of a standard reminder [3].
- **"Healthcare system saving"** = the cost of booked care time a no-show would waste, valued as Swedish regions value missed visits [6] – recovered capacity, not cash returned to the budget.

---

## References

1. **Swedish visit prices:** Södra sjukvårdsregionen. *Regionala priser och ersättningar för Södra sjukvårdsregionen 2025* (decided by Södra regionvårdsnämnden 2024-12-06, version 2), section 1.6.2 *Priser NordDRG CC – öppenvård läkarbesök (somatik)*, column "övriga sjukhus" (85,419 SEK per DRG point; cost-based, KPP). sodrasjukvardsregionen.se/verksamhet/regionala-priser-och-ersattningar
2. Valero-Bover D. et al. Reducing non-attendance in outpatient appointments: predictive model development, validation, and clinical assessment. *BMC Health Services Research* 2022. pmc.ncbi.nlm.nih.gov/articles/PMC8985245
3. Shah S.J. et al. Targeted reminder phone calls to patients at high risk of no-show for primary care appointment: a randomized trial. *J Gen Intern Med* 2016;31(12):1460–1466. pmc.ncbi.nlm.nih.gov/articles/PMC5130951 – **source of the 22 %:** 2,247 high-risk patients who all got a standard automated reminder; a staff call 7 days ahead lowered no-shows from 29.2 % to 22.8 % (−6.4 points, 95 % CI −9.8 to −3.0), a relative reduction of 22 %.
4. Socialstyrelsen. Lägesbild och statistik – tillgänglighet, väntetider och vårdgaranti (September 2026). socialstyrelsen.se
5. Timbro. *Vaskade vårdbesök* (~1 million missed or late-cancelled visits per year). timbro.se/publikation/vaskade-vardbesok
6. VGR Fokus (June 2025). Färre missade sjukhusbesök – men de kostar fortfarande en halv miljard (116,034 missed hospital visits, ~550 MSEK). vgrfokus.se
7. 1177 Region Halland. Var vaksam på bedrägeriförsök i Region Hallands namn (healthcare never asks for BankID during a call; calls come from the unit's own number). 1177.se/Halland
8. Predictive model-based interventions to reduce outpatient no-shows: a rapid systematic review. *Journal of the American Medical Informatics Association* 2023;30(3):559. academic.oup.com/jamia/article/30/3/559/6889491 (targeted calls: 3 RCTs, median RR 0.61; targeted SMS: RR 0.91)
9. Gurol-Urganci I. et al. Mobile phone messaging reminders for attendance at healthcare appointments. *Cochrane Database of Systematic Reviews* 2013, CD007458.pub3 (SMS vs phone call: RR 0.99).
10. Junod Perron N. et al. Text-messaging versus telephone reminders to reduce missed appointments in an academic primary care clinic: a randomized controlled trial. *BMC Health Services Research* 2013;13:125. pmc.ncbi.nlm.nih.gov/articles/PMC3623700
11. Queue figures (~458,000 waiting for a first specialist visit, ~159,000 >90 days, August 2026): secondary summary of Socialstyrelsen's preliminary statistics ("Vårdgarantin 2026", forsakrat.se) – not checked against Socialstyrelsen's database; treat as approximate.
12. Regulation (EU) 2024/1689 (Artificial Intelligence Act), Article 50 – transparency obligations: people must be informed when they interact with an AI system.

**Our own estimates (not from a source)**
- E1. AI call cost: ~4 SEK per answered call (~1.5 SEK/min all-in × 2–3 min); ~1 SEK per unanswered call + SMS.
- E2. Staff time: ~600 SEK/hour incl. employer costs → ~30 SEK per 3-minute rebooking hand-over.
- E3. Answer rate: 65 % of patients answer the call; 50 % of SMS patients who were coming anyway reply YES.
