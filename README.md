<div align="center">

<img src="https://img.shields.io/badge/-Feishu-000000?style=for-the-badge&labelColor=faf9f6&color=faf9f6&logoColor=000000" alt="Feishu" width="280"/>

<h4>Intelligent Feishu Bot Powered by AutoAgents</h4>

English | [简体中文](README-CN.md)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/License-MIT-white.svg?style=flat-square" />
  <img alt="License MIT" src="https://img.shields.io/badge/License-MIT-black.svg?style=flat-square" />
</picture>

</div>

An enterprise-grade intelligent Feishu bot built with AutoAgents and FastAPI, bringing AI-powered conversations to your team collaboration. Support group chat @mentions for seamless AI interactions.

## Table of Contents
- [Table of Contents](#table-of-contents)
- [Why Choose Feishu AI Bot?](#why-choose-feishu-ai-bot)
- [Quick Start](#quick-start)
- [Deployment](#deployment)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Feishu Integration](#feishu-integration)
- [Development Guide](#development-guide)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Why Choose Feishu AI Bot?

Feishu AI Bot is a revolutionary enterprise AI assistant solution that seamlessly integrates advanced AI technology into the Feishu collaboration platform. It's not just a chatbot, but a productivity multiplier for your team.

- **🚀 Ready to Use**: Deploy in 5 minutes and start experiencing AI assistant services immediately
- **🧠 Intelligent Conversations**: Context-aware, high-quality AI responses powered by AutoAgents
- **⚡ High Performance**: FastAPI + async processing, supporting high-concurrency scenarios
- **🔧 Easy Maintenance**: Modular design with clear code structure, easy to extend and maintain
- **🐳 Containerized**: Full Docker support for one-click deployment to production
- **📊 Enterprise-Grade**: Multi-group support with permission control for enterprise needs

## Quick Start

**Requirements**
- Python 3.11+
- Docker & Docker Compose (recommended)
- Feishu Open Platform account

**Get Started**
```bash
# 1. Clone the project
git clone https://github.com/your-repo/feishu-ai-bot.git
cd feishu-ai-bot

# 2. Configure environment
cp src/config/config.yaml.example src/config/config.yaml
# Edit config.yaml with your credentials

# 3. Start services
cd docker
docker-compose up -d

# 4. Test system
cd ..
python playground/test.py
```

**Local Development**
```bash
# Install dependencies
pip install -r src/requirements.txt

# Start development server
python src/API/main.py
```

## Deployment

**Docker Deployment (Recommended)**
```bash
cd feishu-ai-bot

# Edit configuration
nano src/config/config.yaml

# Start services
cd docker
docker-compose up -d
```

**Production Deployment**
```bash
# Deploy to server
git clone https://github.com/your-repo/feishu-ai-bot.git /opt/feishu-bot
cd /opt/feishu-bot

# Configure environment
nano src/config/config.yaml

# Start services
cd docker
docker-compose up -d

# View logs
docker-compose logs -f
```

**Troubleshooting**
```bash
# View application logs
docker-compose logs -f feishu-bot

# Restart services
docker-compose restart feishu-bot

# Complete redeployment
docker-compose down
docker-compose up -d --build
```

## Project Structure

```
├── src/                          # Source code directory
│   ├── API/                      # FastAPI application layer
│   │   └── main.py              # API main entry
│   ├── config/                   # Configuration management
│   │   ├── config.yaml          # Configuration file
│   │   └── config_manager.py    # Configuration manager
│   ├── service/                  # Service layer
│   │   ├── autoagents_service.py # AI service
│   │   └── feishu_service.py    # Feishu service
│   └── requirements.txt         # Python dependencies
├── docker/                      # Docker deployment files
│   ├── Dockerfile              # Image build file
│   └── docker-compose.yml      # Container orchestration config
├── playground/                  # Test files
│   └── test.py                 # System test script
└── README.md                   # Project documentation
```

## Configuration

Edit `src/config/config.yaml` file:

```yaml
# Feishu application configuration
feishu:
  FEISHU_APP_ID: "your_app_id"
  FEISHU_APP_SECRET: "your_app_secret"

# AutoAgents AI service configuration
autoagents:
  AUTOAGENTS_AGENT_ID: "your_agent_id" 
  AUTOAGENTS_AUTH_KEY: "your_auth_key"
  AUTOAGENTS_AUTH_SECRET: "your_auth_secret"
```

## Feishu Integration

### 1. Create Feishu Application
1. Visit [Feishu Open Platform](https://open.feishu.cn/)
2. Create an enterprise self-built application
3. Get `App ID` and `App Secret`

### 2. Configure Application Permissions
Add the following required permissions:
- `im:message` - Read user messages
- `im:message.group_at_msg` - Get group messages
- `im:message:send_as_bot` - Send messages

### 3. Set Event Subscription
- Enable event subscription
- Set request URL: `https://your-domain.com/feishu/webhook`
- Subscribe to event: `im.message.receive_v1`

### 4. Configure Bot
- Enable bot functionality
- Set bot information
- Publish version

## Development Guide

**API Endpoints**
- `GET /` - Service status
- `POST /feishu/webhook` - Feishu message callback

**Usage**
1. Invite bot to Feishu group chat
2. Use `@bot Your question` to interact
3. Bot automatically replies with AI-generated answers

**Extension Development**
```bash
# Add new functionality to service layer
nano src/service/your_new_service.py

# Add API endpoints
nano src/API/main.py

# Run tests
python playground/test.py
```

## Troubleshooting

**Common Issues**

1. **Bot Not Responding**
   ```bash
   # Check service status
   curl http://localhost:9000/
   
   # View logs
   docker-compose logs -f feishu-bot
   ```

2. **Configuration Errors**
   ```bash
   # Verify configuration
   python -c "from src.config.config_manager import ConfigManager; print(ConfigManager().get_config())"
   ```

3. **AI Service Issues**
   ```bash
   # Test AI service
   python playground/test.py
   ```

## Contributing

We welcome all forms of contributions!

1. Fork the project
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Create a Pull Request

**Development Standards**
- Follow PEP 8 coding standards
- Add necessary comments and documentation
- Ensure all tests pass

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
<p>Powered by ❤️ and AI</p>
<p>For questions, please submit an <a href="https://github.com/your-repo/feishu-ai-bot/issues">Issue</a></p>
</div>
