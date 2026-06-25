import openai

openai.api_key = "YOUR_OPENAI_API_KEY"

def generate_variations(prompt, n=10):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # or "gpt-3.5-turbo" for cheaper/faster
        messages=[
            {"role": "system", "content": "You are an AI that paraphrases user queries for training a chatbot."},
            {"role": "user", "content": f"Give me {n} different ways a user might say: '{prompt}'"}
        ],
        temperature=0.7
    )
    output = response['choices'][0]['message']['content']
    return output.strip().split("\n")

# Example
variations = generate_variations("Is the box locked?")
for i, v in enumerate(variations, 1):
    print(f"{i}. {v.strip('- ').strip()}")
