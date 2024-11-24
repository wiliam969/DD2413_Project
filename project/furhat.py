from furhat_remote_api import FurhatRemoteAPI
import os 
import json

# Create an instance of the FurhatRemoteAPI class, providing the address of the robot or the SDK running the virtual robot
furhat = FurhatRemoteAPI("192.168.1.114")
#furhat = FurhatRemoteAPI("localhost")

# Get the voices on the robot
voices = furhat.get_voices()

# Set the voice of the robot
furhat.set_voice(name='Matthew')

# Say "Hi there!"
furhat.say(text="Hi there!")

# Play an audio file (with lipsync automatically added) 
furhat.say(url="https://www2.cs.uic.edu/~i101/SoundFiles/gettysburg10.wav", lipsync=True)

# Listen to user speech and return ASR result
result = furhat.listen()

s = ""

with open("gestures/test1.json") as f:
    s = f.read()

s = json.loads(s)

# Perform a custom gesture
furhat.gesture(body=s)