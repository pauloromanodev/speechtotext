import shutil
import datetime
import os 
import glob

from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
import pytube
from moviepy.editor import *
import speech_recognition as sr 
from pydub import AudioSegment
from pydub.silence import split_on_silence

var_path = os.getcwd()
r = sr.Recognizer()

import pytube
from moviepy.editor import *

def download_youtube_audio(url, output_path="."):
    # Create a YouTube object from the video URL
    yt = pytube.YouTube(url)

    print(yt.title)

    # Get the audio stream
    audio_stream = yt.streams.filter(only_audio=True).first()

    # Download the audio to the specified output path
    audio_stream.download(output_path=output_path)

    arquivo = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Convert the downloaded audio file to a WAV file
    video_file_path = f"{output_path}/{audio_stream.default_filename}"
    audio = AudioFileClip(video_file_path)
    audio.write_audiofile(f"{output_path}/{arquivo}.wav")

    audio_filename = f"{output_path}/{arquivo}.wav"

    return audio_filename


def get_large_audio_transcription(path):
    """
    Splitting the large audio file into chunks
    and apply speech recognition on each of these chunks
    """
    # open the audio file using pydub
    sound = AudioSegment.from_wav(path)  
    # split audio sound where silence is 700 miliseconds or more and get chunks
    chunks = split_on_silence(sound,
        # experiment with this value for your target audio file
        min_silence_len = 500,
        # adjust this per requirement
        silence_thresh = sound.dBFS-14,
        # keep the silence for 1 second, adjustable as well
        keep_silence=500,
    )
    folder_name = "audio-chunks"
    # create a directory to store the audio chunks
    if not os.path.isdir(folder_name):
        os.mkdir(folder_name)
    whole_text = ""
    # process each chunk 
    for i, audio_chunk in enumerate(chunks, start=1):
        # export audio chunk and save it in
        # the `folder_name` directory.
        chunk_filename = os.path.join(folder_name, f"chunk{i}.wav")
        audio_chunk.export(chunk_filename, format="wav")
        # recognize the chunk
        with sr.AudioFile(chunk_filename) as source:
            audio_listened = r.record(source)
            # try converting it to text
            try:
                text = r.recognize_google(audio_listened)
            except sr.UnknownValueError as e:
                print("Error:", str(e))
            else:
                text = f"{text.capitalize()}. "
                print(chunk_filename, ":", text)
                whole_text += text
    filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".txt"
    with open(filename, 'w') as f:
        f.write(whole_text)
    # return the text for all chunks detected
    return whole_text


url = input("Please enter the YouTube video URL: ")

# parse the URL and extract the video ID
parsed_url = urlparse(url)
video_id = parse_qs(parsed_url.query)['v'][0]

# print the video ID
print("Video ID:", video_id)

try: #tenta baixar a legenda.
    srt = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])

    text_list = [i['text'] for i in srt]  # extract all text values
    full_text = ' '.join(text_list)  # join text values with a space

    print(full_text)  # print the concatenated text

    filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".txt"
    with open(filename, 'w') as f:
        f.write(full_text)

except Exception as e: #se não der, baixa o wav e faz speech to text.
    print("An error occurred: ", e)

    output_path = var_path

    audio_filename = download_youtube_audio(url, output_path)

    full_text = get_large_audio_transcription(audio_filename)

    filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".txt"
    with open(filename, 'w') as f:
        f.write(full_text)

    print("\nFull text:", full_text)
    print("\nfilename:", filename)

    # delete all .mp4 and .wav files
    for file in glob.glob("*.mp4"):
        os.remove(file)
    for file in glob.glob("*.wav"):
        os.remove(file)

    # delete the audio-chunks folder and its contents
    if os.path.exists("audio-chunks"):
        shutil.rmtree("audio-chunks")