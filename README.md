<div align="left">
  <img src="Screenshots/logo.png" alt="PaperMark AI Logo" width="55" align="left" style="margin-right: 15px;">

  <h1>
    PaperMark AI Backend
    <img src="https://img.shields.io/badge/version-v1.0-green" alt="v1.0">
    <img src="https://img.shields.io/badge/status-Beta-orange" alt="Beta">
  </h1>
</div>

<br clear="left">

PaperMark AI Backend is the backend service for PaperMark AI, an AI-assisted assignment evaluation platform for instructors.

The backend provides the API, authentication, database communication, AI-assisted evaluation, student data management, and evaluation result processing used by the PaperMark AI frontend.

The project is currently in the MVP and development stage.

## API

Backend API:

https://papermark-ai-backend.onrender.com/

Frontend:

https://paper-mark-ai-frontend.vercel.app/

## About the Project

The PaperMark AI backend is built with FastAPI and provides the services required by the frontend application.

It handles instructor authentication, evaluation creation, student information, evaluation requests, AI processing, and evaluation results.

The backend communicates with the database and the AI provider to process evaluation requests and return results to the frontend.

## Current Features

- Instructor registration
- Instructor login
- Authentication and protected routes
- User management
- Evaluation creation
- Question and expected answer handling
- Student management
- Student answer processing
- AI-assisted answer evaluation
- Score and percentage generation
- Evaluation feedback
- Evaluation result handling
- Analytics data
- PostgreSQL database integration
- Groq API integration
- CORS configuration for the production frontend

## Technology

### Backend

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- Uvicorn
- PostgreSQL
- Supabase

### AI

- Groq API
- AI-assisted answer evaluation
- AI-generated evaluation feedback

### Authentication

- JWT authentication
- Password hashing
- HTTP-only authentication cookies

### Deployment

- Render for the backend
- Supabase for PostgreSQL
- GitHub for source control

## Project Structure

The backend is organized into separate modules for the API routes, authentication, database connection, models, schemas, and application configuration.

```text
PaperMark-AI-Backend/
│
├── app/
│   ├── routes/
│   ├── auth.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── main.py
│
├── requirements.txt
├── .gitignore
└── README.md
```

## Frontend Repository

The frontend is maintained separately:

https://github.com/NafeesIkram/PaperMark-AI-Frontend

The frontend is responsible for the user interface, instructor dashboard, evaluation setup, student management, results, analytics, and communication with this backend API.

## Running the Backend Locally

### 1. Clone the repository

```bash
git clone https://github.com/NafeesIkram/PaperMark-AI-Backend.git
```

### 2. Open the project

```bash
cd PaperMark-AI-Backend
```

### 3. Create a virtual environment

Windows:

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file in the project root.

The application requires environment variables for database access, authentication, AI API configuration, and the frontend URL.

Example:

```env
DATABASE_URL=your_database_url
JWT_SECRET=your_jwt_secret
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=your_groq_model
FRONTEND_URL=http://localhost:3000
```

Do not commit the `.env` file or any API keys to GitHub.

### 6. Start the backend

```bash
python -m uvicorn app.main:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

## API Documentation

When running the backend locally, FastAPI provides interactive API documentation at:

```text
http://localhost:8000/docs
```

The deployed backend also provides the documentation through its `/docs` endpoint.

## Environment Configuration

The production backend uses environment variables for sensitive configuration.

These include:

- Database connection
- JWT secret
- Groq API key
- AI model configuration
- Frontend URL

Sensitive credentials are kept outside the source code and are configured through the deployment environment.

## Future Development

The backend is still under development. Some of the features planned for future versions include:

- PDF assignment processing
- PDF text extraction
- OCR for scanned assignments
- Handwritten answer processing
- Code and programming question evaluation
- AI-assisted plagiarism checking
- More detailed evaluation comments
- Descriptive evaluation generation
- Automated report generation
- PDF annotation support
- Advanced rubric-based evaluation
- Grammar and writing analysis
- Advanced analytics
- Evaluation history
- Additional AI model and provider support
- Instructor review and manual adjustment of AI-generated results

## Development Status

The current version is an MVP. The core backend services for authentication, database communication, AI-assisted evaluation, student management, and evaluation results are implemented.

Additional document processing and advanced evaluation features are being developed incrementally.

## Developer

Nafees Ikram

Developer interested in software development, AI applications, web development, automation, and technology projects.

## Note

PaperMark AI Backend is a personal development project and is currently being developed and improved through continuous testing and iteration.
