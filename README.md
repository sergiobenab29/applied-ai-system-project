# PawPal+ AI Scheduling Assistant

PawPal+ helps pet owners plan their day. You describe what your pet needs in plain English, and the AI turns it into a scheduled task list automatically.

---

## Original Project

This builds on **PawPal+ (Module 2)**, a Streamlit app where users manually added pet care tasks and got a daily schedule. It handled priority sorting, recurring tasks, and conflict detection. The goal was to help busy pet owners stay consistent with their routines.

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
2. The AI (Gemini Flash) extracts task details from it
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

**4. Get a free Gemini API key**
- Go to [aistudio.google.com](https://aistudio.google.com)
- Sign in with Google and click **Get API key**

**5. Add your key**
```bash
export GEMINI_API_KEY="your-key-here"
```

**6. Run the app**
```bash
streamlit run app.py
```

---

## Sample Interactions

> _To be filled in once the AI feature is complete._

| Input | AI Output |
|-------|-----------|
| "My dog Max needs a 30-min walk and his pill" | _(add result here)_ |
| "Luna needs feeding twice a day and grooming" | _(add result here)_ |
| "Rocky has a 1-hour vet visit, high priority" | _(add result here)_ |

---

## Design Decisions

- **Gemini Flash** — free tier, no credit card needed, works well for short tasks
- **Built into the existing app** — the scheduling logic already worked, so the AI just adds a smarter input method
- **Guardrails first** — if the AI returns something unusable, the app shows an error instead of crashing
- **Flat file logging** — simple and good enough for a course project; a real app would use a proper database

---

## Testing

> _To be filled in after testing the AI feature._

The existing test suite covers 12 scheduling behaviors. After building the AI layer, tests will also check that valid inputs create correct tasks and that bad responses are caught safely.

---

## Reflection

The biggest thing I learned is that making AI reliable matters more than making it impressive. A feature that crashes silently is worse than no feature at all — so building error handling before anything else was the right move.

I also learned that AI works best when it removes friction from something people already want to do, not when it replaces things that already work.
