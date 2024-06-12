import boto3
import sounddevice as sd
import numpy as np
import time
import datetime
from scipy.io.wavfile import write
import requests
import os
import json
from openai import OpenAI

aws_access_key_id = ""#Please enter your key.
aws_secret_access_key = ""#Please enter your key.
aws_region_name = "us-west-2"
openai_api_key = ""#Please enter your key.
voice_id = "Ivy"

examples = """User input: I have 1235 candies.
Finish[no]

---

User input: 4593 is my favorite number.
Finish[no]

---

User input: I want to go to room 5732.
Finish[5732]

---

User input: I want to go to room 3219.
Finish[3219]

---

User input: Do you know where is room 3216?
Finish[3216]

---

User input: Room 3492 is cool.
Finish[no]
"""

room_numbers = """- 3219
- 3154
- 3216
"""

suffix_a = "Does the user's input specify navigating to a room? Answer with yes (and specify the room number like Finish[3154]) or no."
suffix_a_prompt = """You will be provided some user input possibly about navigating to a room number.
The available room numbers are:
{room_numbers}

Here are some examples:
{examples}
(END OF EXAMPLES)

User input: {user_input}

Question: {suffix_a}"""

def get_room_number(user_input: str) -> str:
    client = OpenAI(
        api_key=openai_api_key
    )
    
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": suffix_a_prompt.format(room_numbers=room_numbers, examples=examples, user_input=user_input, suffix_a=suffix_a)
            }
        ],
        model="gpt-3.5-turbo"
    )
    answer = chat_completion.choices[0].message.content
    answer = answer.split("Finish[")[-1].split("]")[0]
    
    return answer
    
output_file_path = "speech_output.mp3"
    
def synthesize_speech(text: str) -> None:
    aws_session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_region_name,
    )
    
    polly_client = aws_session.client("polly")
    response = polly_client.synthesize_speech(
        Text=text, OutputFormat="mp3", VoiceId=voice_id
    )
    
    with open(output_file_path, "wb") as f:
        f.write(response["AudioStream"].read())
        
    os.system("mpv" + " " + output_file_path)
    
    
if __name__ == "__main__":
    possible_room_numbers = [3219, 3154, 3216]

    user_input = "Take me to room 3219 please."
    
    # Ask LLM to parse user intent.
    room_number = get_room_number(user_input)
    print(room_number)
    
    # Convert room number to int.
    try:
        room_number = int(room_number)
    except:
        room_number = 0
        
    # Generate response.
    if room_number not in possible_room_numbers:
        response = f"Invalid input. Available rooms are {', '.join(str(x) for x in possible_room_numbers)}. If you specified an available room number and received this response, please try again."
    else:
        response = f"Great! I'll take you to room {room_number}."
        
    print(response)
    
    synthesize_speech(response)
