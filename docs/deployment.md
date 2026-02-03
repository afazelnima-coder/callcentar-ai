# Deployment Guide

This guide covers multiple deployment options for the Call Center Quality Grading System.

## Table of Contents

- [Deployment Options](#deployment-options)
- [Streamlit Cloud (Recommended)](#streamlit-cloud-recommended)
- [Docker Deployment](#docker-deployment)
- [Railway](#railway)
- [Heroku](#heroku)
- [AWS Deployment](#aws-deployment)
- [Production Considerations](#production-considerations)

---

## Deployment Options

| Option | Difficulty | Cost | Best For |
|--------|------------|------|----------|
| Streamlit Cloud | Easy | Free | Quick demos, small teams |
| Docker | Medium | Varies | Flexibility, any cloud |
| Railway | Easy | Free tier | Simple cloud deployment |
| Heroku | Easy | Free tier | Quick deployment |
| AWS (ECS/Fargate) | Hard | Pay-per-use | Production, scale |

---

## Streamlit Cloud (Recommended)

The easiest way to deploy - free hosting directly from GitHub.

### Prerequisites

- GitHub account
- Repository pushed to GitHub

### Steps

1. **Push code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/username/call-center.git
   git push -u origin main
   ```

2. **Create `requirements.txt`** (Streamlit Cloud uses pip):
   ```bash
   uv pip compile pyproject.toml -o requirements.txt
   ```

3. **Create `.streamlit/secrets.toml`** for local testing:
   ```toml
   OPENAI_API_KEY = "sk-your-key"
   DEEPGRAM_API_KEY = "your-key"
   ```

4. **Go to [share.streamlit.io](https://share.streamlit.io)**

5. **Click "New app"** and connect your GitHub repo

6. **Configure**:
   - Repository: `username/call-center`
   - Branch: `main`
   - Main file path: `app/main.py`

7. **Add secrets** in Streamlit Cloud dashboard:
   - Go to App settings → Secrets
   - Add your API keys in TOML format

8. **Deploy** - Click "Deploy!"

### Streamlit Cloud Configuration

Create `.streamlit/config.toml`:
```toml
[server]
maxUploadSize = 100
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
```

---

## Docker Deployment

Package the application in a container for deployment anywhere.

### Dockerfile

Create `Dockerfile`:
```dockerfile
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY pyproject.toml .
COPY README.md .

# Install Python dependencies
RUN pip install --no-cache-dir .

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run the application
ENTRYPOINT ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY}
      - OPENAI_MODEL=${OPENAI_MODEL:-gpt-4o}
      - MAX_FILE_SIZE_MB=${MAX_FILE_SIZE_MB:-100}
    volumes:
      - ./uploads:/app/uploads
    restart: unless-stopped
```

### Build and Run

```bash
# Build the image
docker build -t call-center-grading .

# Run with environment variables
docker run -p 8501:8501 \
  -e OPENAI_API_KEY=sk-your-key \
  -e DEEPGRAM_API_KEY=your-key \
  call-center-grading

# Or use docker-compose
docker-compose up -d
```

### Push to Container Registry

```bash
# Docker Hub
docker tag call-center-grading username/call-center-grading:latest
docker push username/call-center-grading:latest

# AWS ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com
docker tag call-center-grading:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/call-center-grading:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/call-center-grading:latest
```

---

## Railway

Simple cloud deployment with GitHub integration.

### Steps

1. **Create account** at [railway.app](https://railway.app)

2. **Create new project** → "Deploy from GitHub repo"

3. **Connect repository**

4. **Add environment variables**:
   ```
   OPENAI_API_KEY=sk-your-key
   DEEPGRAM_API_KEY=your-key
   ```

5. **Configure build** - Create `railway.toml`:
   ```toml
   [build]
   builder = "nixpacks"

   [deploy]
   startCommand = "streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0"
   healthcheckPath = "/_stcore/health"
   healthcheckTimeout = 300
   ```

6. **Add `Procfile`** (alternative):
   ```
   web: streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0
   ```

7. **Deploy** - Railway auto-deploys on push

---

## Heroku

Classic PaaS deployment option.

### Prerequisites

- Heroku CLI installed
- Heroku account

### Setup Files

Create `Procfile`:
```
web: streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0
```

Create `runtime.txt`:
```
python-3.13.0
```

Create `setup.sh`:
```bash
mkdir -p ~/.streamlit/

echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
\n\
" > ~/.streamlit/config.toml
```

### Deploy

```bash
# Login to Heroku
heroku login

# Create app
heroku create call-center-grading

# Set environment variables
heroku config:set OPENAI_API_KEY=sk-your-key
heroku config:set DEEPGRAM_API_KEY=your-key

# Deploy
git push heroku main

# Open app
heroku open
```

---

## AWS Deployment

Production-grade deployment on AWS.

### Option 1: AWS App Runner (Simplest)

1. **Push Docker image to ECR** (see Docker section)

2. **Create App Runner service**:
   ```bash
   aws apprunner create-service \
     --service-name call-center-grading \
     --source-configuration '{
       "ImageRepository": {
         "ImageIdentifier": "123456789.dkr.ecr.us-east-1.amazonaws.com/call-center-grading:latest",
         "ImageRepositoryType": "ECR"
       }
     }' \
     --instance-configuration '{
       "Cpu": "1024",
       "Memory": "2048"
     }'
   ```

3. **Set environment variables** in AWS Console

### Option 2: ECS Fargate

Create `ecs-task-definition.json`:
```json
{
  "family": "call-center-grading",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "app",
      "image": "ACCOUNT.dkr.ecr.REGION.amazonaws.com/call-center-grading:latest",
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "OPENAI_MODEL", "value": "gpt-4o"}
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:openai-api-key"
        },
        {
          "name": "DEEPGRAM_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:deepgram-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/call-center-grading",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

Deploy:
```bash
# Register task definition
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# Create service
aws ecs create-service \
  --cluster default \
  --service-name call-center-grading \
  --task-definition call-center-grading \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration '{
    "awsvpcConfiguration": {
      "subnets": ["subnet-xxx"],
      "securityGroups": ["sg-xxx"],
      "assignPublicIp": "ENABLED"
    }
  }'
```

### Option 3: EC2 with Docker

```bash
# SSH into EC2 instance
ssh -i key.pem ec2-user@ec2-xxx.compute.amazonaws.com

# Install Docker
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# Run container
docker run -d -p 80:8501 \
  -e OPENAI_API_KEY=sk-xxx \
  -e DEEPGRAM_API_KEY=xxx \
  --restart unless-stopped \
  username/call-center-grading:latest
```

---

## Production Considerations

### Security

1. **Never commit secrets** - Use environment variables or secret managers

2. **Use HTTPS** - Configure SSL/TLS
   ```toml
   # .streamlit/config.toml
   [server]
   enableXsrfProtection = true
   ```

3. **Restrict access** - Add authentication
   ```python
   # Add to app/main.py
   import streamlit_authenticator as stauth

   authenticator = stauth.Authenticate(
       credentials, cookie_name, key, cookie_expiry_days
   )
   ```

4. **API key rotation** - Regularly rotate API keys

### Monitoring

1. **Add logging**:
   ```python
   import logging
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   ```

2. **Health checks** - Streamlit provides `/_stcore/health`

3. **Error tracking** - Consider Sentry:
   ```python
   import sentry_sdk
   sentry_sdk.init(dsn="your-sentry-dsn")
   ```

### Scaling

1. **Horizontal scaling** - Run multiple instances behind load balancer

2. **Caching** - Enable Streamlit caching:
   ```python
   @st.cache_data(ttl=3600)
   def expensive_operation():
       ...
   ```

3. **Rate limiting** - Implement for API protection

### Cost Optimization

| Service | Estimated Cost |
|---------|---------------|
| Streamlit Cloud | Free (Community) |
| Railway | Free tier, then ~$5/month |
| Heroku | Free tier, then ~$7/month |
| AWS App Runner | ~$25/month (always on) |
| AWS Fargate | ~$15/month (on-demand) |

**API costs** (estimate per 100 calls):
- OpenAI GPT-4o: ~$2-5 (depends on transcript length)
- Deepgram: ~$0.50-1 (audio transcription)

### Backup & Recovery

1. **Database** (if added): Regular backups
2. **Configuration**: Store in version control
3. **Secrets**: Use cloud secret managers with versioning

---

## Quick Start Commands

### Streamlit Cloud
```bash
# Just push to GitHub and connect at share.streamlit.io
git push origin main
```

### Docker Local
```bash
docker-compose up -d
```

### Railway
```bash
railway login
railway init
railway up
```

### Heroku
```bash
heroku create && git push heroku main
```

Choose the deployment option that best fits your needs!
