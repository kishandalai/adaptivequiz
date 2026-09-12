# AdaptiveQuiz

AdaptiveQuiz is a student-focused adaptive quiz platform built with Python, Django, Django REST Framework, PostgreSQL, HTML, CSS, and JavaScript. The system generates multiple-choice questions automatically using the Google Gemini API and adjusts difficulty as the learner answers correctly or incorrectly.

## Features

- User registration and login
- Subject and topic selection
- Adaptive quiz flow with Easy, Medium, and Hard difficulty
- AI-generated questions from Google Gemini
- Validated JSON question banks with 13 questions per topic
- Performance tracking and analytics
- Quiz history and topic insights
- PostgreSQL-backed data storage
- REST APIs for dashboard and quiz operations

## Technology Stack

- Python 3
- Django
- Django REST Framework
- PostgreSQL
- HTML, CSS, JavaScript
- Google Gemini API via official GenAI Python SDK
- Chart.js

## Project Architecture

- `adaptivequiz/` contains Django project settings
- `quiz/` contains models, views, serializers, adaptive logic, and Gemini integration
- `templates/` contains reusable HTML pages
- `static/` contains CSS and JavaScript files

## Installation on Windows

1. Open PowerShell in the project folder.
2. Create a virtual environment:

   ```powershell
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

4. Create a `.env` file from `.env.example` and update values.

5. Create and configure PostgreSQL database:

   ```sql
   CREATE DATABASE adaptivequiz;
   ```

6. Run migrations:

   ```powershell
   python manage.py makemigrations
   python manage.py migrate
   ```

7. Create a superuser:

   ```powershell
   python manage.py createsuperuser
   ```

   Set `ADMIN_USERNAME` in `.env` to the username of the one account that should use the separate Admin Panel. The account must be a Django staff account. Open `/admin-panel/login/` to sign in; the normal user dashboard and login flow are unchanged.

8. Run the development server:

   ```powershell
   python manage.py runserver
   ```

## Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your_secret_key_here
DEBUG=True
GEMINI_API_KEY=your_gemini_api_key_here
ADMIN_USERNAME=admin

DB_NAME=adaptivequiz
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_HOST=localhost
DB_PORT=5432
```

## PostgreSQL Setup

Install PostgreSQL on Windows, then open pgAdmin or psql. Create the database:

```sql
CREATE DATABASE adaptivequiz;
```

Set your environment variables to match the local PostgreSQL configuration.

## Gemini API Setup

1. Visit Google AI Studio.
2. Create a Gemini API key.
3. Store the key in the `.env` file under `GEMINI_API_KEY`.
4. Django loads this value from the environment during startup.
5. The Gemini service in `quiz/gemini_service.py` uses this key to generate questions.

Never commit the real `.env` file to GitHub.

## Usage

1. Register a new account.
2. Log in to the dashboard.
3. Select a subject and topic.
4. Start a quiz.
5. Answer 10 generated questions.
6. Review score, performance, and quiz history.

## API Endpoints

All API endpoints require an authenticated Django session and return JSON. Every success response contains `success: true`. Every error response contains `success: false` and an `error` object with `code` and `message`.

### Generate question

`POST /api/generate-question/`

Request:

```json
{"subject": "Python", "topic": "Functions", "difficulty": "Medium"}
```

Returns HTTP 200 with `success` and a `question` object containing `id`, `subject`, `topic`, `difficulty`, `question`, and four `{id, text}` options. The correct answer is never included.

### Start quiz

`POST /api/quiz/start/`

Request:

```json
{"subject": "Python", "topic": "Functions"}
```

Returns HTTP 201 with `success` and a `quiz` object. New quizzes always begin at `Easy` and `in_progress`.

### Current question

`GET /api/quiz/<quiz_id>/question/`

Returns HTTP 200 with `success` and the current question. Correct answers are omitted.

### Submit answer

`POST /api/submit-answer/`

Request:

```json
{"question_id": 123, "selected_option": "A", "time_taken": 12}
```

Returns HTTP 200 with `success` and `result`, including correctness, explanation, correct option, and adaptive difficulty values.

### Next question

`POST /api/quiz/<quiz_id>/next/`

Request:

```json
{"previous_question_id": 123}
```

Returns HTTP 200 with the next `quiz` state and question. Questions do not expose the correct answer.

### Complete quiz

`POST /api/quiz/<quiz_id>/complete/`

Returns HTTP 200 with the final score, accuracy, highest difficulty, and `completed` status. Completed quizzes reject further answers with `QUIZ_COMPLETED`.

### Dashboard

`GET /api/dashboard/`

Returns HTTP 200 with `dashboard`: username, quiz totals, accuracy, level, strongest topic, and weakest topic.

### Performance

`GET /api/performance/`

Returns HTTP 200 with overall totals and per-topic performance rows.

### Quiz history

`GET /api/quiz-history/`

Returns HTTP 200 with only the authenticated user’s quiz history.

### Topics

`GET /api/topics/`

Returns HTTP 200 with a `subjects` array containing each subject name and its topics.

Common error codes include `INVALID_REQUEST`, `INVALID_DIFFICULTY`, `QUESTION_NOT_FOUND`, `QUIZ_NOT_FOUND`, `QUIZ_COMPLETED`, `GEMINI_ERROR`, `INVALID_ANSWER`, and `UNAUTHORIZED`.

## Adaptive Algorithm

- Two consecutive correct answers increase difficulty.
- Two consecutive wrong answers decrease difficulty.
- Difficulty stays between Easy and Hard.
- The backend controls difficulty; the frontend never decides it.

## Question Bank

Normal quiz progression uses the JSON files in `question_bank/`, not Gemini. Each supported subject has a JSON file, every supported topic contains exactly 13 validated questions, and each quiz randomly selects 10 IDs once at startup. Those IDs are stored on `QuizAttempt.selected_question_ids` and are used in order for the entire attempt. Gemini remains available through the explicit question-generation endpoint for future bank expansion, but it is never called after an answer during normal quiz progression.

Question-bank validation checks unique IDs, normalized question text, four unique options, valid answer keys, explanations, subjects, topics, and difficulties before a quiz starts.

## Git Commands

```bash
git init
git add .
git commit -m "Initial AdaptiveQuiz project"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY
git push -u origin main
```

## Common Errors

- Missing `.env` values
- PostgreSQL server not running
- Incorrect database credentials
- Gemini API key invalid or missing
- Migration issues caused by schema drift

## Future Improvements

- Add teacher/admin review tools
- Allow custom quiz lengths
- Add more subjects and topics
- Improve analytics with richer charts
- Add email verification and password reset

## License

This project is created for learning and demonstration purposes.
