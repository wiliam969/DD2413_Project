import os
import openai
from openai import OpenAI
from furhat_remote_api import FurhatRemoteAPI
import time
from dotenv import load_dotenv

load_dotenv()

# Initialize Furhat and OpenAI API
furhat = FurhatRemoteAPI("localhost")
#furhat = FurhatRemoteAPI("192.168.1.114")  # Replace with Furhat's IP or "localhost"

def get_chatgpt_question(context):
    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        response = client.chat.completions.create(
            model="gpt-4",
            temperature=0.7,
            messages=[
                {
                    "role": "system", 
                    "content": """You are playing a maximum of 20 questions game to guess a celebrity. 
                    Ask strategic yes/no questions to narrow down the possibilities.
                    Based on previous answers, don't repeat similar questions.
                    After gathering enough information, make a guess.
                    Provide only the question without any additional text or punctuation.
                    Keep track of all previous answers to make informed guesses.. Provide only the question without any additional text or punctuation."""
                },
                {"role": "user", "content": context}
            ]
        )
        content = response.choices[0].message.content
        # Clean up the response - remove any extra spaces, newlines, or punctuation at the end
        content = content.strip('?.!').strip()
        print(f"Generated question: {content}")
        return content
    except Exception as e:
        print(f"Error with ChatGPT API: {e}")
        return "Sorry, I encountered an issue. Let's try again."
    
def wait_for_valid_response():
    """
    Listen for a response and detect if it contains 'yes' or 'no'.
    """
    print("Listening for response...")
    user_response = furhat.listen()  # Simulated Furhat's listening function
    print(f"Raw response: {user_response}")
    
    message = user_response.message.strip().lower()  # Access the 'message' attribute directly
    print(f"Parsed message: {message}")
    
    # Detect "yes" or "no" in the message using simple pattern matching
    if "yes" in message:
        print("Detected 'yes' response.")
        return "yes"
    elif "no" in message:
        print("Detected 'no' response.")
        return "no"
    
    # If neither "yes" nor "no" is detected
    print("No valid 'yes' or 'no' detected in the response.")
    furhat.say(text="I didn't understand that. Please answer yes or no.")
    return None



def guessing_game():
    # Initial introduction
    furhat.say(text = "Think of a celebrity and I will try to guess who it is")
    time.sleep(2)
    furhat.say(text ="Please answer my questions with yes or no")
    time.sleep(2)
    
    context = "I am trying to guess a celebrity. Previous answers: "
    questions_asked = 0
    
    while questions_asked < 20:  # Maximum 20 questions
        question = get_chatgpt_question(context)
        if question:
            furhat.say(text=question)
            print(f"Asked: {question}")
        else:
            furhat.say(text="I couldn't think of a question. Let me try again.")
            continue
        
        time.sleep(4)
        
        # Get response
        answer = wait_for_valid_response()
        if answer:
            questions_asked += 1
            context += f"\nQ{questions_asked}: {question} - A: {answer}"
            print(f"Updated context: {context}")
            
            # Try to guess after every 3 questions
            if questions_asked % 5 == 0:
                guess_prompt = f"{context}\nBased on these answers, make your best guess of who the celebrity is. Only provide the name."
                guess = get_chatgpt_question(guess_prompt)
                if guess:
                    furhat.say(text=f"Could it be {guess}?")
                    time.sleep(4)
                    guess_response = wait_for_valid_response()
                    if guess_response == 'yes':
                        furhat.say(text="Great! I guessed correctly!")
                        return
                    else:
                        furhat.say(text="Okay, let me continue asking questions.")
                        time.sleep(3)
        else:
            # If no valid response, skip to the next iteration
            furhat.say(text="Let's move to the next question.")
            continue

    
    # If we reach here, we've asked too many questions
    furhat.say(text = "I give up. Thank you for playing")

if __name__ == "__main__":
    guessing_game()