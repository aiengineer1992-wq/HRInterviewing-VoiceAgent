# CV Shortlisting Agent via Ollama

A local, privacy-first CV screening tool that uses a locally-running Ollama LLM to score candidate PDF resumes against a job description, announces progress via text-to-speech, and exports shortlisting results to a timestamped CSV.

---

## What It Does

1. Reads all PDF resumes from a specified folder.
2. Announces the start of screening aloud using text-to-speech (pyttsx3).
3. Sends each resume alongside a job description to a local Ollama model.
4. Receives a match score (0–100) and a short explanation for each candidate.
5. Marks candidates as **Shortlisted** if their score meets or exceeds the threshold (default: 70).
6. Exports all results to a timestamped CSV file.
7. Announces how many candidates were shortlisted when screening is complete.

---

## Project Structure

```
voice-Agents/
├── Shortlisting agent via Ollama.py   # This script
├── requirements.txt
└── read_me_shortlisting_agent.md
```

---

## Requirements

### System
- Python 3.9+
- [Ollama](https://ollama.com/) installed and running locally (`http://localhost:11434`)
- A pulled Ollama model (default: `qwen2.5:7b`)
- A working audio output device (used by pyttsx3 for TTS announcements)

### Python Packages
```bash
pip install pymupdf requests pyttsx3
```

| Package    | Purpose                                        |
|------------|------------------------------------------------|
| `pymupdf`  | Extract text from PDF resumes                  |
| `requests` | Call the local Ollama REST API                 |
| `pyttsx3`  | Text-to-speech announcements (fully offline)   |

---

## Setup

### 1. Install and Start Ollama
```bash
# Pull the default model
ollama pull qwen2.5:7b

# Start the Ollama server (runs on port 11434 by default)
ollama serve
```

### 2. Configure Paths

Open `Shortlisting agent via Ollama.py` and edit the `__main__` block:

```python
# Folder containing candidate PDF resumes
folder_path = "C:/path/to/your/cv_folder"
```

Edit the default value in `export_to_csv()` if you want results saved elsewhere:

```python
def export_to_csv(data, output_folder=r"C:\path\to\your\output_folder"):
```

### 3. Set the Job Description

Edit the `job_description` string in the `__main__` block to match the role you are screening for:

```python
job_description = """
We are looking for a Software Engineer with 2+ years of experience in Python ...
"""
```

---

## Configuration

| Variable        | Location                  | Default                              | Description                                      |
|-----------------|---------------------------|--------------------------------------|--------------------------------------------------|
| `OLLAMA_MODEL`  | Top of file               | `qwen2.5:7b`                         | Ollama model to use for scoring                  |
| `OLLAMA_URL`    | Top of file               | `http://localhost:11434/api/generate`| Ollama REST endpoint                             |
| `threshold`     | `parse_and_shortlist()`   | `70`                                 | Minimum score to mark a candidate as shortlisted |
| `folder_path`   | `__main__` block          | *(user-defined)*                     | Folder containing PDF resumes                    |
| `output_folder` | `export_to_csv()`         | *(user-defined)*                     | Folder where the CSV report is saved             |

---

## Usage

```bash
python "Shortlisting agent via Ollama.py"
```

The script will:
- Announce "Starting CV screening. Please wait." via TTS.
- Print progress to the console as it processes each PDF.
- Print raw LLM responses for debugging.
- Print the final shortlisted candidates to the console.
- Save a CSV report like `cv_results_20240610_143022.csv` to the output folder.
- Announce how many candidates were shortlisted when complete.

---

## Output CSV Format

| Column       | Description                                      |
|--------------|--------------------------------------------------|
| `Filename`   | Name of the PDF file                             |
| `Score`      | Match score returned by the model (0–100)        |
| `Shortlisted`| `Yes` if score >= threshold, otherwise `No`      |
| `Reason`     | 40–50 word explanation from the model            |

---

## How the LLM Prompt Works

Each CV is truncated to 12,000 characters before being sent to avoid exceeding the model's context window. The model is asked to return output in this exact format:

```
Score: <number>
Reason: <40–50 word explanation>
```

The script parses these two lines from the response. If parsing fails, the candidate receives a score of 0 and the error is recorded in the Reason column.

---

## Retry & Error Handling

- The Ollama call retries up to **3 times** on failure.
- Back-off delays: **10 s** then **20 s** between attempts.
- Non-PDF files in the input folder are automatically skipped with a console message.
- If a CV fails to parse, it is still included in the CSV with `Score: 0` and `Shortlisted: No`.

---

## Switching Models

Change `OLLAMA_MODEL` at the top of the file to any model you have pulled:

```python
OLLAMA_MODEL = "llama3:8b"   # or mistral, phi3, gemma2, etc.
```

Larger models generally produce more nuanced reasoning but are slower.

---

## Privacy

All processing runs **entirely on your local machine**. No CV data is sent to any external API or cloud service.
