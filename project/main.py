import operator
import py_trees
import py_trees.console as console
import os
from openai import OpenAI
from furhat_remote_api import FurhatRemoteAPI
import time
from dotenv import load_dotenv
from datetime import datetime, timedelta
import re

load_dotenv()

#furhat = FurhatRemoteAPI(os.getenv('FURHAT_IP'))
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
furhat = FurhatRemoteAPI("localhost")
##############################################################################
# Classes
##############################################################################

class GameState(object):
    def __init__(self):
        self.totalNumberofQuestionsAsked = 0
        self.totalNumberofCorrectGuesses = 0        
        self.totalNumberofWrongGuesses = 0        
        self.previousAnswers = ""
        self.lastRobotFacialExpression = "sad"
        self.lastHumanFacialExpression = "sad"
        self.lastEmotionalStateAccess = None
        self.totalNumberOfInteraction = 0
        
    def toString(self): 
        return str("totalNumberofQuestionsAsked: " + str(self.totalNumberofQuestionsAsked) + 
                   "totalNumberofCorrectGuesses: " + str(self.totalNumberofCorrectGuesses) + 
                   "totalNumberofWrongGuesses: " + str(self.totalNumberofWrongGuesses) + 
                   "previousAnswers: " + str(self.previousAnswers) + 
                   "lastFacialExpression: " + str(self.lastRobotFacialExpression) + 
                   "furHatEmotions: " + str(self.lastHumanFacialExpression))

class furHatMediator(object): 
    def __init__(self):
        self.currentMessage = ""
        self.latestResponse = ""        

class furHatSays(py_trees.behaviour.Behaviour):

    def __init__(self, name, message):
        super().__init__(name=name)
        self.gameState = rGameState.gameState
        self.message = message

    def update(self):
        self.gameState.totalNumberOfInteraction += 1
        
        furhat.say(text=self.message)
        time.sleep(3)
        
        print("[furHat said]: " + self.message)
        
        return py_trees.common.Status.SUCCESS
    
class chatGPTToFurhat(py_trees.behaviour.Behaviour):

    def __init__(self, name):
        super().__init__(name=name)
        self.gameState = rGameState.gameState
        self.blackboard = self.attach_blackboard_client(name="ChatGPT", namespace="ChatGPT_")
        
        self.blackboard.register_key("message", access=py_trees.common.Access.READ)

    def update(self):
        self.gameState.totalNumberOfInteraction += 1
        
        furhat.say(text=self.blackboard.message)
        time.sleep(3)
        
        print("[furHat said]: " + self.blackboard.message)
        
        return py_trees.common.Status.SUCCESS

class furHatListens(py_trees.behaviour.Behaviour):

    def __init__(self, name):
        super().__init__(name=name)
        self.gameState = rGameState.gameState
        self.furHatMediator = wfurHatMediator.furHatMediator

    def update(self):
        self.gameState.totalNumberOfInteraction += 1
        
        furHatResponse = furhat.listen()
        print ("Listenning...")
        
        if furHatResponse.message == "":
            return py_trees.common.Status.FAILURE 
         
        self.furHatMediator.latestResponse = furHatResponse.message.strip().lower()
        print("[furHat heard]: " + furHatResponse.message)
        
        return py_trees.common.Status.SUCCESS

class askChatGPT(py_trees.behaviour.Behaviour):

    def __init__(self, name, messageToLLM):
        super().__init__(name=name)
        self.gameState = rGameState.gameState
        self.messageToLLM = messageToLLM
        self.blackboard = self.attach_blackboard_client(name="ChatGPT", namespace="ChatGPT_")
        
        self.blackboard.register_key("message", access=py_trees.common.Access.WRITE)

    def update(self):        
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
                {"role": "user", "content": self.messageToLLM}
            ]
        )
        content = response.choices[0].message.content
        # Clean up the response - remove any extra spaces, newlines, or punctuation at the end
        content = content.strip('?.!').strip()
        
        self.blackboard.message = content
        print(f"[Chat-GPT said]: {content}")
        
        return py_trees.common.Status.SUCCESS
        
def create_root() -> py_trees.behaviour.Behaviour:
    """
    Create the root behaviour and it's subtree.

    Returns:
        the root behaviour
    """
    root = py_trees.composites.Sequence(name="Warming Up", memory=True)
    
    action1 = furHatSays(name="furHatSays", message="Think of a celebrity and I will try to guess who it is")
    action2 = furHatSays(name="furHatSays", message="Please answer my questions with yes or no")
    
    root.add_children(
        [
            action1,
            action2
        ]
    )
    
    for i in range(1, 8):
        guessingIteration = py_trees.composites.Sequence(name="Guessing Iteration: {i}", memory=True)
        
        reqLLM = askChatGPT(name="idk man", messageToLLM="I am trying to guess a celebrity. Previous answers:")
        execLLM = chatGPTToFurhat(name="chatGPTToFurhat")
        listenPlayer = furHatListens(name="furHatListens")
        
        guessingIteration.add_child(reqLLM)
        
        repeat_on_failure = py_trees.decorators.Repeat("repeat listening process on failure", listenPlayer, 1)
        
        para_listen_speech = py_trees.composites.Parallel(
        name="Parallising of listening and speeching",
        policy=py_trees.common.ParallelPolicy.SuccessOnAll(),
        )
        
        para_listen_speech.add_child(execLLM)
        para_listen_speech.add_child(repeat_on_failure)        
        guessingIteration.add_child(para_listen_speech)
        
        isAnswerCorrect = py_trees.behaviours.CheckBlackboardVariableValue(
        name="Check for YES/NO",
        check=py_trees.common.ComparisonExpression(
            variable="furHatMediator.latestResponse", value="yes", operator=operator.contains
        ),
        )
        
        guessingIteration.add_child(isAnswerCorrect)
        
        action4 = furHatSays(name="furHatSays", message="we are back boys")
        
        tryAskingForCelebIteration = py_trees.composites.Sequence(name="Guessing Iteration: {i}", memory=True)
        reqLLM2 = askChatGPT(name="idk man", messageToLLM="Based on these answers and the current statistics, make your best guess of who the celebrity is. Only provide the name.")
        
        execLLM2 = chatGPTToFurhat(name="chatGPTToFurhat")
        listenPlayer2 = furHatListens(name="furHatListens")
        
        tryAskingForCelebIteration.add_child(reqLLM2)
        tryAskingForCelebIteration.add_child(execLLM2)
        tryAskingForCelebIteration.add_child(listenPlayer2)
        tryAskingForCelebIteration.add_child(action4)
        
        
        isAnswerCorrect2 = py_trees.behaviours.CheckBlackboardVariableValue(
        name="Check for YES/NO 2",
        check=py_trees.common.ComparisonExpression(
            variable="furHatMediator.latestResponse", value="yes", operator=operator.eq
        ),
        )
        
        tryAskingForCelebIteration.add_child(isAnswerCorrect2)
        
        action2 = furHatSays(name="furHatSays", message="seems i found them")
        tryAskingForCelebIteration.add_child(action2)
        
        guessingIteration.add_child(tryAskingForCelebIteration)
                
        root.add_child(guessingIteration)

    return root


##############################################################################
# Main
##############################################################################

wGameState = py_trees.blackboard.Client(name="Writer")
wGameState.register_key(key="gameState", access=py_trees.common.Access.WRITE)
rGameState = py_trees.blackboard.Client(name="Reader")
rGameState.register_key(key="gameState", access=py_trees.common.Access.READ)

wfurHatMediator = py_trees.blackboard.Client(name="Writer")
wfurHatMediator.register_key(key="furHatMediator", access=py_trees.common.Access.WRITE)
rfurHatMediator = py_trees.blackboard.Client(name="Reader")
rfurHatMediator.register_key(key="furHatMediator", access=py_trees.common.Access.READ)


def main() -> None:
    """Entry point for the demo script."""
    py_trees.logging.level = py_trees.logging.Level.DEBUG
    py_trees.blackboard.Blackboard.enable_activity_stream(maximum_size=100)

    wGameState.gameState = GameState()
    wfurHatMediator.furHatMediator = furHatMediator()

    root = create_root()

    ####################
    # Execute
    ####################
    root.setup_with_descendants()
    unset_blackboard = py_trees.blackboard.Client(name="Unsetter")
    unset_blackboard.register_key(key="foo", access=py_trees.common.Access.WRITE)
    print("\n--------- Tick 0 ---------\n")
    root.tick_once()
    print("\n")
    print(py_trees.display.unicode_tree(root, show_status=True))
    print("--------------------------\n")
    print(py_trees.display.unicode_blackboard())
    print("--------------------------\n")
    print(py_trees.display.unicode_blackboard(display_only_key_metadata=True))
    print("--------------------------\n")
    unset_blackboard.unset("foo")
    print(py_trees.display.unicode_blackboard_activity_stream())
    
main()