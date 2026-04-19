# P2P Palestine - Docker Setup Guide

## Overview
This guide explains how to set up and run the P2P Palestine platform using Docker.

## Prerequisites
- Docker Desktop installed (Windows/Mac) or Docker Engine + Docker Compose (Linux)
- Git (for cloning the repository)

## Quick Start

### 1. Clone and configure
```bash
# Navigate to project directory
cd /workspace

# Copy environment file (already done)
cp .env.example .env
```

### 2. Start All Services
```bash
# Build and start all containers
docker compose up -d --build
```

### 3. Verify Services
```bash
# Check running containers
docker compose ps

# View logs
docker compose logs -f api
```

## Services Available

| Service   | URL                    | Credentials              |
|-----------|------------------------|--------------------------|
| FastAPI   | http://localhost:8000  | -                        |
| pgAdmin   | http://localhost:5050  | admin@p2p.com / admin123 |
| PostgreSQL| localhost:5432         | p2p_user / p2p_password  |

## API Documentation
Once running, access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Database Management

### Connect via pgAdmin
1. Open http://localhost:5050
2. Login with: admin@p2p.com / admin123
3. Add server connection:
   - Host: db (container name)
   - Port: 5432
   - Database: p2p_palestine_db
   - Username: p2p_user
   - Password: p2p_password

### Direct Connection (from host)
```bash
psql -h localhost -U p2p_user -d p2p_palestine_db
```

## Common Commands

```bash
# Stop all services
docker compose down

# Stop and remove volumes (WARNING: deletes all data!)
docker compose down -v

# Restart a specific service
docker compose restart api

# View real-time logs
docker compose logs -f

# Run database migrations (when implemented)
docker compose exec api alembic upgrade head

# Access container shell
docker compose exec api bash
```

## Troubleshooting

### Database Connection Issues
If the API can't connect to the database:
```bash
# Check if database is healthy
docker compose ps db

# View database logs
docker compose logs db

# Restart database
docker compose restart db
```

### Port Already in Use
If ports 8000, 5050, or 5432 are occupied:
1. Edit `docker-compose.yml` and change the port mappings
2. Or stop the conflicting service

### Reset Everything
```bash
docker compose down -v
docker compose up -d --build
```

## Production Deployment

For production:
1. Update `.env` with strong secrets
2. Set `DEBUG=False`
3. Use environment variables instead of `.env` file
4. Consider using Docker Swarm or Kubernetes
5. Add SSL/TLS termination
6. Configure proper backup strategy for volumes

## Data Persistence
- PostgreSQL data: `postgres_data` volume
- pgAdmin data: `pgadmin_data` volume

These volumes persist even if containers are deleted. To completely reset:
```bash
docker volume rm workspace_postgres_data
docker volume rm workspace_pgadmin_data
```

## ✅ Database Connection Status

The PostgreSQL database is now fully integrated with the FastAPI application:

1. **Environment Variables**: The app reads `DATABASE_URL` from the `.env` file
2. **Docker Configuration**: In the container, the DB hostname is `db` (service name)
3. **Local Development**: Uses `localhost:5432` when running outside Docker
4. **Health Checks**: Database health is verified before API starts
5. **Auto Table Creation**: Tables are created on application startup

### Connection String Formats:
- **Inside Docker**: `postgresql://p2p_user:p2p_password@db:5432/p2p_palestine_db`
- **Local Host**: `postgresql://p2p_user:p2p_password@localhost:5432/p2p_palestine_db`
