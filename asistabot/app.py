import os
import datetime
from dateutil import parser as date_parser
import spacy
import openai
import speech_recognition as sr
from gtts import gTTS
import tempfile
import subprocess

from google.oauth2 import credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import build

import pyowm
from stackapi import StackAPI

# Replace 'your_openweathermap_api_key' with your actual OpenWeatherMap API key
owm = pyowm.OWM('3ac870b912b7e55af566c4c5c4c50063')
stack_api = StackAPI('stackoverflow')

def get_weather(location):
    observation = owm.weather_at_place(location)
    weather = observation.get_weather()
    return weather.get_status()

def search_stackoverflow(query):
    questions = stack_api.fetch('search/advanced', sort='votes', q=query)
    return questions['items'][:3]

tasks = []

def add_task(task):
    tasks.append(task)

def remove_task(task):
    tasks.remove(task)

def list_tasks():
    return tasks


# Replace 'path/to/credentials.json' with the actual path to your downloaded credentials.json
creds_file = 'path/to/credentials.json'
scopes = ['https://www.googleapis.com/auth/calendar']

flow = InstalledAppFlow.from_client_secrets_file(creds_file, scopes)
creds = flow.run_local_server(port=0)
service = build('calendar', 'v3', credentials=creds)

nlp = spacy.load('en_core_web_sm')

# Replace 'your_api_key' with your actual API key
openai.api_key = 'your_api_key'

def text_to_speech(text):
    tts = gTTS(text=text, lang='en')
    with tempfile.NamedTemporaryFile(delete=True) as fp:
        tts.save(fp.name)
        subprocess.run(["mpg123", "-q", fp.name])

def speech_to_text():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = r.listen(source)
        try:
            text = r.recognize_google(audio)
            return text
        except Exception as e:
            print("Error:", e)
            return None

import openai

# Replace 'your_api_key' with your actual API key
openai.api_key = 'your_api_key'

def generate_response(prompt):
    model_engine = "gpt-3.5-turbo"

    response = openai.ChatCompletion.create(
        model=model_engine,
        messages=[
            {"role": "system", "content": "You are an advanced AI assistant with expertise in various domains, such as programming, management, and general knowledge."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=50,
        n=1,
        stop=None,
        temperature=0.5,
    )

    message = response.choices[0].text.strip()
    return message

def parse_input(text):
    doc = nlp(text)
    date = None
    time = None
    email = None

    for ent in doc.ents:
        if ent.label_ == 'TIME':
            time = date_parser.parse(ent.text)
        elif ent.label_ == 'DATE':
            date = date_parser.parse(ent.text)
        elif ent.label_ == 'EMAIL':
            email = ent.text

    if date and time:
        date = date.replace(hour=time.hour, minute=time.minute)

    return email, date

def schedule_event(email, date, event_title):
    event = {
        'summary': event_title,
        'start': {
            'dateTime': date.isoformat(),
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': (date + datetime.timedelta(hours=1)).isoformat(),
            'timeZone': 'UTC',
        },
        'attendees': [
            {'email': email},
        ],
    }

    created_event = service.events().insert(calendarId='primary', body=event).execute()
    return created_event

# Display the welcome message
print("Welcome to the meeting scheduling assistant!")
text_to_speech("Welcome to the meeting scheduling assistant!")

while True:
    print("Please say your request:")
    user_input = speech_to_text()

    if user_input:
        gpt_prompt = f"Schedule a meeting based on the following input: {user_input}"
        gpt_response = generate_response(gpt_prompt)
        email, date = parse_input(gpt_response)

        if email and date:
            text_to_speech("What is the title of this event?")
            event_title = speech_to_text()
            event = schedule_event(email, date, event_title)
            response = f"Event scheduled: {event['htmlLink']}"
        else:
            response = "Unable to parse the input. Please provide an email and a date/time."
    else:
        response = "I couldn't understand your input. Please try again."

    print(response)
    text_to_speech(response)