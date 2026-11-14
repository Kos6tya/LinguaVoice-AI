import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app
from database import Base, engine, get_db
import models

client = TestClient(app)

@pytest.fixture(autouse=True)
def run_around_tests():
    # Очищуємо базу перед кожним тестом
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_database_models():
    """Тест створення сутностей у базі даних (ORM)."""
    from database import SessionLocal
    db = SessionLocal()
    user = models.User(username="TestStudent", target_level="B2")
    db.add(user)
    db.commit()
    db.refresh(user)

    assert user.id is not None
    assert user.username == "TestStudent"

    session = models.ChatSession(user_id=user.id, topic="Travel")
    db.add(session)
    db.commit()

    msg = models.Message(session_id=session.id, sender="user", content="Hello world")
    db.add(msg)
    db.commit()

    corr = models.GrammarCorrection(
        message_id=msg.id,
        original_phrase="He go",
        corrected_phrase="He goes",
        explanation="Third person -s rule"
    )
    db.add(corr)
    db.commit()

    saved_corr = db.query(models.GrammarCorrection).first()
    assert saved_corr.original_phrase == "He go"
    db.close()

def test_get_mistakes_analytics_empty():
    """Тест аналітики, коли база порожня."""
    response = client.get("/api/v1/analytics/mistakes")
    assert response.status_code == 200
    assert response.json()["total_mistakes"] == 0

@patch("main.groq_client")
@patch("main.generate_speech_base64")
def test_voice_turn_full_pipeline(mock_tts, mock_groq):
    """Повний наскрізний тест ендпоінту голосового ходу."""
    mock_groq.audio.transcriptions.create.return_value = "I wants coffee"

    m = MagicMock()
    m.id = "llama-3.1-8b-instant"
    mock_groq.models.list.return_value.data = [m]

    comp = MagicMock()
    comp.choices = [
        MagicMock(message=MagicMock(content='{"reply": "Here is your coffee!", "corrections": [{"original": "I wants", "correction": "I want", "explanation": "Rule"}]}'))
    ]
    mock_groq.chat.completions.create.return_value = comp

    mock_tts.return_value = "AAAA_BASE64_SOUND"

    file_payload = ("audio.m4a", b"fake binary voice", "audio/m4a")
    response = client.post(
        "/api/v1/chat/voice-turn",
        files={"audio": file_payload},
        data={"chat_history": "[]"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["user_transcript"] == "I wants coffee"
    assert len(data["corrections"]) == 1
    assert data["audio_base64"] == "AAAA_BASE64_SOUND"

    analytics = client.get("/api/v1/analytics/mistakes")
    assert analytics.status_code == 200
    assert analytics.json()["total_mistakes"] == 1