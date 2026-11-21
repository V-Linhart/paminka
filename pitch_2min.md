# Påminka – 2-minute pitch

**[0:00 – Hook, 15 s]**
Every year about **one million** booked visits in Sweden are simply missed.
At the same time, **1 in 4 patients** waits longer than the guaranteed 90 days for a first specialist visit (Socialstyrelsen, Sept 2026).
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
This is not a guess: in a randomized trial at a Spanish public hospital, calling high-risk specialist patients a week ahead cut no-shows by **39–51 %** (Valero-Bover et al., 2022). We assume only a cautious **22 %**.
An AI call costs about **4 kronor**. Priced with real Swedish costs per specialty visit, 1,055 AI calls cost about **4,000 SEK** and save the healthcare system about **370,000 SEK** in otherwise wasted visits.
Scaled to Sweden: a healthcare system saving of roughly **500 million SEK a year**, and about **100,000 visit slots** freed for patients in the queue –
enough to lift the share seen within the 90-day guarantee from **74 % to about 80 %**.

**[1:50 – Close, 10 s]**
**Påminka** – an AI call for the patients who need it.
**Fewer empty chairs – shorter queues.**

---
*Notes for Q&A: only scheduled appointments booked ≥1 day ahead are called (no emergency, walk-in or dental); the calls in the demo are simulated on a demo dataset; money: each visit is valued at the Swedish cost of an outpatient doctor's visit in that specialty (3,075–7,090 SEK, avg ~5,100) from the cost-based (KPP) price list "Regionala priser och ersättningar för Södra sjukvårdsregionen 2025", NordDRG öppenvård läkarbesök, column "övriga sjukhus" (85,419 SEK per point × Socialstyrelsen weight); calls are made by an AI voice agent – cost estimates: ~4 SEK per answered call (~2–3 min at ~1.5 SEK/min for phone line, speech-to-text, text-to-speech and language model), ~1 SEK per unanswered call + SMS, +30 SEK staff time per rescheduling hand-over; 16 parallel AI lines in the demo (can be scaled); the agent says it is an AI at the start of every call (EU AI Act transparency rule) and offers a person at any time; trust & safety (scammers already pretend to be clinics calling to rebook – warnings from 1177 and Region Östergötland): calls come from the clinic's official number and are announced in the 1177 inbox, the agent says up front it will never ask for BankID, personal number, passwords or payment, offers to let the patient hang up and call the clinic via 1177.se, confirms it is the right person before saying anything about the appointment, never mentions symptoms or diagnoses (SMS only say the date), and changes show up in the 1177 app; the trial evidence is for staff calls, so the effect of AI calls is an assumption – one reason we use the cautious 22 %; "healthcare system saving" = the cost of booked care time that a no-show would waste, valued the way Swedish regions value missed visits (VGR: ~550 MSEK for 116,034 missed hospital visits in 2024; Timbro: missed visits cost billions a year) – it is recovered capacity (more patients treated with the same staff), not cash returned to the budget. Model: logistic regression on booking-time data only (lead time, missed visits, severity, appointment type), test AUC 0.72 on a held-out 20 %, out-of-fold scores in the demo; flags risk ≥ 20 %; about the same number of calls (1,055 vs 1,025) reaches 267 future no-shows vs 181 with the 30 % history cut-off (49 % vs 33 % of all no-shows). The demo dataset is synthetic, so impossible combinations were removed (pregnancy checkups kept only for women aged 16–49). The 500 MSEK figure is a rough national extrapolation (Timbro ~1 M missed visits, model catches ~49 % of them with calls to a group missing ~25 %, 22 % effect, a cautious VGR ~4,700 SEK per missed visit, ~4 SEK per AI call). The 74 % → ~80 % (range 78–82 %) assumes 25–50 % of freed slots are specialist first visits given to patients waiting >90 days (queue ~458,000, of which ~159,000 >90 days, Aug 2026). Calls vs SMS head-to-head: about equal on average (Cochrane) – the benefit comes from targeting high-risk patients. Why 22 % and not 39–51 %: in Valero-Bover the control group got no reminder at all; Swedish patients already get an SMS, so we use the 22 % from Shah et al. 2016 (call on top of a standard reminder, primary care). Source: Valero-Bover et al., BMC Health Serv Res 2022, pmc.ncbi.nlm.nih.gov/articles/PMC8985245.*

---
**References**

1. **Swedish visit prices:** Södra sjukvårdsregionen. *Regionala priser och ersättningar för Södra sjukvårdsregionen 2025* (decided by Södra regionvårdsnämnden 2024-12-06, version 2), section 1.6.2 *Priser NordDRG CC – öppenvård läkarbesök (somatik)*, column "övriga sjukhus" (85,419 SEK per DRG point; cost-based, KPP). sodrasjukvardsregionen.se/verksamhet/regionala-priser-och-ersattningar
2. Valero-Bover D. et al. Reducing non-attendance in outpatient appointments: predictive model development, validation, and clinical assessment. *BMC Health Services Research* 2022. pmc.ncbi.nlm.nih.gov/articles/PMC8985245
3. Shah S.J. et al. Targeted reminder phone calls to patients at high risk of no-show for primary care appointment: a randomized trial. *J Gen Intern Med* 2016;31(12):1460–1466. pmc.ncbi.nlm.nih.gov/articles/PMC5130951
4. Socialstyrelsen. Lägesbild och statistik – tillgänglighet, väntetider och vårdgaranti (September 2026). socialstyrelsen.se
5. Timbro. *Vaskade vårdbesök* (~1 million missed or late-cancelled visits per year). timbro.se/publikation/vaskade-vardbesok
6. VGR Fokus (June 2025). Färre missade sjukhusbesök – men de kostar fortfarande en halv miljard (116,034 missed hospital visits, ~550 MSEK). vgrfokus.se
7. 1177 Region Halland. Var vaksam på bedrägeriförsök i Region Hallands namn (healthcare never asks for BankID during a call; calls come from the unit's own number). 1177.se/Halland
