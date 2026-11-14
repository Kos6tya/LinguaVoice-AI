# LinguaVoice AI — Personal Voice Assistant for Language Learning

>  Персональний голосовий помічник для вивчення іноземних мов (EdTech).  
> **ШІ-контур:** Інтеграція Groq API (модель Whisper-large-v3 для транскрипції мови + Llama 3 для тьютора) з ультрашвидким відгуком у реальному часі.

---

## Про проєкт

**LinguaVoice AI** — це нативний мобільний комплекс, розроблений для подолання мовного бар'єра при вивченні англійської мови. Додаток забезпечує живий розмовний діалог із ШІ-репетитором без затримок (End-to-End Latency ~1.3 сек), проводить миттєвий граматичний аналіз реплік учня та озвучує відповіді реалістичним нейронним голосом.

### Ключові можливості:
* **Speech-to-Text (STT):** Модель **Whisper-large-v3** через LPU-чипи Groq (точна транскрипція навіть із сильним акцентом).
* **LLM Language Tutor:** Модель **Llama 3** у режимі Structured JSON (підтримує контекст бесіди за стандартом CEFR B1–B2 та знаходить помилки).
* **Smart Grammar Correction:** Виділення помилок, показ виправленого варіанту та пояснення правила простою мовою.
* **Neural Text-to-Speech (TTS):** Озвучення відповідей природним голосом (`en-US-JennyNeural`).
* **Persistence & Analytics:** Збереження історії розмов та помилок у реляційній БД (SQLAlchemy).

---

## Архітектура та стек технологій

* **Мобільний клієнт (Android):** Kotlin, Jetpack Compose, Retrofit 2, OkHttp 4, MediaRecorder, MediaPlayer.
* **Бекенд (API):** Python 3.11+, FastAPI, Uvicorn (ASGI), SQLAlchemy 2.0, Pydantic v2.
* **ШІ-провайдер:** Groq Cloud SDK (Whisper-large-v3, Llama 3).
* **Синтез мови:** Edge-TTS Neural Engine.
* **База даних:** SQLite / PostgreSQL (DDL-схема в `schema.sql`).

---

## Інструкція із запуску

### 1. Клонування репозиторію
```
git clone https://github.com/ВАШ_НІКНЕЙМ/LinguaVoice-AI.git
cd LinguaVoice-AI
```

### 2. Запуск бекенду (FastAPI)
#### 1. Перейдіть до папки сервера та створіть віртуальне оточення:
```
cd linguavoice-backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```
#### 2. Встановіть залежності:
```
pip install -r requirements.txt
```
#### 3. Створіть файл .env у папці linguavoice-backend:
```
GROQ_API_KEY=ваш_ключ_з_console.groq.com
PORT=8000
```
#### 4. Запустіть сервер:
```
python main.py
```
## 3. Запуск мобільного додатку (Android)
#### 1. Відкрийте папку android_app (або LinguaVoice) в Android Studio.
#### 2. Дочекайтеся завершення індексації та Gradle Sync.
#### 3. Прокиньте мережевий порт для емулятора (виконайте в терміналі Android Studio):
```
adb reverse tcp:8000 tcp:8000
```
#### 4. Запустіть додаток, натиснувши кнопку Run 'app' (зелена стрілка).
#### 5. Як користуватися:
Затисніть/натисніть фіолетову кнопку з мікрофоном.
Чітко скажіть фразу англійською (наприклад: "Yesterday I go to cinema").
Зупиніть запис.
ШІ за 1–2 секунди відповість голосом і виведе картку з розбором граматичної помилки.

## Запуск тестів (Unit Tests)
Для перевірки покриття коду тестами:
```
cd linguavoice-backend
pytest -v
# Або з підрахунком покриття:
pytest --cov=. tests/
```

