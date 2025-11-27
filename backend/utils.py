"""
Utility functions for Personal Assistant
- Time & date
- Math
- Web search helper
- Reminder NLP extraction
"""

import re
from datetime import datetime
import math
import requests
import os

# ================= TIME & DATE ===================

def get_current_time():
    now = datetime.now()
    return now.strftime("The current time is %I:%M %p")

def get_current_date():
    now = datetime.now()
    return now.strftime("Today's date is %A, %B %d, %Y")


# ================= MATH ===================

def calculate_math(expression: str) -> str:
    """
    Safely evaluate a basic math expression.
    Supported: + - * / ** () and integers/decimals.
    """
    try:
        # Only allow safe characters
        if not re.fullmatch(r"[0-9\.\+\-\*\/\(\)\s]+", expression):
            return "I can only calculate basic numeric expressions."
        result = eval(expression, {"__builtins__": {}}, {})
        if isinstance(result, float):
            # avoid 7.0 style
            if math.isclose(result, round(result)):
                result = int(round(result))
        return f"The result is {result}"
    except ZeroDivisionError:
        return "Division by zero is not allowed."
    except Exception:
        return "I couldn't evaluate that expression. Please check the numbers and operators."

def extract_math_expression(command: str) -> str | None:
    """
    Extract a math expression from a natural language command.
    Examples:
      "calculate 5 plus 3" -> "5+3"
      "what is 12 * 8" -> "12*8"
    """
    c = command.lower()

    # Replace word operators with symbols
    replacements = {
        r"\bplus\b": "+",
        r"\badd(ed)?\b": "+",
        r"\bminus\b": "-",
        r"\bsubtract(ed)?\b": "-",
        r"\binto\b": "*",
        r"\btimes\b": "*",
        r"\bmultiply\b": "*",
        r"\bmultiplied by\b": "*",
        r"\bdivided by\b": "/",
        r"\bdivide\b": "/",
        r"\bover\b": "/",
    }
    expr = c
    for pattern, sym in replacements.items():
        expr = re.sub(pattern, f" {sym} ", expr)

    # Take everything from the first digit/symbol onwards
    m = re.search(r"[0-9\(\)]+.*", expr)
    if not m:
        return None

    expr = m.group(0)
    expr = re.sub(r"[^0-9\.\+\-\*\/\(\)\s]", " ", expr)
    expr = re.sub(r"\s+", "", expr)
    return expr if expr else None


# ================= BASIC WEB SEARCH (SERPER) ===================

def search_web(query: str) -> str:
    """
    Fallback simple web search using Serper.dev (if API key configured).
    Returns a short summary string.
    """
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return "Web search is not configured. Please add a SERPER_API_KEY."

    try:
        resp = requests.post(
            "https://google.serper.dev/search",
            json={"q": query, "num": 3},
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            timeout=8,
        )
        data = resp.json()
        snippets = []

        for item in (data.get("organic") or [])[:3]:
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            if title or snippet:
                snippets.append(f"- {title}: {snippet}")

        if not snippets:
            return "No results found. Try a more specific query."

        return "Here are some results I found:\n" + "\n".join(snippets)

    except Exception as e:
        return f"Web search failed: {e}"


# ================= REMINDER NLP ===================

def extract_reminder_info(command: str):
    """
    Extract (reminder_text, time_str) from natural-language reminder commands.

    Handles patterns like:
      - "remind me to call John at 7:45 pm"
      - "set a reminder at 7:45 pm to call John"
      - "reminder to call John at 7:45 p.m."
      - "in 20 minutes remind me to drink water"
      - "set reminder after 1 hour to take a break" (treated as 'in 1 hour')
    """

    original = command.strip()
    text_lower = original.lower()

    # normalise AM/PM variants in a working copy
    norm = text_lower
    norm = norm.replace("p.m.", "pm").replace("p. m.", "pm")
    norm = norm.replace("a.m.", "am").replace("a. m.", "am")
    norm = re.sub(r"\s+", " ", norm)

    time_str = None
    time_span = None  # (start, end) indices in original string

    # -------- 1) relative "in X minutes/hours" / "after X minutes" ----------
    rel_pattern = r"\b(in|after)\s+\d+\s+(minutes?|minute|mins?|hours?|hour|hrs?)\b"
    m_rel = re.search(rel_pattern, norm)
    if m_rel:
        time_str = norm[m_rel.start() : m_rel.end()]
        time_span = m_rel.start(), m_rel.end()

    # -------- 2) "at HH:MM am/pm" or "at 7 pm" ----------
    if not time_str:
        at_pattern = r"\bat\s+(\d{1,2}(:\d{2})?\s*(am|pm)?)\b"
        m_at = re.search(at_pattern, norm)
        if m_at:
            # group(1) is time part only
            time_str = m_at.group(1)
            time_span = m_at.start(), m_at.end()

    # -------- 3) bare time somewhere ("7:45 pm", "7 pm") ----------
    if not time_str:
        bare_time_pattern = r"\b(\d{1,2}(:\d{2})?\s*(am|pm))\b"
        m_time = re.search(bare_time_pattern, norm)
        if m_time:
            time_str = m_time.group(1)
            time_span = m_time.start(), m_time.end()

    # -------- 4) pure 24h time like "19:30" ----------
    if not time_str:
        m_24 = re.search(r"\b\d{1,2}:\d{2}\b", norm)
        if m_24:
            time_str = norm[m_24.start() : m_24.end()]
            time_span = m_24.start(), m_24.end()

    # If still nothing -> no time parsed at all
    if not time_str or time_span is None:
        return None, None

    # Normalize time_str for ReminderManager
    t_norm = time_str.strip()
    t_norm = t_norm.replace("p.m.", "pm").replace("p. m.", "pm")
    t_norm = t_norm.replace("a.m.", "am").replace("a. m.", "am")
    t_norm = re.sub(r"\s+", " ", t_norm)

    # Now build reminder text by removing the time phrase from the original
    start, end = time_span
    # Map indices from norm back to original: lengths are same except case, so safe.
    reminder_raw = (original[:start] + original[end:]).strip()

    # Remove leading helper phrases: "remind me to", "set a reminder", etc.
    cleanup_patterns = [
        r"(?i)^\s*remind me to\s+",
        r"(?i)^\s*remind me\s+",
        r"(?i)^\s*set (a )?reminder (for )?(to )?",
        r"(?i)^\s*set (a )?reminder\s+",
        r"(?i)^\s*reminder (to )?",
        r"(?i)\s*at\s*$",
    ]
    text_clean = reminder_raw
    for pat in cleanup_patterns:
        text_clean = re.sub(pat, "", text_clean).strip()

    # Fallbacks: if still empty, try extracting after "to "
    if not text_clean:
        m_to = re.search(r"(?i)to (.+)", original)
        if m_to:
            text_clean = m_to.group(1).strip()

    # Final clean: trim punctuation
    text_clean = text_clean.strip(" ,.-")

    return (text_clean, t_norm if t_norm else None)
