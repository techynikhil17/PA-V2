"""
Personal AI Assistant — FINAL VERSION
- Intent routing (time, date, math, reminders, search, greetings, exit, help)
- Uses Gemini+Serper for web search (via ai_web_search)
- Integrates with ReminderManager for reminders
"""

import re
from search_ai import ai_web_search
from utils import (
    get_current_time,
    get_current_date,
    extract_math_expression,
    calculate_math,
    extract_reminder_info,
)


class PersonalAssistant:
    def __init__(self, reminder_manager=None):
        self.name = "Assistant"
        self.history = []          # list of {"you": ..., "assistant": ...}
        self.rm = reminder_manager # ReminderManager instance

    # ================= MAIN ENTRY =================
    def process_command(self, cmd: str) -> str:
        """Main entry point from API."""
        if not cmd:
            return "I didn’t catch that, try again."

        cmd = cmd.lower().strip()
        self.history.append({"you": cmd})

        response = self._route(cmd)

        self.history.append({"assistant": response})
        return response

    # ================= ROUTER =====================
    def _route(self, c: str) -> str:
        # 1) Exit
        if self._is_exit_command(c):
            return "Goodbye! Take care."

        # 2) Help
        if self._is_help_query(c):
            return self._handle_help()

        # 3) Search / general Q&A (highest priority after exit/help)
        if self._is_search_query(c):
            return self._handle_search(c)

        # 4) Reminder
        if self._is_reminder_query(c):
            return self._handle_reminder(c)

        # 5) Math
        if self._is_math_query(c):
            return self._handle_math(c)

        # 6) Time & Date
        if self._is_time_query(c):
            return get_current_time()
        if self._is_date_query(c):
            return get_current_date()

        # 7) Greeting
        if self._is_greeting(c):
            return "Hello! I’m your personal assistant. How can I help you?"

        # Default fallback
        return "I’m not sure about that. Try asking me about time, date, math, web search, or reminders."

    # =============== INTENT DETECTORS ==============

    def _is_greeting(self, c: str) -> bool:
        words = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
        return any(w in c for w in words)

    def _is_exit_command(self, c: str) -> bool:
        return c in ["bye", "exit", "quit", "close", "goodbye"]

    def _is_help_query(self, c: str) -> bool:
        phrases = ["help", "what can you do", "commands", "how do i use you"]
        return any(p in c for p in phrases)

    def _is_time_query(self, c: str) -> bool:
        # avoid matching "times" in math
        return "time" in c and "times" not in c

    def _is_date_query(self, c: str) -> bool:
        return any(x in c for x in ["date", "day"]) and "update" not in c

    def _is_math_query(self, c: str) -> bool:
        # must contain a digit and a math keyword
        if not re.search(r"\d", c):
            return False

        math_words = [
            "calculate",
            "plus",
            "minus",
            "divide",
            "multiply",
            "times",
            "add",
            "subtract",
            "over",
            "x",
        ]
        if any(w in c for w in math_words):
            return True

        # or math symbols
        return bool(re.search(r"[+\-*/×÷]", c))

    def _is_search_query(self, c: str) -> bool:
        """
        General knowledge / Q&A routing.
        This intentionally catches broad questions like:
        - who killed indira gandhi
        - what is quantum computing
        - tell me about tesla
        """
        keywords = [
            "who",
            "what",
            "when",
            "where",
            "why",
            "how",
            "tell me about",
            "search",
            "find",
            "look up",
            "explain",
            "define",
            "information about",
        ]

        # Don’t steal pure math / time questions
        if self._is_math_query(c) or self._is_time_query(c):
            return False

        return any(k in c for k in keywords)

    def _is_reminder_query(self, c: str) -> bool:
        return any(x in c for x in ["remind", "reminder", "don't forget", "alert me", "notify me"])

    # ================= HANDLERS =====================

    def _handle_math(self, c: str) -> str:
        expr = extract_math_expression(c)
        if not expr:
            return "I couldn’t find a valid math expression. Try something like: 'calculate 14 × 6'."
        return calculate_math(expr)

    def _handle_search(self, c: str) -> str:
        """Delegate to Gemini+Serper."""
        return ai_web_search(c)

    def _handle_reminder(self, c: str) -> str:
        if not self.rm:
            return "Reminder system is not initialized."

        text, tm = extract_reminder_info(c)

        if not text:
            return "Tell me what to remind you about."
        if not tm:
            return "Also tell me when — like 'at 7 PM' or 'in 15 minutes'."

        result = self.rm.add_reminder(text, tm)
        return result.get("message", "Reminder added.")

    def _handle_help(self) -> str:
        return (
            "Here’s what I can do:\n"
            "• ⏰ Time — 'what time is it'\n"
            "• 📅 Date — 'what's today's date' or 'what day is it'\n"
            "• 🔢 Math — 'calculate 14 × 6', 'what is 25 plus 7'\n"
            "• 🔍 Web search — 'who killed Indira Gandhi', 'tell me about Python', 'search for AI news'\n"
            "• ⏰ Reminders — 'remind me to call mom at 8 PM', 'remind me in 10 minutes to drink water'\n"
            "• 💬 Casual chat — just talk to me normally!"
        )

    # ================= HISTORY =====================

    def get_history(self):
        return self.history

    def clear_history(self):
        self.history = []
