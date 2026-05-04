from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import List, Optional

logging.basicConfig(
    filename="ai_log.txt",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


_PRIORITY_ORDER = {Priority.high: 0, Priority.medium: 1, Priority.low: 2}


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: Priority = Priority.medium
    completed: bool = False
    recurring: Optional[str] = None  # "daily", "weekly", or None
    notes: Optional[str] = None
    due_date: Optional[date] = field(default_factory=date.today)
    time_of_day: Optional[str] = None  # e.g. "morning", "evening", "afternoon"

    def mark_completed(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def is_due_today(self, today: date) -> bool:
        """Return True if this task's due date is today or earlier."""
        if self.due_date is None:
            return True
        return self.due_date <= today

    def next_occurrence(self) -> Optional[Task]:
        """Return a fresh copy of this task scheduled for its next due date, or None if not recurring."""
        if self.recurring == "daily":
            next_due = (self.due_date or date.today()) + timedelta(days=1)
        elif self.recurring == "weekly":
            next_due = (self.due_date or date.today()) + timedelta(weeks=1)
        else:
            return None
        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            recurring=self.recurring,
            notes=self.notes,
            due_date=next_due,
        )


@dataclass
class Pet:
    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's task list."""
        self.tasks.append(task)

    def get_pending_tasks(self) -> List[Task]:
        """Return only tasks that have not been completed yet."""
        return [t for t in self.tasks if not t.completed]

    def refresh_recurring_tasks(self, today: date) -> None:
        """For every completed recurring task, add the next occurrence if not already scheduled."""
        new_tasks = []
        for task in self.tasks:
            if task.completed and task.recurring:
                next_task = task.next_occurrence()
                if next_task and not any(
                    t.title == next_task.title and t.due_date == next_task.due_date
                    for t in self.tasks
                ):
                    new_tasks.append(next_task)
        self.tasks.extend(new_tasks)


@dataclass
class Owner:
    name: str
    available_minutes_per_day: int = 480
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's pet list."""
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Task]:
        """Return every task across all of this owner's pets."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks


@dataclass
class ScheduleEntry:
    task: Task
    start: time
    end: time
    reason: str


@dataclass
class ScheduleResult:
    entries: List[ScheduleEntry] = field(default_factory=list)
    omitted_tasks: List[Task] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class Scheduler:
    @staticmethod
    def build_daily_schedule(
        owner: Owner,
        pet: Pet,
        day_start: time,
        day_end: time,
    ) -> ScheduleResult:
        """Build a priority-sorted schedule fitting all pending tasks into the given time window."""
        result = ScheduleResult()

        # Collect pending tasks from ALL owner pets, sorted by priority
        all_tasks: List[Task] = []
        for p in owner.pets:
            all_tasks.extend(p.get_pending_tasks())
        # Sort by priority first, then by duration (shorter tasks first to fit more in)
        all_tasks.sort(key=lambda t: (_PRIORITY_ORDER[t.priority], t.duration_minutes))

        # Calculate available time window in minutes
        start_dt = datetime.combine(datetime.today(), day_start)
        end_dt = datetime.combine(datetime.today(), day_end)
        remaining = int((end_dt - start_dt).total_seconds() / 60)
        current_dt = start_dt

        for task in all_tasks:
            if task.duration_minutes <= remaining:
                task_end = current_dt + timedelta(minutes=task.duration_minutes)
                result.entries.append(
                    ScheduleEntry(
                        task=task,
                        start=current_dt.time(),
                        end=task_end.time(),
                        reason=f"Priority: {task.priority.value}",
                    )
                )
                current_dt = task_end
                remaining -= task.duration_minutes
            else:
                result.omitted_tasks.append(task)

        if result.omitted_tasks:
            result.warnings.append(
                f"{len(result.omitted_tasks)} task(s) skipped — not enough time in the day."
            )

        return result

    @staticmethod
    def detect_conflicts(pet: Pet) -> List[str]:
        """Check a pet's task list for time overloads or duplicate entries."""
        conflicts = []
        pending = pet.get_pending_tasks()

        total = sum(t.duration_minutes for t in pending)
        if total > 480:
            conflicts.append(
                f"{pet.name}'s tasks total {total} min, which exceeds a typical 8-hour day."
            )

        titles = [t.title for t in pending]
        seen: set = set()
        for title in titles:
            if titles.count(title) > 1 and title not in seen:
                conflicts.append(f"Duplicate task found: '{title}'")
                seen.add(title)

        return conflicts

    @staticmethod
    def detect_schedule_conflicts(schedule: ScheduleResult) -> List[str]:
        """Return warnings for any entries whose time windows overlap in the built schedule."""
        sorted_entries = sorted(schedule.entries, key=lambda e: e.start)
        return [
            f"Conflict: '{a.task.title}' ends at {a.end.strftime('%I:%M %p')} "
            f"but '{b.task.title}' starts at {b.start.strftime('%I:%M %p')}."
            for a, b in zip(sorted_entries, sorted_entries[1:])
            if a.end > b.start
        ]

    @staticmethod
    def sort_by_time(schedule: ScheduleResult) -> List[ScheduleEntry]:
        """Return schedule entries sorted by start time."""
        return sorted(schedule.entries, key=lambda e: e.start)

    @staticmethod
    def filter_tasks(owner: Owner, pet_name: Optional[str] = None, completed: Optional[bool] = None) -> List[Task]:
        """Filter tasks across all pets by pet name and/or completion status."""
        tasks = owner.get_all_tasks()
        if pet_name is not None:
            tasks = [t for p in owner.pets if p.name == pet_name for t in p.tasks]
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        return tasks

    @staticmethod
    def explain_plan(schedule: ScheduleResult) -> str:
        """Return a human-readable summary of the schedule and any skipped tasks."""
        if not schedule.entries:
            return "No tasks were scheduled."

        lines = ["Plan for today:\n"]
        for entry in schedule.entries:
            lines.append(
                f"  {entry.start.strftime('%I:%M %p')} - {entry.end.strftime('%I:%M %p')}: "
                f"{entry.task.title} ({entry.task.priority.value} priority)"
            )

        if schedule.omitted_tasks:
            lines.append("\nSkipped (not enough time):")
            for task in schedule.omitted_tasks:
                lines.append(f"  - {task.title} ({task.duration_minutes} min)")

        if schedule.warnings:
            lines.append("\nWarnings:")
            for w in schedule.warnings:
                lines.append(f"  ! {w}")

        return "\n".join(lines)


class AIParser:
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set.")
        from groq import Groq
        self.client = Groq(api_key=api_key)

    def parse_tasks(self, description: str) -> List[dict]:
        prompt = (
            "You are a pet care assistant. Extract pet care tasks from the description below "
            "and return ONLY a JSON array. No explanation, no markdown.\n\n"
            "Each item must have these exact fields:\n"
            '- "pet_name": the pet\'s name (string)\n'
            '- "title": specific, descriptive task name — e.g. "Morning walk", "Give heartworm pill", "Vet checkup" (string)\n'
            '- "duration_minutes": realistic estimate in minutes — walks 20-60 min, meals 10 min, pills 5 min, grooming 30-60 min, vet visits 60 min (integer)\n'
            '- "priority": one of "low", "medium", or "high" — meds and vet visits are high, walks medium, grooming low (string)\n'
            '- "recurring": "daily" only if the description says "every day" or "daily", "weekly" only if it says "every week" or "weekly", null for everything else including "this week" or one-time events (string or null)\n'
            '- "time_of_day": use the exact time if mentioned (e.g. "7am", "4pm"), otherwise use "morning", "afternoon", or "evening", or null if not mentioned at all (string or null)\n\n'
            f'Description: "{description}"\n\n'
            "Return ONLY the JSON array."
        )

        logging.info("AI request: %s", description)

        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.choices[0].message.content.strip()
            logging.info("AI response: %s", raw)

            # Strip markdown code fences if the model wraps the response
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            tasks = json.loads(raw)

            validated = []
            for task in tasks:
                required = ("pet_name", "title", "duration_minutes", "priority")
                if not all(k in task for k in required):
                    logging.warning("Task missing required fields, skipping: %s", task)
                    continue
                if not isinstance(task["duration_minutes"], int) or task["duration_minutes"] <= 0:
                    logging.warning("Invalid duration for task, defaulting to 15: %s", task)
                    task["duration_minutes"] = 15
                if task["priority"] not in ("low", "medium", "high"):
                    logging.warning("Invalid priority for task, defaulting to medium: %s", task)
                    task["priority"] = "medium"
                validated.append(task)

            return validated

        except json.JSONDecodeError as e:
            logging.error("Failed to parse AI response as JSON: %s | Raw: %s", e, raw)
            raise ValueError("The AI returned an unreadable response. Please try again.")
        except Exception as e:
            logging.error("AI call failed: %s", e)
            raise ValueError(f"AI error: {e}")
