
"""
Handles speech-to-text and text-to-speech functionality
"""
import speech_recognition as sr
import pyttsx3
import time
import threading


class SpeechHandler:
    """
    Manages speech input and output
    """
    
    def __init__(self):
        # Initialize recognizer for speech-to-text
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Initialize text-to-speech engine
        self.tts_engine = pyttsx3.init()
        self._configure_tts()
        
        # Thread lock for TTS
        self.tts_lock = threading.Lock()
    
    def _configure_tts(self):
        """Configure text-to-speech settings"""
        # Set properties
        self.tts_engine.setProperty('rate', 150)  # Speed of speech
        self.tts_engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
        
        # Try to set a voice (optional)
        voices = self.tts_engine.getProperty('voices')
        if voices:
            # Use first available voice (usually default)
            self.tts_engine.setProperty('voice', voices[0].id)
    
    def listen(self, timeout=5, phrase_time_limit=10):
        """
        Listen to microphone and convert speech to text
        Args:
            timeout: Seconds to wait for speech to start
            phrase_time_limit: Maximum seconds for phrase
        Returns:
            Recognized text or error message
        """
        try:
            with self.microphone as source:
                print("Listening...")
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Listen for audio
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_time_limit
                )
                
                print("Processing speech...")
                
                # Recognize speech using Google Speech Recognition
                text = self.recognizer.recognize_google(audio)
                print(f"You said: {text}")
                return text
                
        except sr.WaitTimeoutError:
            return "ERROR: No speech detected. Please try again."
        except sr.UnknownValueError:
            return "ERROR: Could not understand audio. Please speak clearly."
        except sr.RequestError as e:
            return f"ERROR: Could not request results; {e}"
        except Exception as e:
            return f"ERROR: An error occurred: {str(e)}"


class SpeechHandler:

    def __init__(self):
        pass  # NO persistent engine anymore

    def speak(self, text):
        try:
            engine = pyttsx3.init()   # <-- NEW: reinitialize every time
            engine.setProperty('rate', 175)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            del engine
        except Exception as e:
            print("🔴 TTS ERROR:", e)

    
    def test_microphone(self):
        """
        Test if microphone is working
        Returns:
            Boolean indicating if microphone is accessible
        """
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                return True
        except Exception as e:
            print(f"Microphone test failed: {str(e)}")
            return False
    
    def stop(self):
        """Stop the TTS engine"""
        try:
            self.tts_engine.stop()
        except Exception as e:
            print(f"Error stopping TTS engine: {str(e)}")