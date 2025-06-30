# Swayami Backend

FastAPI backend for Swayami - Self-reliance dashboard with AI-powered productivity features.

## Features

- **FastAPI Framework**: Modern, fast web framework for building APIs
- **MongoDB Atlas**: Cloud database for data persistence
- **Authentication**: JWT-based authentication with Supabase integration
- **AI Integration**: OpenAI GPT for task generation and analysis
- **CORS Support**: Configured for frontend integration

## Quick Start

### Prerequisites

- Python 3.9+
- MongoDB Atlas account
- OpenAI API key
- Supabase project (for authentication)

### Installation

1. **Clone and setup:**
   ```bash
   git clone <your-backend-repo-url>
   cd swayami-backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment setup:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

5. **Run the server:**
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000`

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `MONGODB_URL` | MongoDB Atlas connection string | Yes |
| `SECRET_KEY` | JWT secret key | Yes |
| `OPENAI_API_KEY` | OpenAI API key for AI features | Yes |
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_JWT_SECRET` | Supabase JWT secret | Yes |
| `CORS_ORIGINS` | Allowed CORS origins | Yes |
| `PORT` | Server port (default: 8000) | No |
| `DEBUG` | Debug mode (default: True) | No |

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user

### Users
- `GET /api/users/by-email/{email}` - Get user by email
- `POST /api/users` - Create new user
- `PUT /api/users/{user_id}` - Update user
- `PUT /api/users/{user_id}/onboarding` - Update onboarding status

### Goals
- `GET /api/goals` - Get user goals
- `POST /api/goals` - Create new goal
- `PATCH /api/goals/{goal_id}/progress` - Update goal progress

### Tasks
- `GET /api/tasks` - Get user tasks
- `POST /api/tasks` - Create new task
- `PUT /api/tasks/{task_id}` - Update task
- `PATCH /api/tasks/{task_id}/status` - Update task status
- `DELETE /api/tasks/{task_id}` - Delete task

### Journals
- `GET /api/journals` - Get user journal entries
- `POST /api/journals` - Create journal entry

### AI Features
- `POST /api/ai/generate-tasks-from-goal` - Generate tasks from goal
- `POST /api/ai/generate-daily-breakdown` - Create daily task breakdown
- `POST /api/ai/analyze-journal` - Analyze journal content
- `POST /api/ai/motivational-message` - Generate motivational message

## Deployment

### Render

1. Connect your GitHub repository to Render
2. Set environment variables in Render dashboard
3. Deploy with the following settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Environment**: Python 3.9+

### Railway

1. Connect your GitHub repository to Railway
2. Add environment variables
3. Deploy automatically on push

### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

## Development

### Running Tests

```bash
python -m pytest test_*.py
```

### Code Structure

```
swayami-backend/
├── app/
│   ├── __init__.py
│   ├── auth.py          # Authentication utilities
│   ├── config.py        # Configuration settings
│   ├── models.py        # Pydantic models
│   ├── api/             # API routes
│   │   ├── auth.py      # Auth endpoints
│   │   ├── users.py     # User management
│   │   ├── goals.py     # Goals management
│   │   ├── tasks.py     # Tasks management
│   │   ├── journals.py  # Journal endpoints
│   │   └── ai.py        # AI-powered features
│   ├── repositories/    # Database access layer
│   └── services/        # Business logic services
├── main.py              # FastAPI application entry point
├── requirements.txt     # Python dependencies
└── .env.example         # Environment variables template
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.
