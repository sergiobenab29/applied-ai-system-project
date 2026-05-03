import streamlit as st
from datetime import date, time
from pawpal_system import AIParser, Owner, Pet, Task, Priority, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="", available_minutes_per_day=480)

owner: Owner = st.session_state.owner

st.title("🐾 PawPal+")

# --- Owner Info ---
st.subheader("Owner Info")
col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Your name", value=owner.name or "")
with col2:
    avail = st.number_input("Available minutes today", min_value=10, max_value=1440, value=owner.available_minutes_per_day)

if st.button("Save owner info"):
    owner.name = owner_name
    owner.available_minutes_per_day = avail
    st.success(f"Saved! Hi {owner.name}.")

st.divider()

# --- Add a Pet ---
st.subheader("Add a Pet")
col1, col2 = st.columns(2)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    owner.add_pet(Pet(name=pet_name, species=species))
    st.success(f"{pet_name} the {species} added!")

if owner.pets:
    st.write("Your pets:", [p.name for p in owner.pets])

st.divider()

# --- Add a Task ---
st.subheader("Add a Task")

if not owner.pets:
    st.info("Add a pet first before adding tasks.")
else:
    pet_names = [p.name for p in owner.pets]
    selected_pet_name = st.selectbox("Assign to pet", pet_names)
    selected_pet = next(p for p in owner.pets if p.name == selected_pet_name)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col4:
        recurring = st.selectbox("Recurring", ["none", "daily", "weekly"])

    if st.button("Add task"):
        selected_pet.add_task(Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=Priority(priority),
            recurring=None if recurring == "none" else recurring,
        ))
        st.success(f"Task '{task_title}' added to {selected_pet_name}.")

    # Show pending tasks per pet with mark-complete button
    for pet in owner.pets:
        pending = pet.get_pending_tasks()
        if pending:
            st.markdown(f"**{pet.name}'s pending tasks:**")
            for i, t in enumerate(pending):
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.write(f"{t.title} — {t.duration_minutes} min | {t.priority.value} priority"
                             + (f" | repeats {t.recurring}" if t.recurring else ""))
                with col_b:
                    if st.button("Done", key=f"done_{pet.name}_{i}"):
                        t.mark_completed()
                        pet.refresh_recurring_tasks(date.today())
                        st.rerun()

st.divider()

# --- AI Assistant ---
st.subheader("AI Assistant")

if not owner.pets:
    st.info("Add a pet first, then describe their tasks here.")
else:
    ai_description = st.text_area(
        "Describe what your pet needs",
        placeholder='e.g. "Max needs a 30-minute walk and his pill every morning"',
        height=80,
    )

    if st.button("Add tasks with AI"):
        if not ai_description.strip():
            st.warning("Please enter a description first.")
        else:
            try:
                parser = AIParser()
                parsed_tasks = parser.parse_tasks(ai_description)

                if not parsed_tasks:
                    st.error("The AI couldn't find any tasks in that description. Try being more specific.")
                else:
                    added = 0
                    for task_data in parsed_tasks:
                        matched_pet = next(
                            (p for p in owner.pets if p.name.lower() == task_data["pet_name"].lower()),
                            None,
                        )
                        if matched_pet is None:
                            st.warning(f"Pet '{task_data['pet_name']}' not found. Add them first.")
                            continue
                        matched_pet.add_task(Task(
                            title=task_data["title"],
                            duration_minutes=task_data["duration_minutes"],
                            priority=Priority(task_data["priority"]),
                        ))
                        added += 1

                    if added > 0:
                        st.success(f"Added {added} task(s) from your description!")
                        st.rerun()
            except ValueError as e:
                st.error(str(e))

st.divider()

# --- Generate Schedule ---
st.subheader("Build Schedule")

col1, col2 = st.columns(2)
with col1:
    day_start = st.time_input("Day starts at", value=time(8, 0))
with col2:
    day_end = st.time_input("Day ends at", value=time(18, 0))

if st.button("Generate schedule"):
    if not owner.pets or not owner.get_all_tasks():
        st.warning("Add at least one pet and one task first.")
    else:
        scheduler = Scheduler()
        schedule = scheduler.build_daily_schedule(
            owner=owner,
            pet=owner.pets[0],
            day_start=day_start,
            day_end=day_end,
        )

        # Scheduled tasks table (sorted by time)
        sorted_entries = scheduler.sort_by_time(schedule)
        if sorted_entries:
            st.success(f"Scheduled {len(sorted_entries)} task(s) for today.")
            st.table([{
                "Time": f"{e.start.strftime('%I:%M %p')} – {e.end.strftime('%I:%M %p')}",
                "Task": e.task.title,
                "Priority": e.task.priority.value,
                "Duration": f"{e.task.duration_minutes} min",
            } for e in sorted_entries])
        else:
            st.warning("No tasks could be scheduled in this time window.")

        # Skipped tasks
        if schedule.omitted_tasks:
            st.warning(f"{len(schedule.omitted_tasks)} task(s) didn't fit and were skipped:")
            for t in schedule.omitted_tasks:
                st.write(f"  - {t.title} ({t.duration_minutes} min)")

        # Schedule overlap conflicts
        overlap_conflicts = scheduler.detect_schedule_conflicts(schedule)
        for conflict in overlap_conflicts:
            st.error(f"Time conflict: {conflict}")

        # Per-pet overload / duplicate warnings
        for pet in owner.pets:
            for issue in scheduler.detect_conflicts(pet):
                st.warning(f"{pet.name}: {issue}")
