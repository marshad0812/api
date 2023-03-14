from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
import base64
import openai
from gtts import gTTS

api_key = "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"
model_id = "gpt-3.5-turbo"
openai.api_key = api_key

origins = [
    "http://localhost",
    "http://localhost:5173",
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Data(BaseModel):
    message: str


@app.post("/send_message")
async def send_message(message: Data):
    wav_file = open("temp.mp3", "wb")
    decode_string = base64.b64decode(message.message)
    wav_file.write(decode_string)
    wav_file.close()
    file = open("temp.mp3", "rb")
    transcript = openai.Audio.translate("whisper-1", file)
    return {"message": transcript.get('text')}


@app.post("/send_message_text")
async def send_message_text(message: Data):
    return {"message": message.message}


class GPTData(BaseModel):
    message: str
    conversation: list


@app.post("/get_result")
async def get_result(gpt: GPTData):
    gpt.conversation.append({'role': 'user', 'content': gpt.message})
    response = openai.ChatCompletion.create(
        model=model_id,
        messages=gpt.conversation
    )
    gpt.conversation.append({'role': response.choices[0].message.role, 'content': response.choices[0].message.content})
    text = response.choices[0].message.content
    tts = gTTS(text=text, lang='en')
    tts.save("temp.mp3")
    with open("temp.mp3", "rb") as f:
        base64_bytes = base64.b64encode(f.read())
        base64_string = base64_bytes.decode('utf-8')
    return {"conversation": gpt.conversation, "message": response.choices[0].message.content, "voice": base64_string}

uvicorn.run(app, host="0.0.0.0", port=8000)
