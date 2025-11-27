Personal AI Assistant 

A modern desktop AI assistant built with Flask + JavaScript, featuring real-time voice commands, smart reminders with pop-ups, web-search, math solving, and time/date responses.

Important Requirement:
This project only works on Python 3.11.9.
(SpeechRecognition & PyAudio fail on Python 3.13 — downgrade using steps below.)

Features
Feature	Status	Description
-> Voice Recognition: Speak commands using browser microphone (Web Speech API)
-> Text-to-Speech: Assistant speaks responses + reminder alerts
-> Reminders System: Add, view, delete reminders — popup + automatic voice alert
-> Web Search: Answers general queries like "Who killed Indira Gandhi?"
-> Q&A + Conversation: Responds to natural queries conversationally
-> Math Solver: Evaluates expressions via voice or text
-> Time & Date: Get real-time system time and date
-> Clean UI: Sidebar, stats, hints, reminder list, voice status & more
📂 Project Structure
PA-V2/
│── backend/
│   ├── app.py                
│   ├── assistant.py
│   ├── reminder_manager.py
│   ├── speech_handler.py
│   ├── search_ai.py
│   ├── utils.py
│   ├── requirements.txt
│
│
│── frontend/
│   ├── index.html
│   ├── script.js
│   ├── style.css

Setup Guide
1. Install Python Version
install python 3.11.9

2️. Create Virtual Environment
cd backend
python -m venv venv
venv\Scripts\activate

3️. Install Dependencies
pip install -r requirements.txt

4️. Add API Keys
Create .env inside backend/:
GEMINI_API_KEY=YOUR_KEY
SERPER_API_KEY=YOUR_KEY

5️. Start Backend Server
cd backend
python app.py
Server runs at:
http://localhost:5000

6️. Start UI (Frontend)
Open:
frontend/index.html
Best opened via Live Server in VS Code.
How to Use the Assistant
-> Text Input
Type:
what is ai
calculate 14 * 5
what time is it

-> Voice Input
Click 🎤 → speak normally:

who is elon musk
set a reminder in 2 minutes to stretch

-> Reminders
remind me to drink water at 5pm
remind me to take medicine in 10 minutes


When time hits →
 Pop-up alert
 Voice output: "Reminder! drink water"



⭐ If you liked this repo — give it a star
