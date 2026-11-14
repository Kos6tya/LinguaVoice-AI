import os
import json
import base64
import tempfile
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from dotenv import load_dotenv
import edge_tts
from sqlalchemy.orm import Session

from database import engine, Base, get_db
import models

Base.metadata.create_all(bind=engine)

load_dotenv()

app = FastAPI(title="LinguaVoice AI Tutor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("Помилка: GROQ_API_KEY не знайдено у .env файлі!")

groq_client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
You are a friendly, encouraging, and intelligent English language tutor. 
The user is speaking to you to practice conversational English.
Your tasks:
1. Respond naturally to continue the conversation in simple and clear English (CEFR B1-B2 level).
2. Analyze what the user said. If there are any grammatical, pronunciation (phonetic mistakes transcribed), or vocabulary errors, point them out gently. If there are no errors, leave the corrections array empty.

You MUST respond strictly with a valid JSON object matching this schema:
{
  "reply": "Your conversational answer here",
  "corrections": [
    {
      "original": "part of user's sentence with mistake",
      "correction": "corrected version",
      "explanation": "short explanation of the grammar rule"
    }
  ]
}
Do not include markdown blocks like ```json, just return the raw JSON object.
"""

async def generate_speech_base64(text: str, voice: str = "en-US-JennyNeural") -> str:
    communicate = edge_tts.Communicate(text, voice)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        tmp_path = tmp_file.name

    await communicate.save(tmp_path)
    with open(tmp_path, "rb") as f:
        audio_bytes = f.read()
    os.remove(tmp_path)
    return base64.b64encode(audio_bytes).decode("utf-8")

def get_or_create_default_session(db: Session):
    """Створює або повертає активну тестову сесію для учня."""
    user = db.query(models.User).first()
    if not user:
        user = models.User(username="DefaultStudent", target_level="B1")
        db.add(user)
        db.commit()
        db.refresh(user)

    session = db.query(models.ChatSession).filter_by(user_id=user.id).order_by(models.ChatSession.created_at.desc()).first()
    if not session:
        session = models.ChatSession(user_id=user.id, topic="Everyday English Conversation")
        db.add(session)
        db.commit()
        db.refresh(session)
    return session

@app.post("/api/v1/chat/voice-turn")
async def voice_turn(
    audio: UploadFile = File(...),
    chat_history: str = Form("[]"),
    db: Session = Depends(get_db)
):
    try:
        audio_content = await audio.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{audio.filename}") as tmp_audio:
            tmp_audio.write(audio_content)
            tmp_audio_path = tmp_audio.name

        with open(tmp_audio_path, "rb") as file_to_transcribe:
            transcription = groq_client.audio.transcriptions.create(
                file=file_to_transcribe,
                model="whisper-large-v3",
                language="en",
                prompt="Student practicing English speech with clear pronunciation.",
                response_format="text"
            )
        os.remove(tmp_audio_path)
        
        user_text = transcription.strip()
        if not user_text:
            raise HTTPException(status_code=400, detail="Не вдалося розпізнати мову.")

        try:
            history = json.loads(chat_history)
        except Exception:
            history = []

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_text})

        all_models = [m.id for m in groq_client.models.list().data if "whisper" not in m.id]
        chosen_model = next((m for m in all_models if "llama-3" in m), all_models[0])

        completion = groq_client.chat.completions.create(
            model=chosen_model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.6,
        )

        response_content = completion.choices[0].message.content
        ai_data = json.loads(response_content)
        ai_reply = ai_data.get("reply", "I heard you!")
        corrections = ai_data.get("corrections", [])

        audio_base64 = await generate_speech_base64(ai_reply)

        current_session = get_or_create_default_session(db)

        user_msg = models.Message(
            session_id=current_session.id,
            sender="user",
            content=user_text
        )
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)

        for c in corrections:
            correction_entry = models.GrammarCorrection(
                message_id=user_msg.id,
                original_phrase=c.get("original", ""),
                corrected_phrase=c.get("correction", ""),
                explanation=c.get("explanation", "")
            )
            db.add(correction_entry)

        ai_msg = models.Message(
            session_id=current_session.id,
            sender="assistant",
            content=ai_reply
        )
        db.add(ai_msg)
        db.commit()

        return {
            "status": "success",
            "user_transcript": user_text,
            "ai_response": ai_reply,
            "corrections": corrections,
            "audio_base64": audio_base64
        }

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/mistakes")
def get_student_mistakes(db: Session = Depends(get_db)):
    mistakes = db.query(models.GrammarCorrection).all()
    return {
        "total_mistakes": len(mistakes),
        "history": [
            {
                "original": m.original_phrase,
                "correction": m.corrected_phrase,
                "explanation": m.explanation,
                "date": m.created_at
            }
            for m in mistakes
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)