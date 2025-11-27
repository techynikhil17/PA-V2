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


<img width="700" alt="homepage-1" src="https://github.com/user-attachments/assets/e6288d63-c1eb-4c98-9512-b8e2460516f8" />
<img width="700" alt="homepage-2" src="https://github.com/user-attachments/assets/88292e9c-1a4b-456e-8b9e-07859ea69d73" />
<img width="700" alt="math-problem" src="https://github.com/user-attachments/assets/523ccd2b-442d-4144-860a-4ddfb5ce4f96" />
<img width="700" alt="reminder" src="https://github.com/user-attachments/assets/16d7859a-bc26-4141-9f0a-173e17505a80" />
<img width="700" alt="reminder_triggered" src="https://github.com/user-attachments/assets/50e9dfed-8462-415d-bcd7-05664e8b0fae" />
<img width="700" alt="time" src="https://github.com/user-attachments/assets/ba39e746-069e-411c-8f3e-253e6863a9b4" />
<img width="700" alt="web-search" src="https://github.com/user-attachments/assets/d2c60e1b-3bb1-4921-a789-4d8215875eaa" />



⭐ If you liked this repo — give it a star
