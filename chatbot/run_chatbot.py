"""
Interactive GuardBox chatbot loop (voice or text).

Run:  python run_chatbot.py

Set VOICE_MODE below to choose input mode:
    True  -> listen via microphone and speak replies (needs SpeechRecognition,
             pyttsx3 and PyAudio/PortAudio installed)
    False -> type your messages
Say or type "quit"/"bye" to exit.
"""
from chatbot import get_response

VOICE_MODE = False

EXIT_PHRASES = {
    "quit", "bye", "goodbye", "see you later",
    "catch you later", "talk to you soon", "see ya", "see you",
}

if VOICE_MODE:
    import speech_recognition as sr
    import pyttsx3

    _engine = pyttsx3.init()
    _engine.setProperty("rate", 150)

    def speak(text):
        print("Bot:", text)
        _engine.say(text)
        _engine.runAndWait()

    def listen():
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Listening... (say 'quit' to stop)")
            audio = recognizer.listen(source)
        try:
            return recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            print("Couldn't understand audio.")
            return None
        except sr.RequestError as e:
            print("Speech recognition service error:", e)
            return None


def main():
    print("Chatbot is running! Say or type 'quit'/'bye' to exit.\n")
    while True:
        if VOICE_MODE:
            sentence = listen()
            if sentence is None:
                continue
            print("You:", sentence)
        else:
            sentence = input("You: ")

        response = get_response(sentence)

        if VOICE_MODE:
            speak(response)
        else:
            print("Bot:", response)

        if sentence.lower().strip() in EXIT_PHRASES:
            break


if __name__ == "__main__":
    main()
