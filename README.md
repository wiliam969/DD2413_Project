# Main Programm 

the main programm can be found under /project/main.py. Here, the main function, classes and the tree is defined. 
In theory this could (and should) be distributed into different files, also to enhance the readability. But due to time constraints, the refactoring process was delayed. 

## General description of the program
1. Import required libraries and modules.
2. Load environment variables for API keys.
3. Initialize APIs and assistants for interaction (FurhatRemoteAPI and OpenAI).

4. Define global variables:
   - Current assistant
   - Thread for communication
   - Running state

5. Define *Classes*:
   - retrievedObject:
     - Stores questions, expressions, and game status.
   - GameState:
     - Tracks game details such as scores, interaction counts, and history.
   - furHatMediator:
     - Handles communication between the robot and the system.
   - Several py_trees.behaviour classes for different tasks:
     - updAttendance: Updates user attendance.
     - furHatSays: Makes the robot speak.
     - furHatAsks: Makes the robot ask a question.
     - furHatListens: Makes the robot listen to responses.
     - setupGame: Initializes game settings based on user input.
     - closeGame: Ends the game.
     - isGameWonNode: Checks if the game is won.
     - furHatExpressEmotions: Makes the robot show emotions.
     - updateAndRetrieveAssistantsQuestion: Interacts with OpenAI to get questions.
     - sendPlayerResponseToLLM: Sends player responses to the assistant.
     - triggerAssistantMessage: Sends messages and retrieves responses.
     - updateQuestionsAsked: Keeps track of question count.
     - finishGameIntro: Marks game introduction as complete.

6. Define *Game Behaviors*:
   - makeLastGuess():
     - Attempts the final guess based on collected answers.
     - Checks if the game is won or lost and ends accordingly.
   - startGuessingRound():
     - Handles rounds of guessing.
     - Updates question counters and expressions based on interactions.
   - startCelebrityGuessingGame():
     - Manages a celebrity guessing game.
     - Introduces the game and switches between rounds or guessing attempts.
   - startObjectDetectionGame():
     - Manages an object detection guessing game with similar logic to the celebrity game.

7. Define *Tree Construction*:
   - create_root():
     - Builds a behavior tree that organizes tasks.
     - Adds nodes for attendance, welcome messages, game setup, and game selection.

8. Main Program:
   - Initialize blackboard variables for shared state tracking.
   - Create root behavior tree.
   - Set up and execute the tree with a loop until the game ends or interrupted.
   - Print debug information about tree status and activity logs after each tick.

9. Start main() to execute the program.

## dependencies 

The following libraries are required to run the program: 

- operator
- py_trees
- os
- openai 
- furhat_remote_api
- time
- dotenv
- datetime 
- re

## How to start: 

the program can be started using python3. You dont need to pass any parameters: 

python main.py
