# AI Writer PRO

AI-powered article generation service with comprehensive style analysis, content management, and production-ready infrastructure.

## 🚀 Быстрый деплой на Render

### 1. Создание Blueprint
1. Откройте [Render Dashboard](https://dashboard.render.com)
2. Нажмите **"New +"** → **"Blueprint"**
3. Подключите репозиторий: `druzhkin/ai_writer_PRO`
4. Выберите файл: `render.yaml`
5. Нажмите **"Apply"**

### 2. Настройка переменных окружения
Скопируйте переменные из [RENDER_ENV_VARS.md](RENDER_ENV_VARS.md) в Render Dashboard.

### 3. Готово!
Ваше приложение будет автоматически развернуто на Render.

## 📚 Документация

- **[QUICK_START.md](QUICK_START.md)** - Быстрый старт (5 минут)
- **[RENDER_DEPLOYMENT_GUIDE.md](RENDER_DEPLOYMENT_GUIDE.md)** - Полное руководство по деплою
- **[RENDER_ENV_VARS.md](RENDER_ENV_VARS.md)** - Переменные окружения

## 💰 Стоимость на Render

- **Production**: ~$42/месяц
- **Staging**: ~$28/месяц

## 🚀 Features

- **AI Content Generation**: Generate high-quality articles using OpenAI GPT models
- **Style Analysis**: Analyze writing styles from reference articles
- **Content Management**: Full CRUD operations for articles and style profiles
- **User Authentication**: Secure authentication with JWT and OAuth (Google, GitHub)
- **Organization Management**: Multi-tenant organization support
- **File Upload**: Support for various file formats (PDF, DOCX, images)
- **Usage Tracking**: Comprehensive analytics and usage monitoring
- **Real-time Updates**: WebSocket support for real-time content generation
- **Production Ready**: Complete CI/CD pipeline, monitoring, and deployment setup

## 🏗️ Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis for caching and session management
- **Message Queue**: RabbitMQ with Celery for background tasks
- **Authentication**: JWT tokens with OAuth integration
- **File Storage**: AWS S3 integration
- **Monitoring**: Sentry integration for error tracking
- **Testing**: Comprehensive test suite with pytest

### Frontend (Next.js)
- **Framework**: Next.js 14 with React 18
- **Styling**: Tailwind CSS with responsive design
- **State Management**: Zustand for global state
- **API Integration**: React Query for data fetching
- **Rich Text Editor**: TipTap editor for content editing
- **Testing**: Jest, React Testing Library, and Cypress E2E tests
- **Monitoring**: Sentry integration for error tracking

### Infrastructure
- **Containerization**: Docker and Docker Compose
- **CI/CD**: GitHub Actions with automated testing and deployment
- **Monitoring**: Prometheus and Grafana for metrics
- **Security**: Comprehensive security scanning and dependency checking
- **Performance**: Load testing with Locust
- **Backup**: Automated backup and recovery scripts

## 📋 Prerequisites

- Docker and Docker Compose
- Node.js 18+ and npm
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- RabbitMQ 3+

## 🚀 Quick Start

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/ai-writer-pro.git
   cd ai-writer-pro
   ```

2. **Set up environment variables**
   ```bash
   # Backend
   cp backend/env.example backend/.env
   # Edit backend/.env with your configuration
   
   # Frontend
   cp frontend/.env.example frontend/.env.local
   # Edit frontend/.env.local with your configuration
   ```

3. **Start development services**
   ```bash
   # Start all services
   docker-compose up -d
   
   # Or start individual services
   docker-compose up -d postgres redis rabbitmq
   ```

4. **Set up the backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   alembic upgrade head
   uvicorn app.main:app --reload
   ```

5. **Set up the frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

6. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Production Deployment

1. **Configure production environment**
   ```bash
   # Set up production environment variables
   cp backend/env.example backend/.env.production
   cp frontend/.env.example frontend/.env.production
   ```

2. **Deploy using Docker Compose**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Or deploy using Kubernetes**
   ```bash
   kubectl apply -f k8s/production/
   ```

## Development Workflow

### Using Docker Compose (Recommended)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Local Development
```bash
# Setup script
./scripts/setup.sh

# Development script
./scripts/dev.sh
```

### Database Migrations
```bash
# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "Description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback migration
docker-compose exec backend alembic downgrade -1
```

## Project Structure

```
ai_writer_PRO/
├── frontend/                 # Next.js frontend application
│   ├── src/
│   │   ├── app/             # Next.js 13+ app directory
│   │   ├── components/      # Reusable UI components
│   │   ├── lib/            # Utility functions
│   │   └── types/          # TypeScript type definitions
│   ├── Dockerfile
│   └── package.json
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── api/            # API routes and endpoints
│   │   ├── core/           # Core configuration
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # Business logic
│   ├── alembic/            # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
├── docker/                  # Docker configurations
│   └── postgres/           # PostgreSQL setup
├── scripts/                 # Development scripts
├── docker-compose.yml      # Docker Compose configuration
├── .env.example            # Environment variables template
└── README.md
```

## API Documentation

The FastAPI backend provides automatic API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.
