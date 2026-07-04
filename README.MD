## 🎬 Online Cinema API

Welcome to the backend API of the Online Cinema Platform, built with FastAPI.
This project demonstrates a production-ready authentication system, JWT token lifecycle management, background task
processing with Celery, and a fully featured movie catalog with filtering, search, pagination, and favorites support.

## Core Features
### Authentication & Security

#### User Registration
- Email Service: SMTP (Mailtrap for development) 
- Email uniqueness validation
- Activation link valid for 24 hours
- Resend activation link functionality
- Automatic deletion of expired activation tokens
- Background cleanup handled by Celery Beat

#### Login
- Returns Access + Refresh JWT tokens
- Configurable expiration times
- Secure password hashing

#### Logout
- JWT invalidation mechanism
- Prevents reuse of previously issued tokens

#### Password Management
- Change password with old password verification
- Forgot password flow via email reset link
- Password complexity validation

### 🎥 Movie Catalog
#### Search
#### Search by:
- Title
- Description
- Actor
- Director
#### Filtering
#### Filter movies by:
- Release year
- IMDb rating
- Other supported attributes
#### Sorting
#### Sort by:
- Price
- Release date
- Popularity
#### Genres
- List all genres
- Display movie count per genre
- Filter movies by selected genre
#### Pagination
- Paginated catalog responses for optimized performance
#### Favorites
- Add movies to favorites
- Remove movies from favorites

## Background Task Processing
The project uses Celery with Redis as a message broker and result backend.

### Celery Configuration

```
celery = Celery(
    "online_cinema",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["src.tasks.activation_tokens"]
)
```
### Periodic Task (Celery Beat)
Expired activation tokens are automatically removed:
```
celery.conf.beat_schedule = {
    "delete-expired-activation-tokens": {
        "task": "src.tasks.activation_tokens.delete_expired_tokens",
        "schedule": 9000.0,
    }
}
```
#### What the Task Does:
- Checks activation tokens with expired timestamps
- Deletes expired entries from the database
- Commits changes asynchronously
- Runs periodically without blocking API requests

## Project Architecture Overview
The project follows a modular structure to separate responsibilities clearly:
- **`routes/`**: API endpoints
- **`schemas/`**: Pydantic request/response models
- **`models/`**: SQLAlchemy models
- **`security/`**: JWT management and password hashing
- **`notifications/`**: Email sending logic
- **`tasks/`**: Celery background tasks

## Environment Variables
Below is an example **`.env`** configuration:
```
# Mail
SMTP_SERVER=sandbox.smtp.mailtrap.io
SMTP_PORT=587
SMTP_USERNAME=your_username
SMTP_PASSWORD=your_password
MAIL_FROM=noreply@cinema.com

# JWT
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
```

## Running the Project (Local Development)
1. Install Dependencies
```
pip install -r requirements.txt
```
2. Run Redis
```
redis-server
```
3. Start FastAPI
```
uvicorn src.main:app --reload
```
4. Start Celery Worker
```
celery -A src.celery_app.celery worker --loglevel=info
```
5. Start Celery Beat
```
celery -A src.celery_app.celery beat --loglevel=info
```
## Running with Docker
### Build and Start Containers
From the root of the project, run:
```bash
docker-compose up --build
```
This will start:

**`online-cinema-app`** – FastAPI application

**`online-cinema-db`** – PostgreSQL database

The first time you run this, the database will be initialized automatically.
### Environment Variables
Docker reads environment variables from **`.env`**. Make sure you have configured at least the database URL:
```
DATABASE_URL=postgresql+asyncpg://postgres:password@online-cinema-db:5432/online_cinema
```
- Replace **`password`** with your desired PostgreSQL password.
- **`online-cinema-db`** is the name of PostgreSQL container

## API Documentation
Interactive documentation is available:
- Swagger -> **`/docs`**
- ReDoc -> **`/redoc`**