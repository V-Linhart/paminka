# Deploy the Påminka demo to Render

The app is one Python file (`server.py`) plus the page (`demo.html`), the dataset (`data/`) and the
model's risk scores (`model/risk_scores.csv`). Render runs it as a free web service.

## What is already prepared

| File | Purpose |
|---|---|
| `server.py` | Listens on Render's `PORT`, serves the demo at `/`, health check at `/healthz`, optional password |
| `requirements.txt` | `anthropic==2.12.0` (everything else is Python's standard library) |
| `render.yaml` | Render Blueprint: free web service, build + start commands, environment variables |
| `.gitignore` | Keeps `api_key.txt` and other secrets out of GitHub |

## 1. Make a separate API key in the Claude Console

1. Go to the Claude Console (platform.claude.com) → **API Keys** → **Create Key**, name it e.g. `paminka-render`.
2. Copy it once – you will paste it into Render in step 4. Do **not** put it in any file.
3. Console → **Settings → Limits**: set a **spend limit** (e.g. 10 USD). The site is public, so this caps the worst case.

Cost: the demo only calls Claude when someone clicks "View call transcript"/"View SMS conversation".
Each transcript is generated once per patient and then reused, ~0.4 US cents each.

## 2. Put the project on GitHub

Git is not installed on this PC, so use the GitHub website (no installation needed):

1. github.com → **New repository** → name `paminka-demo` → **Private** → Create.
2. On the empty repository page click **uploading an existing file**.
3. Open the `claude-hackathon` folder in Explorer and drag in **these** files and folders:
   - `server.py`, `demo.html`, `index.html`, `requirements.txt`, `render.yaml`, `.gitignore`
   - the folder `data` (contains `smart_hospital_appointment_dataset_with_noshow_pct.csv`)
   - the folder `model` (must contain `risk_scores.csv`)
4. **Do NOT upload `api_key.txt`.** (The pitch files are optional.)
5. Click **Commit changes**. Check that `api_key.txt` is not listed in the repository.

Tip: `.gitignore` starts with a dot and may be hidden in Explorer – it is optional for the upload.

## 3. Create the service on Render

1. render.com → sign in with GitHub.
2. **New → Blueprint** → choose the `paminka-demo` repository. Render reads `render.yaml`.
   (Alternative: **New → Web Service**, Runtime *Python 3*, Build command `pip install -r requirements.txt`,
   Start command `python server.py`, Instance type *Free*.)

## 4. Set the environment variables

In the service → **Environment**:

| Key | Value |
|---|---|
| `ANTHROPIC_API_KEY` | the Console key from step 1 |
| `DEMO_PASSWORD` | optional – a password the browser asks for (any user name works) |

Save → Render builds and deploys (2–3 minutes).

## 5. Open it

Your URL looks like `https://paminka-demo.onrender.com`. The log should show
`Demo patients loaded: 1055`.

## Good to know

- **Free plan sleeps** after ~15 minutes without visitors; the first visit then takes ~30–60 s.
  **Open the page a minute before you present.**
- Transcripts are kept in memory – after a restart or sleep, the first click on each patient takes
  ~5–10 s again. Click your 2–3 demo patients once before going on stage.
- The free-text "Ask Claude" test page (`/test`) is switched off on Render, so strangers cannot use
  your key for anything else.
- If you change a file: upload the new version on GitHub (open the file → pencil/upload → **Commit changes**) –
  Render redeploys automatically.
