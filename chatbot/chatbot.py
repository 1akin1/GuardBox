import pyrebase

firebase_config = {
  "apiKey": "YOUR_FIREBASE_API_KEY",
  "authDomain": "guardbox-7f898.firebaseapp.com",
  "databaseURL": "https://guardbox-7f898-default-rtdb.europe-west1.firebasedatabase.app",
  "projectId": "guardbox-7f898",
  "storageBucket": "guardbox-7f898.firebasestorage.app",
  "messagingSenderId": "YOUR_SENDER_ID",
  "appId": "YOUR_FIREBASE_APP_ID"
}

firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()

import json
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import nltk
from nltk.stem.porter import PorterStemmer
from nltk.tokenize import TreebankWordTokenizer
import random
import speech_recognition as sr
import pyttsx3

engine = pyttsx3.init()
engine.setProperty("rate", 150)  # Speed of speech

nltk.download('punkt')
nltk.data.path

# Make sure NLTK uses the correct data directory first
nltk.data.path.append(r"C:\Users\Zihni\AppData\Roaming\nltk_data")

# Now download the tokenizer AFTER setting path
nltk.download('punkt', download_dir=r"C:\Users\Zihni\AppData\Roaming\nltk_data")

stemmer = PorterStemmer()


tokenizer = TreebankWordTokenizer()

def tokenize(sentence):
    return tokenizer.tokenize(sentence)
    
def stem(word):
    return stemmer.stem(word.lower())

def bag_of_words(tokenized_sentence, all_words):
    tokenized = [stem(w) for w in tokenized_sentence]
    return np.array([1 if w in tokenized else 0 for w in all_words], dtype=np.float32)

def fetch_guardbox_stats():
    ref = db.reference('/guardbox_stats')
    return ref.get()


def speak(text):
    print("Bot:", text)
    engine.say(text)
    engine.runAndWait()

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


tokenizer = TreebankWordTokenizer()
sentence = "This is a test sentence for tokenization."
tokens = tokenizer.tokenize(sentence)
print(tokens)

with open("intents.json", "r") as f:
    intents = json.load(f)

all_words = []
tags = []
xy = []

for intent in intents['intents']:
    tag = intent['tag']
    tags.append(tag)
    for pattern in intent['patterns']:
        w = tokenize(pattern)
        all_words.extend(w)
        xy.append((w, tag))

ignore_words = ['?', '!', '.', ',']
all_words = sorted(set(stem(w) for w in all_words if w not in ignore_words))
tags = sorted(set(tags))

X_train = []
y_train = []

for (pattern_sentence, tag) in xy:
    bag = bag_of_words(pattern_sentence, all_words)
    X_train.append(bag)
    y_train.append(tags.index(tag))

X_train = np.array(X_train)
y_train = np.array(y_train)

class ChatDataset(Dataset):
    def __init__(self):
        self.n_samples = len(X_train)
        self.x_data = X_train
        self.y_data = y_train

    def __getitem__(self, index):
        return self.x_data[index], self.y_data[index]

    def __len__(self):
        return self.n_samples

batch_size = 8
train_loader = DataLoader(dataset=ChatDataset(), batch_size=batch_size, shuffle=True)

input_size = len(X_train[0])
hidden_size = 8
output_size = len(tags)

class NeuralNet(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes):
        super(NeuralNet, self).__init__()
        self.l1 = nn.Linear(input_size, hidden_size)
        self.l2 = nn.Linear(hidden_size, hidden_size)
        self.l3 = nn.Linear(hidden_size, num_classes)
        self.relu = nn.ReLU()

    def forward(self, x):
        out = self.relu(self.l1(x))
        out = self.relu(self.l2(out))
        return self.l3(out)

model = NeuralNet(input_size, hidden_size, output_size)

criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

epochs = 1000
for epoch in range(epochs):
    for words, labels in train_loader:
        # Ensure correct data types
        words = words.to(torch.float32)
        labels = labels.to(torch.long)

        outputs = model(words)
        loss = criterion(outputs, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    if (epoch + 1) % 100 == 0:
        print(f"Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}")

print("Training complete.")

data = {
    "model_state": model.state_dict(),
    "input_size": input_size,
    "hidden_size": hidden_size,
    "output_size": output_size,
    "all_words": all_words,
    "tags": tags
}

torch.save(data, "chatbot_model.pth")
print("Model saved.")

import torch
import json

# Load trained data
data = torch.load("chatbot_model.pth")

input_size = data["input_size"]
hidden_size = data["hidden_size"]
output_size = data["output_size"]
all_words = data["all_words"]
tags = data["tags"]
model_state = data["model_state"]

# Load intents
with open("intents.json", "r") as f:
    intents = json.load(f)

# Initialize model
model = NeuralNet(input_size, hidden_size, output_size)
model.load_state_dict(model_state)
model.eval()

def get_response(msg):
    sentence = tokenize(msg)
    X = bag_of_words(sentence, all_words)
    X = torch.from_numpy(X).unsqueeze(0)

    output = model(X)
    _, predicted = torch.max(output, dim=1)
    tag = tags[predicted.item()]

    probs = torch.softmax(output, dim=1)
    confidence = probs[0][predicted.item()]

    if confidence.item() > 0.6:
        # === Realtime Sensor Queries ===
        if tag == "check_weight":
            try:
                weight = db.child("guardbox").child("weight").get().val()
                if weight is not None:
                    return f"The current weight is {weight:.2f} grams."
                else:
                    return "I couldn't retrieve the weight right now."
            except Exception as e:
                return f"Error accessing weight: {e}"
                
        elif tag == "box_status":
            locked = db.child("guardbox").child("locked").get().val()
            return "The box is currently locked." if locked else "The box is currently unlocked."
                
        elif tag == "check_vibration":
            vibration = db.child("guardbox").child("vibration").get().val()
            return "Yes, vibration has been detected recently." if vibration else "No vibration has been detected."

        elif tag == "check_package":
            weight = db.child("guardbox").child("weight").get().val()
            if weight is not None and weight >= 100:
                return f"Yes, there is a package inside. The weight is approximately {weight:.0f} grams."
            else:
                return "No, the box appears to be empty."

        # === New Stats Queries ===
        elif tag == "vibration_count":
            count = db.child("guardbox_stats").child("vibrations").get().val()
            return f"The box has recorded {count} vibration events." if count is not None else "I couldn't retrieve the vibration count."

        elif tag == "lock_count":
            count = db.child("guardbox_stats").child("locked").get().val()
            return f"The box has been locked {count} times." if count is not None else "I couldn't retrieve the lock count."

        elif tag == "delivery_count":
            count = db.child("guardbox_stats").child("deliveries").get().val()
            return f"There have been {count} package deliveries." if count is not None else "I couldn't retrieve the delivery count."

        # === Fallback to intents.json ===
        else:
            for intent in intents["intents"]:
                if tag == intent["tag"]:
                    return random.choice(intent["responses"])

    return "I'm not sure I understand. Can you try again?"


# Loop to talk

# Toggle this to False if you want text mode
voice_mode = True

print("Chatbot is running! Say 'quit' or 'bye' to exit.\n")

while True:
    if voice_mode:
        sentence = listen()
        if sentence is None:
            continue
        print("You:", sentence)
    else:
        sentence = input("You: ")

    exit_phrases = [
        "quit", "bye", "goodbye", "see you later",
        "catch you later", "talk to you soon", "see ya", "see you"
    ]

    if sentence.lower() in [phrase.lower() for phrase in exit_phrases]:
        response = get_response(sentence)
        if voice_mode:
            speak(response)
        else:
            print("Bot:", response)
        break

    response = get_response(sentence)
    if voice_mode:
        speak(response)
    else:
        print("Bot:", response)
