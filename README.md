# PawPal+ AI Scheduling Assistant

PawPal+ helps pet owners plan their day. You describe what your pet needs in plain English, and the AI turns it into a scheduled task list automatically.

---

## Original Project

This builds on **PawPal+**, a Streamlit app where users manually added pet care tasks and got a daily schedule. It handled priority sorting, recurring tasks, and conflict detection. The goal was to help busy pet owners stay consistent with their routines.

---

## What's New

Instead of filling out a form, you just type something like:

> "My dog needs a 30-minute walk and his pill every morning"

The AI reads it, creates the tasks, and adds them to your schedule.

---

## System Diagram

![System Architecture](assets/flowchart.png)

**How data flows:**
1. You type a description in the app
2. The AI (Groq / Llama 3.1) extracts task details from it
3. The app checks the response is valid before using it
4. Tasks get added to your schedule
5. Everything is logged in `ai_log.txt`

---

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/sergiobenab29/applied-ai-system-project.git
cd applied-ai-system-project
```

**2. Create a virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Get a free Groq API key**
- Go to [console.groq.com](https://console.groq.com)
- Sign up and click **API Keys** → **Create API key**

**5. Add your key**
```bash
export GROQ_API_KEY="your-key-here"
```

**6. Run the app**
```bash
streamlit run app.py
```

---

## Demo

[Watch the demo on Loom](https://www.loom.com/share/06ca5536adcf45a3b56032b46643155e)

---

## Sample Interactions

**Input 1:** `"Mochi needs a 30-minute walk and her pill at 7am every morning"`
- Morning walk — 30 min | medium priority | morning | repeats daily
- Give heartworm pill — 5 min | high priority | 7am | repeats daily

**Input 2:** `"Luna needs feeding in the evening and a grooming session on weekends"`
- Evening meal — 10 min | medium priority | evening | repeats daily
- Grooming — 45 min | low priority | repeats weekly

**Input 3:** `"Rocky has an important vet visit at 3pm this week"`
- Vet visit — 60 min | high priority | 3pm

---

## Design Decisions

- **Groq / Llama 3.1** — free, globally available, and fast. Gemini was the original plan but had regional quota restrictions, so we switched to Groq which works without billing.
- **Built into the existing app** — the scheduling logic already worked well, so the AI just adds a smarter input method instead of replacing what was there.
- **Prompt engineering over complexity** — instead of a multi-step agent, a single well-crafted prompt extracts all needed fields (title, duration, priority, recurring). Simple and reliable.
- **Guardrails before features** — the parser validates every AI response before using it. Bad or missing fields are caught and logged instead of crashing the app.
- **Flat file logging** — `ai_log.txt` is simple and good enough for a course project. A production app would use a proper logging service.

---

## Testing

The original 12 tests all still pass after adding the AI feature. I also tested the AI manually:

- Task titles, durations, and priorities came out correctly for all test inputs
- Specific times like "7am" were extracted correctly
- One-time tasks no longer get marked as recurring after fixing the prompt
- Bad inputs show a clear error message instead of crashing

Run the tests with:
```bash
python3 -m pytest tests/ -v
```

---

## Reflection

The hardest part was getting the AI to follow instructions consistently. Early on, the model marked a one-time vet visit as "weekly" just because the description said "this week." Fixing it taught me that good prompts need to be very specific about edge cases.

I also learned that keeping AI logic in one place made it easy to swap from Gemini to Groq without touching the rest of the app.

Building this made me realize how much work goes into making AI actually reliable, not just functional.
