import time
from furhat_remote_api import FurhatRemoteAPI
from openai import OpenAI

# Connect to the Furhat robot
furhat = FurhatRemoteAPI("localhost")

# Create OpenAI assistant for the guessing game
assistant = client.beta.assistants.create(
    name="guessing_game",
    instructions="You are a player in a game much like Akinator. A participant will try to think of a celebrity and you will try to guess it by asking yes or no questions. It is turn-based. You will have 3 questions before you must decide and make a guess. Only respond with the questions until it is time to guess, be brief and concise. When it's your turn to guess, only say 'My guess is [celebrity name]'",
    tools=[{"type": "code_interpreter"}],
    model="gpt-4o"
)

# Create a new thread for the game
thread = client.beta.threads.create()

# Start a game session
furhat.say(text="Hello! Let's play a guessing game. Think of a celebrity, and I'll try to guess who it is. You can only answer yes or no.")
time.sleep(2)

# Initialize game variables
guesses = 0
max_guesses = 3
is_correct = False

# Game loop
while guesses < max_guesses:
    # Request GPT assistant for the next question
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )
    
    # Wait for GPT to generate a question
    time.sleep(7)
    
    # Retrieve the assistant's question
    run = client.beta.threads.runs.retrieve(
        thread_id=thread.id,
        run_id=run.id
    )
    
    # Retrieve all the messages from the thread
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    
    # Extract the latest question from the assistant
    question = None
    for message in messages.data:
        if message.role == "assistant":
            question = message.content[0].text.value
            break
    
    question_str = str(question)
    print(f"Assistant's Question: {question_str}")
    
    # Send the question to Furhat
    furhat.say(text=question_str)
    
    # Wait for the participant's response using Furhat's listener
    response = furhat.listen()  # This will block until a response is received
    print(f"Participant's Response: {response.message}")
    
    participant_response = str(response.message)
    
    # Send the participant's response back to OpenAI
    new_message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=participant_response
    )

    # Increment the number of guesses
    guesses += 1

furhat.say(text=f"I have made {max_guesses} now i will think of an answer")
run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )
    
# Wait for GPT to generate a question
time.sleep(7)
    
# Retrieve the assistant's question
run = client.beta.threads.runs.retrieve(
    thread_id=thread.id,
    run_id=run.id
    )
    
# Retrieve all the messages from the thread
messages = client.beta.threads.messages.list(thread_id=thread.id)
    
# Extract the latest question from the assistant
question = None
for message in messages.data:
    if message.role == "assistant":
        question = message.content[0].text.value
        break
    
question_str = str(question)
print(f"Assistant's Question: {question_str}")
    
# Send the question to Furhat
furhat.say(text=question_str)

    

print("I'm here")
