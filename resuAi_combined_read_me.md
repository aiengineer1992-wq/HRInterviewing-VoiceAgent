# ResuAI: End-to-End Shortlisting & Voice Interview

A fully local, privacy-first recruitment pipeline built with Streamlit. Upload candidate CVs, score them against a job description using a local LLM, then automatically conduct spoken voice interviews with every shortlisted candidate — all without sending data to any external service.

---

## What It Does

**Stage 1 — Shortlisting**
1. Upload multiple PDF or DOCX resumes through the browser UI.
2. Each resume is scored 0–100 against your job description by a local Ollama model.
3. Candidates above your chosen threshold are marked **Shortlisted** and their contact details are extracted.
4. Two CSVs are available for download: all results and shortlisted contacts only.

**Stage 2 — Voice Interview**
1. The app greets each shortlisted candidate by name using text-to-speech.
2. Five fixed questions are read aloud; the candidate's spoken response is recorded for 10 seconds.
3. Whisper transcribes the response locally; the LLM validates relevance before accepting it.
4. After all five answers are collected, the LLM assigns an interview score (0–100) and classifies overall sentiment (Positive / Neutral / Negative).
5. The process repeats for every shortlisted candidate; final results are available as a downloadable CSV.

---

## Project Structure

```
voice-Agents/
├── ResuAi_combined.py        # Main Streamlit application (this file)
├── requirements.txt          # Python dependencies
├── resuAi_combined_read_me.md
├── read_me_shortlisting_agent.md   # Standalone shortlisting agent docs
└── read_me_Voice_Agent.md          # Standalone voice agent docs
```

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.10+ | Tested with 3.11 |
| [Ollama](https://ollama.com) running locally | Must have `qwen2.5:7b` pulled |
| A working microphone | Used by sounddevice for recording |
| Audio output device | Used by pyttsx3 for TTS |

Pull the required Ollama model before running:

```bash
ollama pull qwen2.5:7b
ollama serve
```

---

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd voice-Agents

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt
```

> **Windows note:** `sounddevice` bundles the PortAudio DLL in its wheel, so no separate install is needed.

---

## Running the App

```bash
streamlit run ResuAi_combined.py
```

The app opens in your browser at `http://localhost:8501`.

---

## Usage Walkthrough

### Step 1 — Shortlisting

1. Paste the **Job Description** into the text area.
2. Upload one or more **PDF or DOCX** resumes using the file uploader.
3. Adjust the **score threshold** slider (default: 70). Candidates at or above this score are shortlisted.
4. Click **Run Shortlist**. A progress bar tracks processing.
5. Download **All CV Results** or **Shortlisted Contacts** CSVs.

### Step 2 — Voice Interview

Once shortlisting completes, the voice interview section appears automatically.

1. The app greets each candidate by name via audio.
2. Each of the five questions is read aloud. Click **Record Response** to capture the answer.
3. If the LLM deems the answer invalid, the question is repeated.
4. After five valid answers, scores and sentiment are displayed.
5. Click **Next Candidate** to proceed. When all interviews are done, download **Interview Results** CSV.

### Interview Questions (fixed script)

1. What position are you applying for?
2. Can you briefly describe your previous work experience?
3. What is your highest qualification?
4. Are you available for remote work?
5. What are your salary expectations?

---

## Configuration

| Constant | Location | Default | Description |
|---|---|---|---|
| `OLLAMA_MODEL` | Top of file | `qwen2.5:7b` | Ollama model used for all LLM calls |
| `OLLAMA_URL` | Top of file | `http://localhost:11434/api/generate` | Ollama REST endpoint |
| `SHORTLIST_THRESHOLD_DEFAULT` | Top of file | `70` | Default slider value for shortlist cutoff |
| `RESUME_PREVIEW_CHARS` | Top of file | `12000` | Max characters of each CV sent to the LLM |
| `duration` | `record_audio()` | `10` (seconds) | Length of each voice recording |

To switch Ollama models, change `OLLAMA_MODEL` at the top of the file:

```python
OLLAMA_MODEL = "llama3:8b"   # or mistral, phi3, gemma2, etc.
```

---

## Output Files

### Shortlisting — All CV Results

| Column | Description |
|---|---|
| `Filename` | Name of the uploaded file |
| `Score` | Match score 0–100 |
| `Shortlisted` | `Yes` if score >= threshold, else `No` |
| `Reason` | 40–50 word LLM explanation |

### Shortlisting — Shortlisted Contacts

| Column | Description |
|---|---|
| `Name` | Extracted from CV text (falls back to filename) |
| `Phone` | Extracted from CV text |
| `Email` | Extracted from CV text |

### Voice Interview Results

| Column | Description |
|---|---|
| `Name` | Candidate name |
| `Score` | 0–100 LLM interview score |
| `Sentiment` | Positive / Neutral / Negative |
| `Details` | LLM reasoning for the score and sentiment |

---

## Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web UI |
| `pandas` | DataFrames and CSV I/O |
| `sounddevice` | Microphone recording |
| `faster-whisper` | Offline speech-to-text (tiny/int8 model) |
| `pyttsx3` | Offline text-to-speech |
| `ollama` | Local LLM chat inference |
| `PyMuPDF` (`fitz`) | PDF text extraction |
| `python-docx` | DOCX text extraction |
| `requests` | Ollama REST API calls for shortlisting |
| `streamlit-aggrid` | Enhanced data grid display |

---

## How the LLM Prompts Work

**Shortlisting:** Each CV is truncated to 12,000 characters then sent with the job description. The model returns:
```
Score: <0–100>
Reason: <40–50 word explanation>
```

**Answer validation:** The model is given the question and transcribed answer and replies with either `Valid Answer` or `Invalid Answer`.

**Interview scoring:** All five Q&A pairs are sent together. The model returns a 0–100 score with a written explanation covering relevance, communication quality, and role fit.

**Sentiment analysis:** All transcribed answers are concatenated and classified as `Positive`, `Neutral`, or `Negative`.

---

## Retry & Error Handling

- Ollama calls during shortlisting retry up to **3 times** with exponential back-off (2 s, 4 s, 6 s).
- Files that are neither PDF nor DOCX are skipped silently.
- CVs that fail text extraction receive `Score: 0` and `Shortlisted: No`.

---

## Privacy

All processing — LLM inference, speech transcription, text-to-speech — runs **entirely on your local machine**. No candidate data is sent to any external API or cloud service.

---

## License

MIT
