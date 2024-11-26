import os
from openai import OpenAI
from furhat_remote_api import FurhatRemoteAPI
import time
from dotenv import load_dotenv
from datetime import datetime, timedelta
import re

load_dotenv()

# Initialize Furhat and OpenAI API
#furhat = FurhatRemoteAPI("localhost")
furhat = FurhatRemoteAPI("192.168.1.114")  # Replace with Furhat's IP or "localhost"

def get_chatgpt_emotions(context):
    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        response = client.chat.completions.create(
            model="gpt-4",
            temperature=0.7,
            messages=[
                {
                    "role": "system", 
                    "content": """You are playing a game with a human and you try to guess the right celebrity.
                    While doing so, your task is to show an appropriate facial expression to the user. 
                    You are provided with the Gamestate of the Game. 
                    in which the variable gameState.lastFacialExpression is the emotional state of the human you are playing with.
                    Your task is to return the emotional reponse you think would suit the situation best. 
                    You can choose from the following emotions: ["BigSmile", "Blink", "BrowFrown", "BrowRaise"]
                    <express(happiness)>
                    """
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
                    Keep track of all previous answers to make informed guesses..
                    Provide only the question without any additional text or punctuation.
                    express(emotion): Given a string emotion name, change your facial expression to match that emotion. The
                    list of available emotions is [BigSmile, Blink, BrowFrown, BrowRaise, CloseEyes, ExpressAnger, ExpressDisgust, ExpressSad, GazeAway, Nod, Oh, OpenEyes, Roll, Shake, Surprise, Thoughtful, Wink]. 
                    Every response should start by calling an action function to express an appropriate available expression, like
                    the following example. <express(BigSmile)>.
                    """
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

    gameState.lastGuess = message
    
    # Detect "yes" or "no" in the message using simple pattern matching
    if "yes" in message:
        print("Detected 'yes' response.")
        gameState.totalNumberofCorrectGuesses+= 1
        return "yes"
    elif "no" in message:
        print("Detected 'no' response.")
        gameState.totalNumberofWrongGuesses+= 1
        return "no"
    
    # If neither "yes" nor "no" is detected
    print("No valid 'yes' or 'no' detected in the response.")
    furhat.say(text="I didn't understand that. Please answer yes or no.")
    time.sleep(3)
    return None

class GameState(object):
    def __init__(self):
        self.totalNumberofQuestionsAsked = 0
        self.totalNumberofCorrectGuesses = 0        
        self.totalNumberofWrongGuesses = 0        
        self.previousAnswers = ""
        self.lastRobotFacialExpression = "sad"
        self.lastHumanFacialExpression = "sad"
        self.lastEmotionalStateAccess = None
        
    def toString(self): 
        return str("totalNumberofQuestionsAsked: " + str(self.totalNumberofQuestionsAsked) + 
                   "totalNumberofCorrectGuesses: " + str(self.totalNumberofCorrectGuesses) + 
                   "totalNumberofWrongGuesses: " + str(self.totalNumberofWrongGuesses) + 
                   "previousAnswers: " + str(self.previousAnswers) + 
                   "lastFacialExpression: " + str(self.lastRobotFacialExpression) + 
                   "furHatEmotions: " + str(self.lastHumanFacialExpression))
    

gameState = GameState()

def guessing_game():
    furhat.say(text = "Think of a celebrity and I will try to guess who it is")
    time.sleep(2)
    furhat.say(text ="Please answer my questions with yes or no")
    time.sleep(2)
    
    context = "I am trying to guess a celebrity. Previous answers: "
    
    while gameState.totalNumberofQuestionsAsked < 20:  # Maximum 20 questions
        gameState.totalNumberofQuestionsAsked += 1
        question = get_chatgpt_question(context)
        pattern = r"<express\([^)]*\)>"
        matches = re.findall(pattern, question)
        
        if question:
            if matches:
                question = question.replace(matches[0], "")    
            
            furhat.say(text=question)
            print(f"Asked: {question}")
        else:
            furhat.say(text="I couldn't think of a question. Let me try again.")
            continue
        
        time.sleep(3)
                
        if matches:
            idx1 =  matches[0].index("(")
            idx2 =  matches[0].index(")")
            gameState.lastRobotFacialExpression =  matches[0][idx1 + len("("): idx2]
            furhat.gesture(name=gameState.lastRobotFacialExpression)

        with open ("emotions.csv", "r" ) as humanEmotions:
            gameState.lastHumanFacialExpression = humanEmotions.read()

        # Get response
        answer = wait_for_valid_response()
        if answer:
            gameState.previousAnswers += f"\nQ{gameState.totalNumberofQuestionsAsked}: {question} - A: {answer}"
            context += gameState.previousAnswers
            context += "Here is the current state of the game and some other statistics which might be useful" + gameState.toString() 
            
            print(f"Updated context: {context}")
            
            # Try to guess after every 3 questions
            if gameState.totalNumberofQuestionsAsked % 5 == 0:
                guess_prompt = f"{gameState.previousAnswers}\n Based on these answers and the current statistics, make your best guess of who the celebrity is. Only provide the name."
                print("guessprompt: "  + guess_prompt)
                guess = get_chatgpt_question(guess_prompt)
                
                pattern = r"<express\([^)]*\)>"
                matches = re.findall(pattern, guess)
                
                if guess:
                    if matches:
                        guess = guess.replace(matches[0], "")    
                        
                    furhat.say(text=f"Could it be {guess}?")
                    time.sleep(3)
                    guess_response = wait_for_valid_response()
                    if guess_response == 'yes':
                        furhat.say(text="Great! I guessed correctly!")
                        break
                    else:
                        furhat.say(text="Okay, let me continue asking questions.")
                        time.sleep(3)
        else:
            # If no valid response, skip to the next iteration
            furhat.say(text="Let's move to the next question.")
            time.sleep(3)
            continue
    
    # If we reach here, we've asked too many questions
    furhat.say(text = "I give up. Thank you for playing")

if __name__ == "__main__":
    guessing_game()