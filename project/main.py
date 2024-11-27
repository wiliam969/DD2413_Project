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
assistant = client.beta.assistants.retrieve("asst_pGFByUcST71ndbhfFWg07OdB")
furhat = FurhatRemoteAPI("localhost")
thread = client.beta.threads.create()
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
        self.questionHistory = []
        self.answerHistory = []
        
        
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

class askLLMwithGameState(py_trees.behaviour.Behaviour):

    def __init__(self, name, messageToLLM):
        super().__init__(name=name)
        self.gameState = rGameState.gameState
        self.messageToLLM = messageToLLM
        self.blackboard = self.attach_blackboard_client(name="ChatGPT", namespace="ChatGPT_")
        
        self.blackboard.register_key("message", access=py_trees.common.Access.WRITE)

    def update(self):        
        
        concatenatedMessage = f"{self.messageToLLM} The following represents all questions you asked before: {self.gameState.questionHistory}. The following represents all answers the human has given prior: {self.gameState.answerHistory}"
        
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=concatenatedMessage,
        )
        
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id,
        )


        def wait_on_run(run, thread):
            while run.status == "queued" or run.status == "in_progress":
                run = client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id,
                )
                time.sleep(0.5)
            return run

        run = wait_on_run(run, thread)

        response = client.beta.threads.messages.list(thread_id=thread.id)
        
        question = response.data[0].content[0].text.value
        
        wGameState.gameState.questionHistory.append(question)
        
        self.blackboard.message = question
        print(f"[Chat-GPT said]: {question}")
        
        return py_trees.common.Status.SUCCESS

class askLLMRaw(py_trees.behaviour.Behaviour):

    def __init__(self, name, messageToLLM):
        super().__init__(name=name)
        self.gameState = rGameState.gameState
        self.messageToLLM = messageToLLM
        self.blackboard = self.attach_blackboard_client(name="ChatGPT", namespace="ChatGPT_")
        
        self.blackboard.register_key("message", access=py_trees.common.Access.WRITE)

    def update(self):        
                
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=self.messageToLLM,
        )
        
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id,
        )


        def wait_on_run(run, thread):
            while run.status == "queued" or run.status == "in_progress":
                run = client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id,
                )
                time.sleep(0.5)
            return run

        run = wait_on_run(run, thread)

        response = client.beta.threads.messages.list(thread_id=thread.id)
        
        content = response.data[0].content[0].text.value
        
        # Clean up the response - remove any extra spaces, newlines, or punctuation at the end
        content = content.strip('?.!').strip()
        
        wGameState.gameState.questionHistory.append(content)
        
        self.blackboard.message = content
        print(f"[Chat-GPT said]: {content}")
        
        return py_trees.common.Status.SUCCESS

class updateAnswerHistory(py_trees.behaviour.Behaviour):

    def __init__(self, name):
        super().__init__(name=name)

    def update(self):        
        
        latestResponse = rfurHatMediator.furHatMediator.latestResponse

        wGameState.gameState.answerHistory.append(latestResponse)
        
        return py_trees.common.Status.SUCCESS

def guessCelebrity() -> py_trees.behaviour.Behaviour:
        
    tryAskingForCelebIteration = py_trees.composites.Sequence(name="Guessing Iteration: {i}", memory=True)
    
    startAskingForCeleb = py_trees.behaviours.CheckBlackboardVariableValue(
    name="Should we already try asking for the celeb",
    check=py_trees.common.ComparisonExpression(
        variable="gameState.totalNumberOfInteraction", value=8, operator=operator.ge
    ),
    )
        
    tryAskingForCelebIteration.add_child(startAskingForCeleb)
    
    reqLLM = askLLMRaw(name="idk man", messageToLLM="Based on these answers and the current statistics, make your best guess of who the celebrity is. Only provide the name.")
    
    execLLM = chatGPTToFurhat(name="chatGPTToFurhat")
    listenPlayer = furHatListens(name="furHatListens")
    
    guessedCelebrityCorrect = py_trees.behaviours.CheckBlackboardVariableValue(
    name="Check for YES/NO",
    check=py_trees.common.ComparisonExpression(
        variable="furHatMediator.latestResponse", value="yes", operator=operator.contains
    ),
    )
    
    tryAskingForCelebIteration.add_child(reqLLM)
    tryAskingForCelebIteration.add_child(execLLM)
    tryAskingForCelebIteration.add_child(listenPlayer)
    
    tryAskingForCelebIteration.add_child(guessedCelebrityCorrect)
    
    furHatWon = furHatSays(name="furHatSays", message="seems i found them")
    tryAskingForCelebIteration.add_child(furHatWon)
    
    return tryAskingForCelebIteration

def startGuessingRound() -> py_trees.behaviour.Behaviour:
       
    guessingIteration = py_trees.composites.Sequence(name="Guessing Iteration: {i}", memory=True)
    
    reqLLM = askLLMwithGameState(name="idk man", messageToLLM="I am trying to guess a celebrity. The following is a history of previous questions and answers/responses from the player. Based on the size of the array you know how many questions and answers were being asked already;")
    execLLM = chatGPTToFurhat(name="chatGPTToFurhat")
    listenPlayer = furHatListens(name="furHatListens")
    
    wGameState.gameState.totalNumberofQuestionsAsked += 1
    
    guessingIteration.add_child(reqLLM)
    
    repeat_on_failure = py_trees.decorators.Retry("repeat listening process on failure", listenPlayer, 5)
    
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
    
    reqLLM = updateAnswerHistory(name="updateAnswerHistory")
    guessingIteration.add_child(isAnswerCorrect)
    guessingIteration.add_child(reqLLM)     
       
    celebrity = guessCelebrity() 
    guessingIteration.add_child(celebrity)
        
    return guessingIteration
        
def create_root() -> py_trees.behaviour.Behaviour:
    """
    Create the root behaviour and it's subtree.

    Returns:
        the root behaviour
    """
    root = py_trees.composites.Sequence(name="Complete Tree", memory=True)
    
    welcomeRoutine = py_trees.composites.Sequence(name="Warming Up", memory=True)
    
    action1 = furHatSays(name="furHatSays", message="Think of a celebrity and I will try to guess who it is")
    action2 = furHatSays(name="furHatSays", message="Please answer my questions with yes or no")
    
    welcomeRoutine.add_child(action1)
    welcomeRoutine.add_child(action2)
    welcome = py_trees.idioms.oneshot(welcomeRoutine, "oneShot Welcome")
    
    root.add_children(
        [
            welcome
        ]
    )
    
    isTotalNumberofQuestionsAsked = py_trees.behaviours.CheckBlackboardVariableValue(
    name="Check if totalNumberofQuestionsAsked is <= 20",
    check=py_trees.common.ComparisonExpression(
        variable="gameState.totalNumberofQuestionsAsked", value=20, operator=operator.le
    ),
    )
    
    root.add_child(isTotalNumberofQuestionsAsked)
    
    guessingRound = startGuessingRound()
                
    root.add_child(guessingRound)

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
    
    i = 0
    
    while True:
        try:
            print(f"\n--------- Tick {i} ---------\n")
            root.tick_once()
            
            i += 1
            # if args.interactive:
            #     py_trees.console.read_single_keypress()
            # else:
            #     time.sleep(0.5)
        except KeyboardInterrupt:
            break
    
    print("\n")
    print(py_trees.display.unicode_tree(root, show_status=True))
    print("--------------------------\n")
    print(py_trees.display.unicode_blackboard())
    print("--------------------------\n")
    print(py_trees.display.unicode_blackboard(display_only_key_metadata=True))
    print("--------------------------\n")
    print(py_trees.display.unicode_blackboard_activity_stream())
    
main()