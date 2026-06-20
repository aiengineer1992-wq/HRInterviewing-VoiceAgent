# ResuAI Voice Interviewer

An automated voice-based HR interview agent built with Streamlit, Whisper, Ollama, and pyttsx3. It reads a list of candidates from a CSV file, conducts a five-question spoken interview with each one, validates answers with an LLM, scores the full interview, analyzes sentiment, and exports the results.

---

## Features

- **Text-to-speech greeting & questions** — pyttsx3 reads each question aloud (fully offline)
- **Voice recording** — sounddevice captures the candidate's spoken answer
- **Automatic transcription** — faster-whisper (tiny/int8) converts speech to text in real time
- **Answer validation** — Ollama (qwen2.5:7b) checks whether each answer is on-topic before accepting it
- **Interview scoring** — LLM assigns a 0–100 relevance score with a written explanation
- **Sentiment analysis** — classifies the overall transcript as Positive, Neutral, or Negative
- **CSV export** — results saved to `interview_results.csv` and available as an in-app download

---

## Project Structure

```
voice-Agents/
├── voice_agent.py        # Main Streamlit application
├── candidates.csv        # Input: list of candidates (Name, Email, Phone)
├── interview_results.csv # Output: generated after interviews complete
├── requirements.txt      # Python dependencies
└── read_me_Voice_Agent.md
```

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.10+ | Tested with 3.11 |
| [Ollama](https://ollama.com) running locally | Must have `qwen2.5:7b` pulled |
| A working microphone | Used by sounddevice |
| Audio output device | Used by pyttsx3 |

Pull the required Ollama model before running:

```bash
ollama pull qwen2.5:7b
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

> **Windows note:** sounddevice requires the [PortAudio](http://www.portaudio.com/) DLL. Install it via `pip install sounddevice` — the wheel bundles the DLL on Windows.

---

## Candidate Input Format

Edit `candidates.csv` before running. The file must have exactly these three columns:

```csv
Name,Email,Phone
Ahmed Raza,ahmed.raza@example.com,0300-1234567
Fatima Malik,fatima.malik@example.com,0312-2345678
```

---

## Running the App

```bash
streamlit run voice_agent.py
```

The app opens in your browser at `http://localhost:8501`.

### Interview flow

1. The agent greets the candidate and reads the first question aloud.
2. Click **Record Response** to capture a 10-second audio clip.
3. The clip is transcribed and validated. If irrelevant, the question is repeated.
4. After all five questions are answered, the LLM scores the interview and analyzes sentiment.
5. The process repeats for every candidate in `candidates.csv`.
6. When all interviews are done, results are saved to `interview_results.csv` and a download button appears.

### Interview questions (fixed script)

1. What position are you applying for?
2. Can you briefly describe your previous work experience?
3. What is your highest qualification?
4. Are you available for remote work?
5. What are your salary expectations?

---

## Output

`interview_results.csv` contains one row per candidate with the following columns:

| Column | Description |
|---|---|
| Candidate Name | From candidates.csv |
| Email | From candidates.csv |
| Phone | From candidates.csv |
| What position are you applying for? | Transcribed answer |
| Can you briefly describe... | Transcribed answer |
| What is your highest qualification? | Transcribed answer |
| Are you available for remote work? | Transcribed answer |
| What are your salary expectations? | Transcribed answer |
| Score | 0–100 LLM relevance score |
| Explanation | LLM reasoning for the score |
| Sentiment | Positive / Neutral / Negative |
| Sentiment Explanation | Brief LLM sentiment rationale |

---

## Dependencies

| Package | Purpose |
|---|---|
| streamlit | Web UI |
| pandas | CSV I/O |
| sounddevice | Microphone recording |
| faster-whisper | Speech-to-text (offline) |
| pyttsx3 | Text-to-speech (offline) |
| ollama | Local LLM inference (validation, scoring, sentiment) |
| numpy | Audio array handling |

---

## Configuration

Two constants at the top of `voice_agent.py` control file paths:

```python
CANDIDATES_CSV_PATH  # input CSV  (default: same directory as the script)
RESULTS_CSV          # output CSV (default: same directory as the script)
```

Recording duration defaults to **10 seconds**. Change the `duration` parameter in `record_audio()` to adjust.

---

## License

MIT
