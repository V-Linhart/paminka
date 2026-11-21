"""Påminka demo web app.

Run locally:  python server.py
Open:         http://localhost:8000          -> Påminka demo  (also /demo)
              http://localhost:8000/test     -> Ask Claude test page (local only)

On Render: set ANTHROPIC_API_KEY (and optionally DEMO_PASSWORD) as environment variables.
The API key stays on the server side (never in the web page). Locally it can also be read
from api_key.txt next to this file. Never share or upload api_key.txt.
"""
import base64
import csv
import hashlib
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import anthropic

HERE = Path(__file__).parent
ON_RENDER = "RENDER" in os.environ                 # Render sets RENDER=true
PORT = int(os.environ.get("PORT", 8000))           # Render tells us which port to use
HOST = "0.0.0.0" if ON_RENDER else "127.0.0.1"     # public on Render, only this PC locally
DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "")  # if set: browser asks for it (any user name)
ASK_ENABLED = not ON_RENDER or os.environ.get("ENABLE_ASK") == "1"  # free-text Claude page: local only

MODEL = "claude-opus-5-5"            # "claude-haiku-5-5" for very cheap testing
PRICE_IN, PRICE_OUT = 4.00, 20.00     # $ per 1M tokens (Haiku 5.5: 0.10, 0.50)
SYSTEM = "You are a helpful assistant for my hackathon app. Answer clearly and briefly."

# --- demo assumptions (same as in the pitch) ---
DATA = HERE / "data" / "smart_hospital_appointment_dataset_with_noshow_pct.csv"
CUTOFF = 30.0          # old rule: previous no-show % that made a patient high-risk (kept for comparison)
SCORES = HERE / "model" / "risk_scores.csv"   # team's logistic model, out-of-fold scores (model/score_and_compare.py)
RISK_HIGH = 0.20       # model's "High" band: predicted no-show risk >= 20 %
# Specialist-care RCT: calls to high-risk patients cut no-shows 39-51 % (Valero-Bover et al. 2022, vs no reminder).
# We use the cautious 22 % (Shah et al. 2016, on top of a standard reminder), since Swedish patients already get an SMS.
CALL_EFFECT = 0.22
SMS_EFFECT = 0.09      # relative no-show reduction from a targeted SMS (JAMIA review, RR 0.91)
REACH = 0.65           # assumed share of patients who answer the call; the rest get an SMS
SMS_REPLY = 0.50       # assumed share of SMS patients (who were coming anyway) that reply YES
# --- Swedish money: cost of one outpatient doctor's visit per department ---
# Source: Regionala priser och ersättningar för Södra sjukvårdsregionen 2025 (cost-based, KPP),
# 1.6.2 NordDRG öppenvård läkarbesök, column "övriga sjukhus" (85,419 kr per point x Socialstyrelsen weight).
VISIT_PRICE_SEK = {
    "Neurology": 7090,          # A99Q Läkarbes sjd i nervsystemet U O
    "Pulmonology": 6834,        # D99O Läkarbesök andningssjd O
    "Cardiology": 5808,         # E99O Läkarbesök cirkulationssjd O
    "Gastroenterology": 5296,   # F99Q Läkarbes sjd matsmältningorg U O
    "General Medicine": 5125,   # W99O Läkarbesök andra problem O
    "Gynecology": 4442,         # O99Q Läk adnexa/vulva U O
    "Orthopedics": 4186,        # H99Q Läkarbes sjd muskelskelett U O
    "Dermatology": 4186,        # J99Q Läkarbesök sjd hud/underhud U O
    "Ophthalmology": 3075,      # B99O Läkarbesök ögonsjd O
}   # Dental is not in this price list (separate dental fee system) -> not called in the demo
# --- cost of contacting: an AI voice agent makes the calls (estimates, not quotes) ---
# ~1.5 kr per minute all-in (phone line + speech-to-text + text-to-speech + language model), ~2-3 min per call.
CALL_COST_SEK = 4      # answered AI call
SMS_COST_SEK = 1       # unanswered call attempt (~30 s ringing) + SMS
HANDOVER_COST_SEK = 30 # rescheduling is handed over to staff: ~3 min of staff time at ~600 kr/h


def load_key() -> str | None:
    key = os.environ.get("ANTHROPIC_API_KEY")
    key_file = HERE / "api_key.txt"
    if not key and key_file.exists():
        key = key_file.read_text(encoding="utf-8").strip()
    return key or None


def plausible(r: dict) -> bool:
    """The demo dataset is synthetic: age and gender are random, so drop impossible combinations.
    Every Gynecology visit is a 'Pregnancy Checkup' -> keep only women aged 16-49."""
    if r["department"] == "Gynecology":
        return r["gender"] == "Female" and 16 <= int(r["age"]) <= 49
    return True


def load_patients() -> dict:
    with SCORES.open(encoding="utf-8") as f:
        risk = {r["patient_id"]: float(r["risk_score"]) for r in csv.DictReader(f)}
    with DATA.open(encoding="utf-8") as f:
        # only scheduled appointments booked at least 1 day ahead can get a reminder call
        callable_ = [r for r in csv.DictReader(f)
                     if r["appointment_type"] == "Scheduled" and int(r["booking_to_appointment_days"]) >= 1
                     and r["department"] in VISIT_PRICE_SEK and plausible(r)]
    rows = [r for r in callable_ if risk[r["patient_id"]] >= RISK_HIGH]
    # comparison with the old 30 % cut-off, same callable patients
    cut = [r for r in callable_ if r["no_show_pct"] and float(r["no_show_pct"]) >= CUTOFF]
    noshow = lambda rs: sum(r["appointment_status"] == "No Show" for r in rs)
    compare = {"cut_n": len(cut), "cut_noshows": noshow(cut), "model_n": len(rows), "model_noshows": noshow(rows),
               "all_noshows": noshow(callable_)}
    base_rate = sum(r["appointment_status"] == "No Show" for r in rows) / len(rows)
    patients = []
    for r in rows:
        bill_sek = VISIT_PRICE_SEK[r["department"]]   # Swedish cost of this kind of visit
        outcome = call_outcome(r["patient_id"], r["appointment_status"])
        recovered = bill_sek if outcome.endswith("rescued") else 0.0   # only rescued visits are money back
        patients.append({
            "id": r["patient_id"], "age": int(r["age"]), "gender": r["gender"],
            "cost_sek": (CALL_COST_SEK + (HANDOVER_COST_SEK if outcome == "call_rescheduled" else 0)
                         if outcome.startswith("call") else SMS_COST_SEK),
            "department": r["department"], "symptoms": r["symptoms"], "chronic": r["chronic_disease"],
            "type": r["appointment_type"], "day": r["appointment_day"], "month": r["appointment_month"],
            "booked_days_ahead": int(r["booking_to_appointment_days"]),
            "previous": int(r["previous_appointments"]), "missed": int(r["missed_previous_appointments"]),
            "pct": float(r["no_show_pct"]) if r["no_show_pct"] else None,
            "risk": risk[r["patient_id"]], "bill_sek": round(bill_sek), "outcome": outcome,
            "saving_sek": round(recovered),
        })
    return {"patients": patients, "base_rate": base_rate, "effect": CALL_EFFECT, "sms_effect": SMS_EFFECT,
            "reach": REACH, "call_cost_sek": CALL_COST_SEK, "sms_cost_sek": SMS_COST_SEK,
            "handover_cost_sek": HANDOVER_COST_SEK,
            "cutoff": CUTOFF,
            "risk_high": RISK_HIGH, "compare": compare}


def _h(patient_id: str, salt: str) -> float:
    """Deterministic 0-1 number per patient, so the demo looks the same every run."""
    return int(hashlib.md5((patient_id + salt).encode()).hexdigest(), 16) % 10000 / 10000


def call_outcome(patient_id: str, status: str) -> str:
    """Simulated result of calling one patient, using what really happened in the dataset.

    status = the real appointment_status: 'No Show' patients are the ones who would have missed.
    The trial's 22 % was measured over everyone called (reached or not), so a reached patient who
    would have missed is rescued with probability 0.22 / REACH; an SMS rescues with 0.09.
    """
    reached = _h(patient_id, "reach") < REACH
    if reached:
        if status == "No Show":
            return "call_rescued" if _h(patient_id, "rescue") < CALL_EFFECT / REACH else "call_confirmed"
        return "call_rescheduled" if status == "Cancelled" else "call_confirmed"
    if status == "No Show":
        return "sms_rescued" if _h(patient_id, "rescue") < SMS_EFFECT else "sms_sent"
    return "sms_confirmed" if _h(patient_id, "reply") < SMS_REPLY else "sms_sent"


api_key = load_key()
client = anthropic.Anthropic(api_key=api_key) if api_key else None
total_cost = 0.0
DEMO = load_patients() if DATA.exists() else None
BY_ID = {p["id"]: p for p in DEMO["patients"]} if DEMO else {}


def claude(system: str, question: str) -> dict:
    global total_cost
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=4000,
        system=system,
        output_config={"effort": "low"},          # low = cheaper and faster
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",                       # if Opus declines, another model answers
        messages=[{"role": "user", "content": question}],
    )
    cost = (response.usage.input_tokens * PRICE_IN
            + response.usage.output_tokens * PRICE_OUT) / 1_000_000
    total_cost += cost
    if response.stop_reason == "refusal":
        answer = "(Claude declined this request)"
    else:
        answer = "".join(b.text for b in response.content if b.type == "text")
    return {"answer": answer, "cost": cost, "total": total_cost, "model": response.model}


CALL_SYSTEM = ("You write the transcript of a short, warm reminder phone call made by Påminka, an AI voice assistant "
               "calling on behalf of a hospital clinic, to a patient. Lines start with 'AI:' or 'Patient:' "
               "(and 'Staff:' only if the call is handed over to a person). 9-13 lines.\n"
               "TRUST - the first AI line must be short (max 3 short sentences, ~35 words) and close to: "
               "'Hi, this is Påminka, the clinic's AI assistant, about a booked appointment. I'll never ask for BankID or "
               "payment - you can always call the clinic via 1177.se instead. Am I speaking with the person the "
               "appointment is for?'\n"
               "PRIVACY - before the patient confirms who they are, mention nothing about the appointment except that one "
               "exists. After confirmation you may say the day and the department, but NEVER mention symptoms, diagnosis, "
               "chronic conditions or medicines.\n"
               "Then confirm the appointment, gently ask if anything could stop them from coming (transport, work, "
               "forgetting), help solve it, and end by confirming and saying the booking is visible in the 1177 app. "
               "Never mention their missed-appointment history or that they are 'high-risk'. "
               "Do not invent a name for the patient. Output only the dialogue.")


CALL_STORY = {
    "call_confirmed": "In this call the patient simply confirms they will come.",
    "call_rescued": ("In this call the patient first admits they had forgotten or had a problem (pick one: transport, "
                     "work shift, childcare) - the AI helps solve it (e.g. offers a different time the same day from "
                     "the clinic's free slots) and the patient confirms they will come."),
    "call_rescheduled": ("In this call the patient cannot come; the AI says it will transfer them to a staff member to book "
                         "a new time, a staff member joins for 2-3 lines and books it, so the slot can go to someone else."),
}
SMS_SYSTEM = ("You write one short, friendly reminder SMS (under 320 characters) sent by Påminka on behalf of the "
              "hospital clinic to a patient who did not answer an automated reminder call. Mention only the day and "
              "month of the appointment - no department, symptoms or diagnosis (someone else may read the phone). Ask "
              "them to reply YES to confirm, or call the clinic on the number at 1177.se to reschedule, and add that "
              "the clinic never asks for BankID or payment by SMS or phone. Never mention missed appointments or risk. "
              "Output only the SMS text.")


TRANSCRIPTS: dict[str, dict] = {}   # one transcript per patient, so it looks like a stored record


def call_script(p: dict, agent: str = "") -> dict:
    if p["id"] not in TRANSCRIPTS:
        TRANSCRIPTS[p["id"]] = _make_script(p)
    return TRANSCRIPTS[p["id"]]


def _make_script(p: dict) -> dict:
    facts = ("Do not mention the patient's age or sex. (Background only - never say symptoms or conditions aloud.) "
             f"Appointment: {p['department']} ({p['type']}), for {p['symptoms'].lower()}, "
             f"on {p['day']} in {p['month']}, booked {p['booked_days_ahead']} days ahead. "
             f"Chronic condition: {p['chronic']}.")
    if p["outcome"].startswith("call"):
        return claude(CALL_SYSTEM, facts + " " + CALL_STORY[p["outcome"]])
    return claude(SMS_SYSTEM, facts)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, data: dict) -> None:
        self._send(code, json.dumps(data).encode("utf-8"), "application/json")

    def _authorized(self) -> bool:
        """Optional password (HTTP Basic auth) so strangers can't use the public demo / API key."""
        if not DEMO_PASSWORD:
            return True
        header = self.headers.get("Authorization", "")
        if header.startswith("Basic "):
            try:
                _, _, pw = base64.b64decode(header[6:]).decode("utf-8").partition(":")
                if hmac.compare_digest(pw, DEMO_PASSWORD):
                    return True
            except Exception:
                pass
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Påminka demo", charset="UTF-8"')
        self.send_header("Content-Length", "0")
        self.end_headers()
        return False

    def do_GET(self):
        if self.path == "/healthz":                       # for Render's health check
            return self._send(200, b"ok", "text/plain")
        if not self._authorized():
            return
        if self.path in ("/test", "/index.html") and ASK_ENABLED:
            self._send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif self.path in ("/", "/demo", "/demo.html"):
            self._send(200, (HERE / "demo.html").read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/patients":
            if DEMO is None:
                return self._json(500, {"error": f"Dataset not found: {DATA}"})
            self._json(200, DEMO)
        elif self.path == "/status":
            self._json(200, {"key": client is not None, "model": MODEL})
        else:
            self._send(404, b"Not found", "text/plain")

    def do_POST(self):
        if not self._authorized():
            return
        if self.path not in ("/ask", "/call") or (self.path == "/ask" and not ASK_ENABLED):
            return self._send(404, b"Not found", "text/plain")
        if client is None:
            return self._json(400, {"error": "No API key. Put it in api_key.txt "
                                             "(or set ANTHROPIC_API_KEY) and restart server.py."})
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        try:
            if self.path == "/ask":
                question = body.get("question", "").strip()
                if not question:
                    return self._json(400, {"error": "Empty question."})
                self._json(200, claude(SYSTEM, question))
            else:
                p = BY_ID.get(body.get("id", ""))
                if p is None:
                    return self._json(404, {"error": "Unknown patient."})
                self._json(200, call_script(p, str(body.get("agent", ""))))
        except anthropic.AuthenticationError:
            self._json(401, {"error": "The API key was rejected - check api_key.txt."})
        except anthropic.APIStatusError as e:
            self._json(e.status_code, {"error": f"API error {e.status_code}: {e.message}"})
        except anthropic.APIConnectionError:
            self._json(503, {"error": "Could not reach the Claude API - check your internet."})

    def log_message(self, fmt, *args):  # keep the console quiet
        pass


if __name__ == "__main__":
    print(f"API key found: {'yes' if client else 'NO - set ANTHROPIC_API_KEY or add api_key.txt'}")
    print(f"Demo patients loaded: {len(BY_ID)}")
    print(f"Password protection: {'on' if DEMO_PASSWORD else 'off'}")
    print(f"Listening on {HOST}:{PORT} - open http://localhost:{PORT} (Ctrl+C to stop)", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
