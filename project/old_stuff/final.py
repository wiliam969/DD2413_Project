import time
from furhat_remote_api import FurhatRemoteAPI
from openai import OpenAI

# Connect to the Furhat robot
furhat = FurhatRemoteAPI("localhost")

# Create OpenAI assistant for the guessing game
assistant = client.beta.assistants.create(
    name="guessing_game",
    instructions="You are a player in a game like Akinator. A participant will think of a celebrity, and you will try to guess it by asking yes or no questions. Be concise in your questions. When told to make a guess, you have to make a guess. You can have a short dialog early if you want, but the game starts immedietly and you ask the first question",
    tools=[{"type": "code_interpreter"}],
    model="gpt-4"
)

# Create a new thread for the game
thread = client.beta.threads.create()

# Start a game session
furhat.say(text="Hello! Let's play a guessing game. Think of a celebrity, and I'll try to guess who it is")
time.sleep(4)

# Initialize game variables
guesses = 0
max_guesses = 10

#This is litteraly only to initialize the response.message
class Response:
    def __init__(self):
        self.message = None

# Game loop
while guesses < max_guesses:
    # Request GPT assistant for the next question
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant.id)
    time.sleep(3)  # Wait for GPT to generate a question
    
    # Retrieve the assistant's question
    run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    
    # Extract the latest question from the assistant
    question = None
    for message in messages.data:
        if message.role == "assistant":
            question = message.content[0].text.value
            break
    
    # Send the question to Furhat
    question_str = str(question)
    print(f"Assistant's Question: {question_str}")
    furhat.say(text=question_str)
    
    start_time = time.time()

    response = Response()

    while not response.message:
        
        # Listen for a response
        response = furhat.listen()  
        #print(response)
        print("Waiting for response...")

    if response and response.message:
        print(f"Participant's Response: {response.message}")
        participant_response = str(response.message)

        # Send the participant's response back to OpenAI
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=participant_response
        )
    else:
        # Handle case where there is no valid response
        participant_response = "No answer"  
        print("im in no answer")
        # Send the fallback response back to OpenAI
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=participant_response
        )
    
    # Increment the number of guesses
    guesses += 1

furhat.say(text="Now I'll make my guess.")
time.sleep(2)

client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="Now make your guess"
        )

# Final guess from the assistant
run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant.id)
time.sleep(5)  # Wait for the assistant to think

# Retrieve and send the final guess
run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
messages = client.beta.threads.messages.list(thread_id=thread.id)

# Extract the assistant's guess
guess = None
for message in messages.data:
    if message.role == "assistant":
        guess = message.content[0].text.value
        break

# Send the guess to Furhat
furhat.say(text=f"{guess}")
