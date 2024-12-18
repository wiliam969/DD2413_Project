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
from threading import Thread
#from object_detection import objDetection

load_dotenv()

#furhat = FurhatRemoteAPI(os.getenv('FURHAT_IP'))
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
#CelebAsssitant = client.beta.assistants.retrieve("asst_pGFByUcST71ndbhfFWg07OdB") # WITH SSML 
CelebAsssitant = client.beta.assistants.retrieve("asst_vDh0qD69O3lJT5MAek39fhZY") # BAREBONE

ObjectAsssitant = client.beta.assistants.retrieve("asst_nPsAYTI77WwJG8XK7Zh4muRu")

currentAssistant = None

furhat = FurhatRemoteAPI("localhost")
thread = client.beta.threads.create()

running = True

##############################################################################
# Classes
##############################################################################

class retrievedObject: 
    def __init__(self, question, expression = "", isGameWon = False):
        self.question = question 
        self.expression = expression 
        self.isGameWon = isGameWon 

def retrieveQuestionAndActionFunctions(text: str) -> retrievedObject:
    pattern = r"<express\([^)]*\)>"
    
    matches = re.findall(pattern, text)
    pattern = r"<[^>]*>"  # Matches any text within < >
    
    question = text
    expression = ""
    if matches: 
        question = text.replace(matches[0], "")
        idx1 =  matches[0].index("(")
        idx2 =  matches[0].index(")")
        expression =  matches[0][idx1 + len("("): idx2]
        
    pattern = r"<game\([^)]*\)>"    
    matches = re.findall(pattern, text)
    pattern = r"<[^>]*>"  # Matches any text within < >
    
    isGameAlreadyWon = False
    if matches: 
        question = text.replace(matches[0], "")
        idx1 =  matches[0].index("(")
        idx2 =  matches[0].index(")")
        GameWonString =  matches[0][idx1 + len("("): idx2]
        
        if "WON" in GameWonString:
            isGameAlreadyWon = True
        else: 
            isGameAlreadyWon = False
    
    returnObject = retrievedObject(question, expression, isGameAlreadyWon)
    
    return returnObject

class GameState(object):
    def __init__(self):
        self.gameName = ""
        self.isGameWon = False
        self.gameIntroFinished = False
        self.totalNumberofQuestionsAsked = 0
        self.totalNumberofCorrectGuesses = 0        
        self.totalNumberofWrongGuesses = 0        
        self.previousAnswers = ""
        self.lastEmotionalStateAccess = None
        self.totalNumberOfInteraction = 0
        self.questionHistory = []
        self.answerHistory = []
        self.robotFacialExpressionHistory = []
        
        
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

class updAttendance(py_trees.behaviour.Behaviour): 
    def __init__(self, name, message = ""):
        super().__init__(name=name)
        self.message = message

    def update(self):
        users = furhat.get_users()
        
        if users:
            furhat.attend(userid=users[0].id)
                
        return py_trees.common.Status.SUCCESS

class furHatSays(py_trees.behaviour.Behaviour):

    def __init__(self, name, message = ""):
        super().__init__(name=name)
        self.message = message

    def update(self):
        rGameState.gameState.totalNumberOfInteraction += 1

        if self.message == "":
            self.message = rfurHatMediator.furHatMediator.sendMessageToFurhat

        if self.message != "":
            furhat.say(text=self.message, blocking=True)

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

# class updateAttendance(py_trees.behaviour.Behaviour):
#     def __init__(self, name):
#         super().__init__(name=name)

#     def update(self):
#         users = furhat.get_users()
        
#         if users: 
#             furhat.attend(userid=users[0].id)


class setupGame(py_trees.behaviour.Behaviour):

    def __init__(self, name):
        super().__init__(name=name)

    def update(self):
        global currentAssistant
        # rfurHatMediator.furHatMediator.latestResponse."object" 
        
        if "celebrity" in rfurHatMediator.furHatMediator.latestResponse.lower():
            wGameState.gameState.gameName = "celebrity"
            currentAssistant = CelebAsssitant
            return py_trees.common.Status.SUCCESS
        elif "object" in rfurHatMediator.furHatMediator.latestResponse.lower():
            wGameState.gameState.gameName = "object"
            currentAssistant = ObjectAsssitant
            return py_trees.common.Status.SUCCESS
        
        return py_trees.common.Status.FAILURE
                
                
class closeGame(py_trees.behaviour.Behaviour):

    def __init__(self, name):
        super().__init__(name=name)

    def update(self):
        global running
        running = False
        return py_trees.common.Status.SUCCESS


class isGameWonNode(py_trees.behaviour.Behaviour):

    def __init__(self, name):
        super().__init__(name=name)

    def update(self):
        global currentAssistant
        # rfurHatMediator.furHatMediator.latestResponse."object" 
        
        if "yes" in rfurHatMediator.furHatMediator.latestResponse.lower():
            wGameState.gameState.isGameWon = True
            return py_trees.common.Status.SUCCESS
        elif "no" in rfurHatMediator.furHatMediator.latestResponse.lower():
            wGameState.gameState.isGameWon = False
            return py_trees.common.Status.SUCCESS
        
        return py_trees.common.Status.FAILURE
    
class furHatExpressEmotions(py_trees.behaviour.Behaviour):

    def __init__(self, name, emotion = ""):
        super().__init__(name=name)
        self.emotion = emotion

    def update(self):
        wGameState.gameState.totalNumberOfInteraction += 1
        
        if self.emotion == "":
            self.emotion = rfurHatMediator.furHatMediator.sendGestureToFurhat
            
        if self.emotion != "":
            furhat.gesture(name=self.emotion)
        
        self.emotion = ""
        
        return py_trees.common.Status.SUCCESS

class updateAndRetrieveAssistantsQuestion(py_trees.behaviour.Behaviour):

    def __init__(self, name, messageToLLM):
        super().__init__(name=name)
        self.messageToLLM = messageToLLM
    
    def update(self):        
        
        concatenatedMessage = f"{self.messageToLLM} The following represents all questions you asked before: {rGameState.gameState.questionHistory}. The following represents all answers the human has given prior: {rGameState.gameState.answerHistory}"
        
        if currentAssistant == CelebAsssitant: 
            message = client.beta.threads.messages.create(
                thread_id=thread.id,
                role="assistant",
                content=concatenatedMessage,
            )
        else: 
            file = client.files.create(
                file=open("objects.json", "rb"),
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
            assistant_id=currentAssistant.id,
        )

        def wait_on_run(run, thread):
            while run.status == "queued" or run.status == "in_progress":
                run = client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id,
                )
            return run

        run = wait_on_run(run, thread)

        response = client.beta.threads.messages.list(thread_id=thread.id)
        
        question = response.data[0].content[0].text.value
        
        preppedObject = retrieveQuestionAndActionFunctions(question)

        wGameState.gameState.questionHistory.append(preppedObject.question)
        
        wfurHatMediator.furHatMediator.sendMessageToFurhat = preppedObject.question
        wfurHatMediator.furHatMediator.sendGestureToFurhat = preppedObject.expression
        
        wGameState.gameState.isGameWon = preppedObject.isGameWon
        
        print(f"[Chat-GPT said]: {preppedObject.question}")
        
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
            assistant_id=currentAssistant.id,
        )

        def wait_on_run(run, thread):
            while run.status == "queued" or run.status == "in_progress":
                run = client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id,
                )
            return run

        run = wait_on_run(run, thread)

        response = client.beta.threads.messages.list(thread_id=thread.id)
        
        content = response.data[0].content[0].text.value
        
        # Clean up the response - remove any extra spaces, newlines, or punctuation at the end
        content = content.strip('?.!').strip()
        
        preppedObject = retrieveQuestionAndActionFunctions(content)

        wfurHatMediator.furHatMediator.sendMessageToFurhat = preppedObject.question
        wfurHatMediator.furHatMediator.sendGestureToFurhat = preppedObject.expression

        wGameState.gameState.isGameWon = preppedObject.isGameWon

        print(f"[Chat-GPT said]: {preppedObject.question}")

        return py_trees.common.Status.SUCCESS

class getCurrentObjects(py_trees.behaviour.Behaviour):

    def __init__(self, name):
        super().__init__(name=name)
        

    def update(self):        
        
        with open ("objects.json", "r") as ObjectFiles: 
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

class finishGameIntro(py_trees.behaviour.Behaviour):
    def __init__(self, name):
        super().__init__(name=name)

    def update(self):        
        wGameState.gameState.gameIntroFinished = True
        return py_trees.common.Status.SUCCESS

def makeLastGuess() -> py_trees.behaviour.Behaviour:
        
    tryAskingForCelebIteration = py_trees.composites.Sequence(name="Guess Celebrity: {i}", memory=True)
            
    reqLLM = triggerAssistantMessage(name="Trying to Guess...", messageToLLM="Based on these answers and the current statistics, make your best guess of who the celebrity is. Only provide the name.")
    
    wonORLost = furHatSays(name="won or lost")
    getLastResponse = furHatListens(name="last response :(")
    triggerGameWon = isGameWonNode(name="fu")
    

    
    gameWonSequence = py_trees.composites.Sequence(name="gameWonSequence", memory=False)
    gameWonMessage = furHatSays(name="present yourself boy", message="Yeah I won :D")
    gameWonSequence.add_child(gameWonMessage)
    gameWonSequence.add_child(closeGame(name="Close the Game"))
    
    gameLostSequence = py_trees.composites.Sequence(name="gameLostSequence", memory=False)
    gameLostMessage = furHatSays(name="furHatSays", message="Seems that i didnt have a Chance. I lost")
    gameLostSequence.add_child(gameLostMessage)
    gameLostSequence.add_child(closeGame(name="Close the Game"))
    
    # After how many guesses should furhat guess the object
    isGameWon = py_trees.idioms.either_or(
        name="Check whether we already Won the Game",
        conditions=[
            py_trees.common.ComparisonExpression(
            variable="gameState.isGameWon", value=True, operator=operator.eq
        ),
            py_trees.common.ComparisonExpression(
            variable="gameState.isGameWon", value=False, operator=operator.eq
        )],
    subtrees=[gameWonSequence, gameLostSequence]
    )
    
    tryAskingForCelebIteration.add_child(reqLLM)
    tryAskingForCelebIteration.add_child(wonORLost)
    tryAskingForCelebIteration.add_child(getLastResponse)
    tryAskingForCelebIteration.add_child(triggerGameWon)
    
    tryAskingForCelebIteration.add_child(isGameWon)
        
    return tryAskingForCelebIteration

def startGuessingRound() -> py_trees.behaviour.Behaviour:
       
    guessingIteration = py_trees.composites.Sequence(name="Guessing Iteration", memory=True)
    updateQuestionCounter = updateQuestionsAsked(name="QuestionCounter")
    
    fThinking = furHatExpressEmotions(name="furhat ExpressEmotion", emotion="Roll")
    reqLLM = updateAndRetrieveAssistantsQuestion(name="Ask LLM a Question...", messageToLLM="The following is a history of previous questions and answers/responses from the player. Based on the size of the array you know how many questions and answers were being asked already;")

    fSays = furHatSays(name="chatGPTToFurhat")
    fListens = furHatListens(name="furHatListens")
    
    repeadOnFailure = py_trees.decorators.Retry("repeat listening process on failure", fListens, 10)  
    
    playersAnswer = sendPlayerResponseToLLM(name="Sending the Answer of the Player to LLM")
    fExpression = furHatExpressEmotions(name="furhat ExpressEmotion")
    
    guessingIteration.add_children(
        [
            fThinking,
            reqLLM,
            updateQuestionCounter,
            fSays,
            repeadOnFailure,
            playersAnswer,
            fExpression
        ]
    )
        
    return guessingIteration
        
def startCelebrityGuessingGame() -> py_trees.behaviour.Behaviour:
    
    celebRootTree = py_trees.composites.Sequence(name="Celebrity - Root - Tree", memory=True)
    
    gameIntro = py_trees.composites.Sequence(name="How do we play the game?", memory=False)

    sdsdfdsfsfd = furHatSays(name="think about a celebrity", message="Now, please think of a celebrity and I will try to guess who it is.")
    welcomeMessasdfdsfge1 = furHatSays(name="Please answer the Questions", message="We are playing 10 rounds, if i cant guess it until the last round i will loose the game")
    
    gameIntro.add_child(sdsdfdsfsfd)
    gameIntro.add_child(welcomeMessasdfdsfge1)
    gameIntro.add_child(finishGameIntro(name="finishGameIntro"))
    
    guessingRound = startGuessingRound()    
    celebrity = makeLastGuess() 
    # Should we start the Intro or directly go into the game    
    isTotalNumberofQuestionsAskedReached = py_trees.idioms.either_or(
        name="If Guess <= 07 then guessing round else celebrity",
        conditions=[
            py_trees.common.ComparisonExpression(
            variable="gameState.totalNumberofQuestionsAsked", value=10, operator=operator.le
        ),
            py_trees.common.ComparisonExpression(
            variable="gameState.totalNumberofQuestionsAsked", value=10, operator=operator.gt
        )],
    subtrees=[guessingRound, celebrity]
    )
    
    # After how many guesses should furhat guess the object
    gameIntroFinished = py_trees.idioms.either_or(
        name="Should we start the Game ",
        conditions=[
            py_trees.common.ComparisonExpression(
            variable="gameState.gameIntroFinished", value=False, operator=operator.eq
        ),
            py_trees.common.ComparisonExpression(
            variable="gameState.gameIntroFinished", value=True, operator=operator.eq
        )],
    subtrees=[gameIntro, isTotalNumberofQuestionsAskedReached]
    )    

    celebRootTree.add_children(
        [
            gameIntroFinished
        ]
    )
    
    return celebRootTree
    
def startObjectDetectionGame() -> py_trees.behaviour.Behaviour:
    
    ObjectRootTree = py_trees.composites.Sequence(name="Object - Root - Tree", memory=True)
    
    gameIntro = py_trees.composites.Sequence(name="How do we play the game?", memory=False)

    gameIntro1 = furHatSays(name="think about a celebrity", message="Think of an object infront of you and i will try to guess which it is.  ")
    gameIntro2 = furHatSays(name="Please answer the Questions", message="We are playing 4 rounds, if i cant guess it until the last round i will loose the game")
    
    gameIntro.add_child(gameIntro1)
    gameIntro.add_child(gameIntro2)
    gameIntro.add_child(finishGameIntro(name="finishGameIntro"))
    
    guessingRound = startGuessingRound()    
    celebrity = makeLastGuess() 
    # Should we start the Intro or directly go into the game    
    isTotalNumberofQuestionsAskedReached = py_trees.idioms.either_or(
        name="If Guess <= 04 then guessing round else celebrity",
        conditions=[
            py_trees.common.ComparisonExpression(
            variable="gameState.totalNumberofQuestionsAsked", value=5, operator=operator.le
        ),
            py_trees.common.ComparisonExpression(
            variable="gameState.totalNumberofQuestionsAsked", value=5, operator=operator.gt
        )],
    subtrees=[guessingRound, celebrity]
    )
    
    # After how many guesses should furhat guess the object
    gameIntroFinished = py_trees.idioms.either_or(
        name="Check whether we already Won the Game",
        conditions=[
            py_trees.common.ComparisonExpression(
            variable="gameState.gameIntroFinished", value=False, operator=operator.eq
        ),
            py_trees.common.ComparisonExpression(
            variable="gameState.gameIntroFinished", value=True, operator=operator.eq
        )],
    subtrees=[gameIntro, isTotalNumberofQuestionsAskedReached]
    )    

    ObjectRootTree.add_children(
        [
            gameIntroFinished
        ]
    )
    
    return ObjectRootTree
    
def create_root() -> py_trees.behaviour.Behaviour:
    """
    Create the root behaviour and it's subtree.

    Returns:
        the root behaviour
    """
    root = py_trees.composites.Sequence(name="Complete Tree", memory=True)
    
    attendance = updAttendance(name="update attendance")
    
    root.add_child(attendance)
    
    welcomeRoutine = py_trees.composites.Sequence(name="Thats not Warming up but rather stuff like presenting or something ", memory=True)

    welcomeMessage1 = furHatSays(name="present yourself boy", message="Hello My Name is Furhat I am a Robot.")
    welcomeMessage2 = furHatSays(name="furHatSays", message="Lets play a Guessing Game where I will try to guess a celebrity you are thinking about. Please say Celebrity to start the game.")
    
    welcomeRoutine.add_child(welcomeMessage1)
    welcomeRoutine.add_child(welcomeMessage2)
    
    getTheGame = py_trees.composites.Sequence(name="Complete Tree", memory=True)
    listenToFurhat = furHatListens(name="Get the Game")
    settingTheGame = setupGame(name="Setting the Game for the entire Session")
    getTheGame.add_child(listenToFurhat)
    getTheGame.add_child(settingTheGame)
    
    repeadOnFailure = py_trees.decorators.Retry("repeat listening process on failure", getTheGame, 10)
    welcomeRoutine.add_child(repeadOnFailure)
        
    oneShotWelcomeRoutine = py_trees.idioms.oneshot(welcomeRoutine, "oneShot Welcome")
    
    root.add_child(oneShotWelcomeRoutine)
    
    celebrityGame = startCelebrityGuessingGame()
    #root.add_child(celebrityGame)
    
    objectGame = startObjectDetectionGame() 
    
    # After how many guesses should furhat guess the object
    whichGameToChoose = py_trees.idioms.either_or(
        name="Which Game are we going to play?",
        conditions=[
            py_trees.common.ComparisonExpression(
            variable="gameState.gameName", value="celebrity", operator=operator.eq
        ),
            py_trees.common.ComparisonExpression(
            variable="gameState.gameName", value="object", operator=operator.eq
        )],
        subtrees=[celebrityGame, objectGame]
    )
    
    root.add_child(whichGameToChoose)
    
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

# thread = Thread(target = objDetection)
# thread.start()

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
    
    i = 0
    
    while running:
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
            
            # time.sleep(10)
            print(f"\n--------- END-TICK {i} ---------\n")
            i += 1
            # if args.interactive:
            #     py_trees.console.read_single_keypress()
        except KeyboardInterrupt:
            break
    
    # thread.join()
    
main()