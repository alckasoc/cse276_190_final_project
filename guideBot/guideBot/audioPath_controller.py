########
# Name: audioPath_controller.py
# Student: Nihal Nazeem, Vincent Tu
# Final Project
#
# Purpose: Tour guide robot with audio processing/synthesis and navigation around 3rd floor of CSE Building. This is the main controller file that consists of the code to record, process, and synthesis a response. It also includes the code to navigate.
#
# Author: Nihal Nazeem, Vincent Tu <{nnazeem, vitu}@ucsd.edu>
#
# Date: 10 May 2024
#
# How to use:
#      
#   colcon build --packages-select guideBot
#   ros2 run guideBot audioPath
#
#####################


# Our custom interface, GoPupper. This specifies the message type (commands).
from pupper_interfaces.srv import GoPupper

# Packages to let us create nodes and spin them up
import rclpy
from rclpy.node import Node

#from touch_test.py
import time
import RPi.GPIO as GPIO

# From pupper_display_test.py.
from MangDang.mini_pupper.display import Display, BehaviorState
from PIL import Image
from resizeimage import resizeimage

import os

#################################### AUDIO ####################################
import boto3
import sounddevice as sd
import numpy as np
import time
import datetime
from scipy.io.wavfile import write
import requests
import json
from openai import OpenAI
#----------------------------------- AUDIO -----------------------------------#

#Global Variables
# There are 4 areas for touch actions
# Each GPIO to each touch area
touchPin_Front = 6
touchPin_Left  = 3
touchPin_Right = 16
touchPin_Back  = 2
MAX_WIDTH = 320   # Max width of the LCD display.

#################################### AUDIO ####################################
duration = 7
sample_rate = 16000
volume_gain_multiplier = 30
aws_audio_file = "user_audio_input.flac"

aws_access_key_id = ""#Please enter your key.
aws_secret_access_key = ""#Please enter your key.
aws_region_name = "us-west-2"

bucket_name = "cse190bucket"
audio_file_key = "gpt_audio.flac" #name of audio file in S3

transcribe_job_uri = f"s3://{bucket_name}/{audio_file_key}"

openai_api_key = ""#Please enter your key.
voice_id = "Ivy"

examples = """User input: I have 1235 candies.
Finish[no]

---

User input: 4593 is my favorite number.
Finish[no]

---

User input: I want to go to room 3154.
Finish[3154]


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


instr3219  = ["stay", "turnLeft", "moveForward", "turnLeft", "moveForward", "turnRight", "moveForward", "stay"]
repNum3219 = [2,1,4,1,73,1,1,2]

instr3154  = ["stay", "turnLeft", "moveForward", "turnRight", "moveForward", "turnRight", "moveForward", "turnLeft", "moveForward", "stay"]
repNum3154 =  [2,1,4,1,35,1,30,1,2,2]

instr3216  = ["stay", "turnLeft", "moveForward", "turnLeft", "moveForward", "turnLeft", "moveForward", "stay"]
repNum3216 = [2,1,4,1,73,1,1,2]

#dictionary to cosntruct pseudo-instructions to call service
roomNum_to_pathElems = {3219 : [instr3219, repNum3219],
                        3154 : [instr3154, repNum3154],
                        3216 : [instr3216, repNum3216]
                       }

possible_room_numbers = list(roomNum_to_pathElems.keys())

room_numbers = "\n".join("- " + str(room) for room in possible_room_numbers)

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
    """Gets the room number based on transcribed user audio input.
    
    Args:
        user_input (str): The user input.
        
    Returns:
        str: A string response specifying whether the room number is valid or not.
    """
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
    """Synthesizes the text string into speech with AWS Polly.
    
    Args:
        text (str): The text to synthesize.
    """
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
#----------------------------------- AUDIO -----------------------------------#


# Use GPIO number but not PIN number
GPIO.setmode(GPIO.BCM)

# Set up GPIO numbers to input
GPIO.setup(touchPin_Front, GPIO.IN)
GPIO.setup(touchPin_Left,  GPIO.IN)
GPIO.setup(touchPin_Right, GPIO.IN)
GPIO.setup(touchPin_Back,  GPIO.IN)

# Get pupper's display.
disp = Display()

#Current working directory
cwd = "/home/ubuntu/ros2_ws/src/guideBot/guideBot/"

# Method: Sample Controller Async
# Purpose: Constructor for the controller
#
######
class SampleControllerAsync(Node):

    def __init__(self):
        # initalize
        super().__init__('sample_controller')
        self.cli = self.create_client(GoPupper, 'pup_command')

        # Check once per second if service matching the name is available.
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting again...')

        # Create a new request object.
        self.req = GoPupper.Request()

    ###
    # Name: show_expression
    # Purpose: shows the expression from an image given the file_path. The image is resized
    # and stored in new_file_path.
    # Arguments: self (reference the current class), file_path (the file path to the expression for a particular movement), new_file_path (the place where the file_path image is saved).
    # 
    ####
    def show_expression(self, file_path: str, new_file_path: str):
    	# Get pupper's display.
        imgFile = Image.open(file_path)

	# now output it (super inefficient, but it is what it is).
        imgFile.save(new_file_path, imgFile.format)

	# Display it on Pupper's LCD display.
        disp.show_image(new_file_path)
	
    ###
    # Name: send_move_request
    # Purpose: send_move_request method, send request and spin until receive response or fail
    # Arguments:  self (reference the current class), move_command (the command we plan to send to the server)
    #####
    def send_move_request(self, move_command):
        self.req = GoPupper.Request()
        self.req.command = move_command
        # Debug - uncomment if needed
        print("In send_move_request, command is: %s" % self.req.command)
        self.future = self.cli.call_async(self.req)  # send the command to the server
        rclpy.spin_until_future_complete(self, self.future)
        return self.future.result()

    ###
    # Name: pupper_touch_movement
    # Purpose: When the front sensor is touched, the robot records user input for a couple seconds and uploads to AWS S3, transcribes it, deciphers the user's intent, and synthesizes an audio response with AWS Polly. Then, if successful, the robot will navigate to the corresponding room.
    # Arguments:  self (reference the current class) -- /not sure if needed, but won't hurt/
    #####
    def pupper_touch_movement(self):
        self.show_expression(
                file_path= cwd+"img/walk.png",
                new_file_path= cwd+"img/new_walk.png"
                )
        # Detection Loop
        while True:
            touchValue_Front = GPIO.input(touchPin_Front)
            self.show_expression(
                    file_path= cwd+"img/touch4help.png",
                    new_file_path= cwd+"img/new_touch4help.png"
                    )
            print("Please pet the front of my head to get navigation help!") 
            if not touchValue_Front:
                self.show_expression(
                file_path= cwd+"img/forward.png",
                new_file_path= cwd+"img/new_forward.png"
                )
                # Step 1: Record audio.
                print("Recording...")
                self.show_expression(
                file_path= cwd+"img/recording.png",
                new_file_path= cwd+"img/new_recording.png"
                )
                audio_data = sd.rec(
                    int(duration * sample_rate), samplerate=sample_rate, channels=1
                )
                sd.wait() # Wait until recording is finished.
                print("Done recording")
                self.show_expression(
                file_path= cwd+"img/recording_done.png",
                new_file_path= cwd+"img/new_recording_done.png"
                )
                # Step 2: Save audio file locally.
                audio_data *= volume_gain_multiplier
                write(aws_audio_file, sample_rate, audio_data)
            
                # Step 3: Save local file to S3.
                aws_session = boto3.Session(
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    region_name =aws_region_name,
                )

                s3 = aws_session.client("s3")
                with open(aws_audio_file, "rb") as f:
                    s3.upload_fileobj(
                        Fileobj=f, Bucket=bucket_name, Key=audio_file_key
                    )

                # Step 4: AWS Transcribe the S3-saved audio file.
                transcribe_job_name = f'my-transcribe-job-{datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}'
                print("Transcription job name", transcribe_job_name)
            
                transcribe = aws_session.client("transcribe")
                transcribe.start_transcription_job(
                    TranscriptionJobName=transcribe_job_name,
                    LanguageCode="en-US",
                    Media={"MediaFileUri": transcribe_job_uri},
                )
            
                while True:
                    status = transcribe.get_transcription_job(
                        TranscriptionJobName=transcribe_job_name
                    )
                    if status["TranscriptionJob"]["TranscriptionJobStatus"] in [
                        "COMPLETED",
                        "FAILED"
                    ]:
                        print(status)
                        break
                    time.sleep(1)
            
                # Step 5: Get the transcription.
                if status["TranscriptionJob"]["TranscriptionJobStatus"] == "COMPLETED":
                    transcript_file_url = status["TranscriptionJob"]["Transcript"][
                        "TranscriptFileUri"
                    ]
                    response = requests.get(transcript_file_url)
                    transcript_data = json.loads(response.text)
                    transcript_text = transcript_data["results"]["transcripts"][0][
                        "transcript"
                    ]
                else:
                    transcript_text = "Invalid transcription."
                print("<=======================TRANSCRIPTION=======================>")
                print(transcript_text)
                print("<=======================TRANSCRIPTION=======================>")
                
                # Step 6: Synthesize speech response.
                    
                # Ask LLM to parse user intent.
                room_number = get_room_number(transcript_text)
                print("Room number", room_number)
                
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
                print("<=======================RESPONSE=======================>")
                print(response)
                print("<=======================RESPONSE=======================>")
                
                # Synthesize and output speech.
                synthesize_speech(response)
                self.move_to_room(room_number)

    def move_to_room(self, roomNum: int) -> None:
        """Moves to the corresponding room number.
      
        The robot will use a series of predefined commands to navigate from its starting position to the specified room number and back. This only supports a limited set of rooms.
      
        Args:
           roomNum (int): The room number.
        """
        if roomNum not in possible_room_numbers:
            return

        # Create a sequence of forward pseudo-instruction list, with repetition
        forward_instr = lambda room_Num: [instruction 
                                          for instruction, repeat in zip(roomNum_to_pathElems[room_Num][0],
                                                                         roomNum_to_pathElems[room_Num][1]) 
                                          for _ in range(repeat)
                                         ]
        fwd_instr = forward_instr(roomNum)
        # Reverse the forward pseudo-instructions.
        bck_instr = fwd_instr[::-1]

        # Enforce turning around for robt to face the reverse path. 
        bck_instr.insert(2, 'turnLeft')
        bck_instr.insert(2, 'turnLeft')
        
        # Negate all turns except last.
        # 1. Change all psuedo-instructions that turn the robot.
        change = lambda pseudo_turn : ('turnRight' if pseudo_turn == 'turnLeft' else 'turnLeft')
        bck_instr = [change(pseudo_instr) if pseudo_instr in ["turnLeft","turnRight"] else pseudo_instr for pseudo_instr in bck_instr]
        
        # 2. Undo the change turn on the last turn using backward pseudo-instruction list.
        last_turn_index = next(ind for ind, instruction in enumerate(bck_instr[::-1]) if instruction in ["turnLeft", "turnRight"])
        bck_instr[-last_turn_index-1] = change(bck_instr[-last_turn_index-1])
        
        # 3. Show the paths from A to B (forward psuedo-instructions), and B to A (backward pseudo-instructions):
        print(f"Forward Sequence:\n {fwd_instr}\n\n") 
        print(f"Backward Sequence:\n {bck_instr}\n\n")

        # 4. Move according to the forward path, then the backward path using the service from go_pupper_srv.service.go_pupper.py
        for instr in (fwd_instr+bck_instr):
            display_sting = ''

            # If the psuedo-instruction is to move forward, call the service to move the robot forward.
            if instr == "moveForward":
                display_sting += ' Front'
                self.show_expression(
                        file_path= cwd+"img/forward.png",
                        new_file_path= cwd+"img/new_forward.png"
                        )
                self.send_move_request("move_forward")

            # Although not needed (since robot moves Forward, and turns left or right by 90 degrees),
            # If the psuedo-instruction is to backward forward, call the service to move the robot backward.
            if instr == "moveBackward":#if not touchValue_Back:
                display_sting += ' Back'
                self.show_expression(
                        file_path=cwd+"img/backward.png", 
                        new_file_path=cwd+"img/new_backward.png"
                        )
                self.send_move_request("move_backward")
                
            # If the psuedo-instruction is to turn right, call the service to turn the robot right 90 degrees, in-place.
            if instr == "turnRight":
                  display_sting += ' Right'
                  self.show_expression(
                          file_path=cwd+"img/right.png", 
                          new_file_path=cwd+"img/new_right.png"
                          )
                  self.send_move_request("turn_right")
                  
             # If the psuedo-instruction is to turn left, call the service to turn the robot left 90 degrees, in-place.
            if instr == "turnLeft":
                display_sting += ' Left'
                self.show_expression(
                        file_path=cwd+"img/left.png",
                        new_file_path=cwd+"img/new_left.png"
                        )
                self.send_move_request("turn_left")
                
            # If the psuedo-instruction is to have the pupper "stay", call the service to make the robot stay in-place.
            # (Just sleeps and sends no Twist message for movement).
            if instr == "stay":#if display_sting == '':
                display_sting = 'Thinking ... Staying'
                self.show_expression(
                        file_path=cwd+"img/logo.png",
                        new_file_path=cwd+"img/new_logo.png"
                        )
                self.send_move_request("stay")
            
            # If the psuedo-instruction was not well-formed (mistyped) or any-other isssue occured with the pseudo-instruction,
            # don't even call  the service to send a Twist message for movement.
            else:
                display_sting = 'Waiting to move'
                self.show_expression(
                        file_path=cwd+"img/logo.png", 
                        new_file_path=cwd+"img/new_logo.png"
                        )
                print(display_sting)

# Name: Main
# Purpose: Main function. Going to try to have the robot move based on touch and display an expression for every direction. 
#####
def main():
    rclpy.init()
    sample_controller = SampleControllerAsync()

    # send commands to do the touch-based movement
    sample_controller.pupper_touch_movement()

    # This spins up a client node, checks if it's done, throws an exception of there's an issue
    # (Probably a bit redundant with other code and can be simplified. But right now it works, so ¯\_(ツ)_/¯)
    while rclpy.ok():
        rclpy.spin_once(sample_controller)
        if sample_controller.future.done():
            try:
                response = sample_controller.future.result()
            except Exception as e:
                sample_controller.get_logger().info(
                    'Service call failed %r' % (e,))
            else:
                sample_controller.get_logger().info(
                   'Result of command: %s ' %
                   (response))
            break

    # Destroy node and shut down
    sample_controller.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()


