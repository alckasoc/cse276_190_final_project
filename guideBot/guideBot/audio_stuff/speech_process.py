import boto3
import sounddevice as sd
import numpy as np
import time
import datetime
from scipy.io.wavfile import write
import requests
import json

##Test SoundDevice
#Step 1
duration = 7
sample_rate = 16000
volume_gain_multiplier = 30

audio_data = sd.rec(
            int(duration * sample_rate), samplerate=sample_rate, channels=1
        )
sd.wait() #Wait until recording is finished

#Step 2: Increase volume by a multiplier
aws_audio_file = "tmp/user_audio_input.flac"
audio_data *= volume_gain_multiplier
write(aws_audio_file, sample_rate, audio_data)


##Testing WAV -> AWS Bucket
aws_access_key_id = ""#Please enter your key.
aws_secret_access_key = ""#Please enter your key.
aws_region_name = "us-west-2"

bucket_name = "cse190bucket"
audio_file_key = "gpt_audio.flac" #name of audio file in S3

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

##Send transcription Job and do Job
transcribe_job_uri = f"s3://{bucket_name}/{audio_file_key}"

transcribe_job_name = f'my-transcribe-job-{datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}'
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

##GET Transcription
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
    pass
print(transcript_text)

