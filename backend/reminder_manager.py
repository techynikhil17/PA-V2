"""
Reminder Manager - Handles scheduled reminders with notifications
"""

import threading
import time
import requests
from datetime import datetime, timedelta
import re


class ReminderManager:
    """Manages scheduled reminders"""

    def __init__(self):
        self.reminders = []
        self.reminder_id_counter = 0
        self.checker_thread = None
        self.running = False
        self.callback = None

    # -------------------------------------------------
    # SERVICE CONTROL
    # -------------------------------------------------
    def start(self, callback=None):
        """
        Start the reminder checker thread
        Args:
            callback: Function to call when reminder triggers (receives reminder dict)
        """
        if self.running:
            return

        self.callback = callback
        self.running = True
        self.checker_thread = threading.Thread(
            target=self._check_reminders, daemon=True
        )
        self.checker_thread.start()
        print("Reminder Service ✔ Running")

    def stop(self):
        """Stop the reminder checker thread"""
        self.running = False
        if self.checker_thread:
            self.checker_thread.join(timeout=2)
        print("Reminder Service ⏹ Stopped")

    # -------------------------------------------------
    # PUBLIC API
    # -------------------------------------------------
    def add_reminder(self, text, time_str):
        """
        Add a new reminder
        Args:
            text: Reminder text
            time_str: Time string (e.g., "3 PM", "15:30", "in 5 minutes")
        Returns:
            dict with reminder info or error
        """
        try:
            target_time = self._parse_time(time_str)

            if not target_time:
                return {
                    "success": False,
                    "message": "Invalid time format. Try '3 PM', '15:30', or 'in 10 minutes'.",
                }

            if target_time < datetime.now():
                return {
                    "success": False,
                    "message": "That time has already passed. Please specify a future time.",
                }

            self.reminder_id_counter += 1
            reminder = {
                "id": self.reminder_id_counter,
                "text": text.strip(),
                "time": target_time,
                "time_str": time_str,
                "created_at": datetime.now(),
                "triggered": False,
            }

            self.reminders.append(reminder)

            time_until = self._format_time_until(target_time)

            return {
                "success": True,
                "message": f"✅ Reminder set! I'll remind you to '{text}' at {target_time.strftime('%I:%M %p')} ({time_until})",
                "reminder": reminder,
            }

        except Exception as e:
            return {"success": False, "message": f"Error setting reminder: {str(e)}"}

    def get_reminders(self, include_triggered: bool = False):
        """
        Get list of reminders
        include_triggered=True  -> return all
        include_triggered=False -> only upcoming (NOT triggered)
        """
        if include_triggered:
            return self.reminders
        return [r for r in self.reminders if not r["triggered"]]

    def delete_reminder(self, reminder_id):
        """Delete a reminder by ID"""
        self.reminders = [r for r in self.reminders if r["id"] != reminder_id]

    def clear_all(self):
        """Clear all reminders"""
        self.reminders = []

    # -------------------------------------------------
    # INTERNAL HELPERS
    # -------------------------------------------------
    def _parse_time(self, time_str: str):
        """
        Parse time string to datetime
        Supports:
          - '3 PM', '7:45 pm', '07:30'
          - 'in 5 minutes', 'in 2 hours'
          - '7:45 p.m.' / '7:45 P.M.' (with dots)
        """
        if not time_str:
            return None

        now = datetime.now()

        # Normalise spacing / dots
        ts = time_str.strip().lower()
        ts = ts.replace("p.m.", "pm").replace("p. m.", "pm")
        ts = ts.replace("a.m.", "am").replace("a. m.", "am")
        ts = re.sub(r"\s+", " ", ts)

        # --- relative: "in 5 minutes / hours"
        m_rel = re.search(
            r"\bin\s+(\d+)\s*(minute|minutes|min|mins|hour|hours|hr|hrs)\b", ts
        )
        if m_rel:
            amount = int(m_rel.group(1))
            unit = m_rel.group(2)
            if "hour" in unit or "hr" in unit:
                return now + timedelta(hours=amount)
            else:
                return now + timedelta(minutes=amount)

        # --- "HH:MM am/pm" or "H am/pm"
        m_ampm = re.search(
            r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b",
            ts,
        )
        if m_ampm:
            hour = int(m_ampm.group(1))
            minute = int(m_ampm.group(2)) if m_ampm.group(2) else 0
            mer = m_ampm.group(3)

            if mer == "pm" and hour != 12:
                hour += 12
            if mer == "am" and hour == 12:
                hour = 0

            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target < now:
                target += timedelta(days=1)
            return target

        # --- pure 24h "HH:MM"
        m_24 = re.search(r"\b(\d{1,2}):(\d{2})\b", ts)
        if m_24:
            hour = int(m_24.group(1))
            minute = int(m_24.group(2))
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target < now:
                target += timedelta(days=1)
            return target

        return None

    def _format_time_until(self, target_time: datetime) -> str:
        """Format time until reminder as human-readable string"""
        delta = target_time - datetime.now()

        if delta.days > 0:
            return f"in {delta.days} day(s)"

        total_minutes = int(delta.total_seconds() // 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60

        if hours > 0 and minutes > 0:
            return f"in {hours} hour(s) and {minutes} minute(s)"
        if hours > 0:
            return f"in {hours} hour(s)"
        if minutes > 0:
            return f"in {minutes} minute(s)"
        return "very soon"

    def _check_reminders(self):
        """Background thread that checks and triggers reminders"""
        while self.running:
            now = datetime.now()

            for reminder in self.reminders:
                if not reminder["triggered"] and reminder["time"] <= now:
                    reminder["triggered"] = True
                    print(f"⏰ Reminder Triggered: {reminder['text']}")

                    # 1) Voice output
                    try:
                        requests.post(
                            "http://localhost:5000/speak",
                            json={"text": f"Reminder! {reminder['text']}"},
                            timeout=2,
                        )
                    except Exception as e:
                        print("TTS Failed:", e)

                    # 2) Frontend popup polling
                    try:
                        requests.get(
                            "http://localhost:5000/trigger_popup", timeout=2
                        )
                    except Exception as e:
                        print("Popup trigger failed:", e)

                    if self.callback:
                        try:
                            self.callback(reminder)
                        except Exception as e:
                            print("Reminder callback error:", e)

            time.sleep(3)
    def get_reminders_raw(self):
        """Return full internal reminder objects including triggered status."""
        return self.reminders  # Not formatted/filtered
