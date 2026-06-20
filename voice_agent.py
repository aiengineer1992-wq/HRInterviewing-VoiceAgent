import streamlit as st
import pandas as pd
import sounddevice as sd
from datetime import datetime
from faster_whisper import WhisperModel
import pyttsx3
import ollama
import os
import re

# Configure the Streamlit page layout
st.set_page_config(page_title="Voice Interview Agent", layout="centered")

# -------------------------------
# Config
# -------------------------------
# Resolve paths relative to this script so the app works from any working directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CANDIDATES_CSV_PATH = os.path.join(SCRIPT_DIR, "candidates.csv")   # input: list of candidates to interview
SAVE_FOLDER_PATH = SCRIPT_DIR
RESULTS_CSV = os.path.join(SAVE_FOLDER_PATH, "interview_results.csv")  # output: scored interview data

# -------------------------------
# Load Models
# -------------------------------
@st.cache_resource  # cache across reruns so the model loads only once per session
def load_models():
    # "tiny" model balances speed vs. accuracy; int8 quantization reduces memory usage
    whisper_model = WhisperModel("tiny", compute_type="int8")
    return whisper_model

whisper_model = load_models()

# -------------------------------
# Audio Playback
# -------------------------------
def play_audio(text):
    # pyttsx3 is an offline TTS engine — no internet or API key needed
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    engine.stop()  # release the audio device so subsequent calls don't block

# -------------------------------
# LLM Validator & Scoring (via Ollama)
# -------------------------------
def validate_answer(question, answer):
    # Ask the LLM whether the candidate's answer is on-topic for the question
    prompt = f"Is the following answer relevant to the question?\nQuestion: {question}\nAnswer: {answer}\nRespond with 'Yes' or 'No' only."
    result = ollama.chat(model="qwen2.5:7b", messages=[{"role": "user", "content": prompt}])
    return result["message"]["content"].strip()

def score_interview(data):
    # Collect only substantive Q&A pairs (skip metadata keys like Name/Email)
    qas = "\n".join([f"Q: {q}\nA: {a}" for q, a in data.items() if q.startswith("What") or q.startswith("Are")])
    prompt = f"""
    You are an HR expert. Based on the following answers, give a relevance score from 0 to 100 and provide a short, clear explanation of why you gave that score:
    {qas}
    Score and explanation:
    """
    result = ollama.chat(model="qwen2.5:7b", messages=[{"role": "user", "content": prompt}])

    score_text = result["message"]["content"].strip()

    # Extract the first integer found in the response as the numeric score
    match = re.search(r"(\d{1,3})", score_text)
    score = int(match.group()) if match else "Invalid score"
    # Everything after the score number is treated as the explanation
    explanation = score_text[match.end():].strip() if match else "No explanation provided"

    return score, explanation

def analyze_sentiment(all_answers):
    # Concatenate all answers into one block for holistic sentiment analysis
    joined_answers = " ".join(all_answers)
    prompt = f"""
    Analyze the sentiment of the following text (a job interview transcript). Respond with a single word: Positive, Neutral, or Negative — and give a brief explanation.

    Transcript: {joined_answers}

    Sentiment and Explanation:
    """
    result = ollama.chat(model="qwen2.5:7b", messages=[{"role": "user", "content": prompt}])

    sentiment_text = result["message"]["content"].strip()

    # Parse the sentiment label and separate the explanation
    match = re.search(r"(Positive|Neutral|Negative)", sentiment_text, re.IGNORECASE)
    sentiment = match.group() if match else "Unknown"
    explanation = sentiment_text[match.end():].strip() if match else "No explanation found."

    return sentiment.capitalize(), explanation

# -------------------------------
# Audio Recording & Transcription
# -------------------------------
def record_audio(duration=10, fs=16000):
    # 16 kHz mono is the native sample rate expected by Whisper
    st.info("🎙 Recording... Please answer now.")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
    sd.wait()  # block until recording finishes
    st.success("✅ Recording complete.")
    return audio[:, 0]  # return 1-D array (drop the channel dimension)

def transcribe_audio(audio):
    # Whisper returns an iterable of segments; join them into a single transcript string
    segments, _ = whisper_model.transcribe(audio, language="en")
    return " ".join([seg.text for seg in segments])

# -------------------------------
# Main App
# -------------------------------
def main():
    st.title("🗣 ResuAI Voice Interviewer")

    # Guard: if all candidates have been interviewed, show the download panel and exit
    if "interview_data" in st.session_state and "current_index" in st.session_state:
        if st.session_state.current_index >= len(st.session_state.candidates):
            st.success("✅ All interviews complete!")
            df = pd.DataFrame(st.session_state.interview_data)
            try:
                df.to_csv(RESULTS_CSV, index=False)
                st.write("Results saved to:")
                st.code(RESULTS_CSV)

                csv_bytes = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download Interview Results as CSV",
                    data=csv_bytes,
                    file_name="interview_results.csv",
                    mime="text/csv"
                )
            except Exception as e:
                st.error(f"❌ Failed to save results: {e}")
            return

    # Initialize session state on first run
    if "candidates" not in st.session_state:
        st.session_state.candidates = pd.read_csv(CANDIDATES_CSV_PATH).to_dict(orient="records")
    if "current_index" not in st.session_state:
        st.session_state.current_index = 0
    if "interview_data" not in st.session_state:
        st.session_state.interview_data = []

    # Fetch the current candidate by index
    candidate = st.session_state.candidates[st.session_state.current_index]
    st.subheader(f"Interviewing: {candidate['Name']}")

    # Fixed interview script — same five questions for every candidate
    questions = [
        "What position are you applying for?",
        "Can you briefly describe your previous work experience?",
        "What is your highest qualification?",
        "Are you available for remote work?",
        "What are your salary expectations?"
    ]

    # Per-candidate state: step tracks which question we're on
    if "step" not in st.session_state:
        st.session_state.step = 0
        st.session_state.answers = {}
        st.session_state.greeted = False

    # Greet the candidate exactly once (before the first question)
    if st.session_state.step == 0 and not st.session_state.get("greeted", False):
        greeting = f"Hello {candidate['Name']}, this is HR from Blutech Consulting. Let's begin. {questions[0]}"
        play_audio(greeting)
        st.session_state.greeted = True

    if st.session_state.step < len(questions):
        current_q = questions[st.session_state.step]
        st.markdown(f"### ❓ {current_q}")

        if st.button("🎙 Record Response"):
            audio = record_audio()
            text = transcribe_audio(audio)
            st.write(f"🗣 You said: **{text}**")

            valid = validate_answer(current_q, text)
            if "no" in valid.lower():
                # Irrelevant answer — prompt the candidate to try again without advancing
                st.warning("⚠️ That didn't seem relevant. Please try again.")
                play_audio(f"That didn't seem relevant. {current_q}")
            else:
                # Valid answer — store it and advance to the next question
                st.session_state.answers[current_q] = text
                st.session_state.step += 1

                if st.session_state.step < len(questions):
                    play_audio(questions[st.session_state.step])
                else:
                    # All questions answered — attach metadata and run AI scoring
                    st.session_state.answers["Candidate Name"] = candidate["Name"]
                    st.session_state.answers["Email"] = candidate["Email"]
                    st.session_state.answers["Phone"] = candidate["Phone"]

                    score, explanation = score_interview(st.session_state.answers)
                    st.session_state.answers["Score"] = score
                    st.session_state.answers["Explanation"] = explanation

                    all_answer_texts = list(st.session_state.answers.values())
                    sentiment, sentiment_expl = analyze_sentiment(all_answer_texts)
                    st.session_state.answers["Sentiment"] = sentiment
                    st.session_state.answers["Sentiment Explanation"] = sentiment_expl

                    st.session_state.interview_data.append(st.session_state.answers)

                    # Reset per-candidate state and advance to the next candidate
                    st.session_state.step = 0
                    st.session_state.current_index += 1
                    st.session_state.greeted = False

                    if st.session_state.current_index < len(st.session_state.candidates):
                        st.rerun()
                    else:
                        # Last candidate done — save and offer download
                        df = pd.DataFrame(st.session_state.interview_data)
                        try:
                            df.to_csv(RESULTS_CSV, index=False)
                            st.success("✅ All interviews completed!")
                            st.write("Results saved to:")
                            st.code(RESULTS_CSV)

                            csv_bytes = df.to_csv(index=False).encode("utf-8")
                            st.download_button(
                                label="📥 Download Interview Results as CSV",
                                data=csv_bytes,
                                file_name="interview_results.csv",
                                mime="text/csv"
                            )
                        except Exception as e:
                            st.error(f"❌ Failed to save results: {e}")
                    return

if __name__ == "__main__":
    main()
