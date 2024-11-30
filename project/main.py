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
CelebAsssitant = client.beta.assistants.retrieve("asst_pGFByUcST71ndbhfFWg07OdB")
ObjectAsssitant = client.beta.assistants.retrieve("asst_nPsAYTI77WwJG8XK7Zh4muRu")

furhat = FurhatRemoteAPI("localhost")
thread = client.beta.threads.create()

##############################################################################
# Classes
##############################################################################

def retrieveQuestionAndEmotion(text: str) -> str:
    pattern = r"<express\([^)]*\)>"
    cleanedQuestion = re.sub(pattern, "", text).strip()
    
    matches = re.findall(pattern, text)
    pattern = r"<[^>]*>"  # Matches any text within < >
    
    if matches: 
        question = text.replace(matches[0], "")
        idx1 =  matches[0].index("(")
        idx2 =  matches[0].index(")")
        expression =  matches[0][idx1 + len("("): idx2]
        
        return question, expression 
    
    return text, ""

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
        self.sendMessageToFurhat = ""
        self.sendGestureToFurhat = ""

class furHatSays(py_trees.behaviour.Behaviour):

    def __init__(self, name, message = ""):
        super().__init__(name=name)
        self.message = message

    def update(self):
        rGameState.gameState.totalNumberOfInteraction += 1

        if self.message == "":
            self.message = rfurHatMediator.furHatMediator.sendMessageToFurhat

        if self.message != "":
            furhat.say(text=self.message)

            print("[furHat said]: " + self.message)
        
        self.message = ""
        
        return py_trees.common.Status.SUCCESS
    
class furHatAsks(py_trees.behaviour.Behaviour):

    def __init__(self, name):
        super().__init__(name=name)

    def update(self):
        wGameState.gameState.totalNumberOfInteraction += 1

        furHatResponse = furhat.ask(text=rfurHatMediator.furHatMediator.sendMessageToFurhat)

        print ("Listenning...")
        
        if furHatResponse.message == "":
            return py_trees.common.Status.FAILURE 
         
        wfurHatMediator.furHatMediator.latestResponse = furHatResponse.message.strip().lower()
        print("[furHat heard]: " + furHatResponse.message)
        
        return py_trees.common.Status.SUCCESS

class furHatListens(py_trees.behaviour.Behaviour):

    def __init__(self, name):
        super().__init__(name=name)

    def update(self):
        wGameState.gameState.totalNumberOfInteraction += 1
        
        furHatResponse = furhat.listen()
        print ("Listenning...")
        
        if furHatResponse.message == "":
            return py_trees.common.Status.FAILURE 
         
        wfurHatMediator.furHatMediator.latestResponse = furHatResponse.message.strip().lower()
        print("[furHat heard]: " + furHatResponse.message)
        
        return py_trees.common.Status.SUCCESS

class updateAndRetrieveAssistantsQuestion(py_trees.behaviour.Behaviour):

    def __init__(self, name, messageToLLM):
        super().__init__(name=name)
        self.messageToLLM = messageToLLM
    
    def update(self):        
        
        concatenatedMessage = f"{self.messageToLLM} The following represents all questions you asked before: {rGameState.gameState.questionHistory}. The following represents all answers the human has given prior: {rGameState.gameState.answerHistory}"
        
        file = client.files.create(
            file=open("C:\src\obj-detection\objects.json", "rb"),
            purpose='assistants'
        )
        
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="assistant",
            content=concatenatedMessage,
            attachments = [
                {
                "file_id": file.id,
                "tools": [{"type": "file_search"}]
                }
            ]
        )
        
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=CelebAsssitant.id,
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
        
        cleanedQuestion, emotion =retrieveQuestionAndEmotion(question)

        wGameState.gameState.questionHistory.append(cleanedQuestion)
        
        wfurHatMediator.furHatMediator.sendMessageToFurhat = cleanedQuestion
        wfurHatMediator.furHatMediator.sendGestureToFurhat = emotion
        
        print(f"[Chat-GPT said]: {cleanedQuestion}")
        
        return py_trees.common.Status.SUCCESS

class sendPlayerResponseToLLM(py_trees.behaviour.Behaviour):

    def __init__(self, name):
        super().__init__(name=name)

    def update(self):        
                
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=rfurHatMediator.furHatMediator.latestResponse,
        )
        
        # Update the blackboard and game state
        wGameState.gameState.answerHistory.append(rfurHatMediator.furHatMediator.latestResponse)

        return py_trees.common.Status.SUCCESS

class triggerAssistantMessage(py_trees.behaviour.Behaviour):

    def __init__(self, name, messageToLLM):
        super().__init__(name=name)
        self.messageToLLM = messageToLLM
        
    def update(self):        
                
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=self.messageToLLM,
        )
        
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=CelebAsssitant.id,
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
        
        cleaned_content, emotion = retrieveQuestionAndEmotion(content)

        wfurHatMediator.furhatMediator.sendMessageToFurhat = cleaned_content
        wfurHatMediator.furHatMediator.sendGestureToFurhat = emotion

        print(f"[Chat-GPT said]: {cleaned_content}")

        return py_trees.common.Status.SUCCESS

class getCurrentObjects(py_trees.behaviour.Behaviour):

    def __init__(self, name):
        super().__init__(name=name)
        

    def update(self):        
        
        with open ("C:\src\obj-detection\objects.json", "r") as ObjectFiles: 
            csvObjList = ObjectFiles.read() 

        latestResponse = rfurHatMediator.furHatMediator.latestResponse

        wGameState.gameState.answerHistory.append(latestResponse)
        
        return py_trees.common.Status.SUCCESS
    
class updateQuestionsAsked(py_trees.behaviour.Behaviour):

    def __init__(self, name):
        super().__init__(name=name)

    def update(self):        
        
        wGameState.gameState.totalNumberofQuestionsAsked += 1
        
        return py_trees.common.Status.SUCCESS

def guessCelebrity() -> py_trees.behaviour.Behaviour:
        
    tryAskingForCelebIteration = py_trees.composites.Sequence(name="Guess Celebrity: {i}", memory=True)
            
    reqLLM = triggerAssistantMessage(name="Send Message to LLM", messageToLLM="Based on these answers and the current statistics, make your best guess of who the celebrity is. Only provide the name.")
    
    fSays = furHatSays(name="chatGPTToFurhat")
    listenPlayer = furHatListens(name="furHatListens")
        
    tryAskingForCelebIteration.add_child(reqLLM)
    tryAskingForCelebIteration.add_child(fSays)
    tryAskingForCelebIteration.add_child(listenPlayer)
        
    furHatWon = furHatSays(name="furHatSays", message="seems i found them")
    tryAskingForCelebIteration.add_child(furHatWon)
    
    return tryAskingForCelebIteration

def startGuessingRound() -> py_trees.behaviour.Behaviour:
       
    guessingIteration = py_trees.composites.Sequence(name="Guessing Iteration", memory=True)
    
    reqLLM = updateAndRetrieveAssistantsQuestion(name="Ask LLM a Question...", messageToLLM="The following is a history of previous questions and answers/responses from the player. Based on the size of the array you know how many questions and answers were being asked already;")
    fSays = furHatSays(name="chatGPTToFurhat")
    fListens = furHatListens(name="furHatListens")
    
    updateQuestionCounter = updateQuestionsAsked(name="QuestionCounter")
    
    guessingIteration.add_child(reqLLM)
    guessingIteration.add_child(updateQuestionCounter)
    
    repeadOnFailure = py_trees.decorators.Retry("repeat listening process on failure", fListens, 10)
    
    para_listen_speech = py_trees.composites.Parallel(
        name="Parallising of listening and speeching",
        policy=py_trees.common.ParallelPolicy.SuccessOnAll(),
    )
    
    para_listen_speech.add_child(fSays)
    para_listen_speech.add_child(repeadOnFailure)        
    guessingIteration.add_child(para_listen_speech)
    
    playersAnswer = sendPlayerResponseToLLM(name="Sending the Answer of the Player to LLM")
    
    guessingIteration.add_child(playersAnswer) 
        
    return guessingIteration
        
def create_root() -> py_trees.behaviour.Behaviour:
    """
    Create the root behaviour and it's subtree.

    Returns:
        the root behaviour
    """
    root = py_trees.composites.Sequence(name="Complete Tree", memory=True)
    
    welcomeRoutine = py_trees.composites.Sequence(name="Warming Up", memory=True)

    action1 = furHatSays(name="Think of a celeb", message=f"Think  of a celebrity and I will try to guess who it is")
    action2 = furHatSays(name="furHatSays", message="Please answer my questions with yes or no")
    
    welcomeRoutine.add_child(action1)
    welcomeRoutine.add_child(action2)
    welcome = py_trees.idioms.oneshot(welcomeRoutine, "oneShot Welcome")
    
    root.add_children(
        [
            welcome
        ]
    )
    
    guessingRound = startGuessingRound()    
    celebrity = guessCelebrity() 
    
    # After how many guesses should furhat guess the object
    isTotalNumberofQuestionsAskedReached = py_trees.idioms.either_or(
        name="If Guess <= 2 then guessing round else celebrity",
        conditions=[
            py_trees.common.ComparisonExpression(
            variable="gameState.totalNumberofQuestionsAsked", value=2, operator=operator.le
        ),
            py_trees.common.ComparisonExpression(
            variable="gameState.totalNumberofQuestionsAsked", value=2, operator=operator.gt
        )],
    subtrees=[guessingRound, celebrity]
    )
    
    root.add_child(isTotalNumberofQuestionsAskedReached)

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
            print(py_trees.display.unicode_tree(root, show_status=True))
            
            print("\n")
            print("--------------------------\n")
            print(py_trees.display.unicode_blackboard())
            print("--------------------------\n")
            print(py_trees.display.unicode_blackboard(display_only_key_metadata=True))
            print("--------------------------\n")
            print(py_trees.display.unicode_blackboard_activity_stream())
            
            i += 1
            # if args.interactive:
            #     py_trees.console.read_single_keypress()
            # else:
            #     time.sleep(0.5)
        except KeyboardInterrupt:
            break
    
main()