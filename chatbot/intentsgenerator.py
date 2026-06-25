"""
Optional helper: use the OpenAI API to paraphrase a query into several
training patterns for intents.json.

The API key is read from the OPENAI_API_KEY environment variable.
NEVER hardcode your key here.

Run:  export OPENAI_API_KEY=sk-...   (then)   python intentsgenerator.py
"""
import os
import openai

openai.api_key = os.environ.get("OPENAI_API_KEY")
if not openai.api_key:
    raise SystemExit("Set the OPENAI_API_KEY environment variable first.")


def generate_variations(prompt, n=10):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an AI that paraphrases user queries for training a chatbot."},
            {"role": "user", "content": f"Give me {n} different ways a user might say: '{prompt}'"},
        ],
        temperature=0.7,
    )
    output = response["choices"][0]["message"]["content"]
    return output.strip().split("\n")


if __name__ == "__main__":
    variations = generate_variations("Is the box locked?")
    for i, v in enumerate(variations, 1):
        print(f"{i}. {v.strip('- ').strip()}")
