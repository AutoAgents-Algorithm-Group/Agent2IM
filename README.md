<div align="center">

<img src="https://img.shields.io/badge/Agent2IM-000000?style=for-the-badge&labelColor=faf9f6&color=faf9f6&logoColor=000000" alt="Feishu" width="280"/>

<h4>Universal AI-Powered Instant Messaging Integration Platform</h4>

English | [简体中文](README-CN.md)

<a href="LICENSE">
  <img alt="License GNU" src="https://img.shields.io/badge/License-GNU-yellow.svg?style=for-the-badge" />
</a>

</div>

An enterprise-grade AI-powered messaging platform that seamlessly integrates AutoAgents intelligence across multiple instant messaging platforms including Feishu, WeChat Enterprise, and DingTalk. Transform your team collaboration with intelligent AI conversations that work everywhere your team communicates.

## Table of Contents
- [Table of Contents](#table-of-contents)
- [Why Choose Agent2IM?](#why-choose-agent2im)
- [Supported Platforms](#supported-platforms)
- [Quick Start](#quick-start)
- [Deployment](#deployment)
- [Platform Integration](#platform-integration)
  - [Feishu Integration](#feishu-integration)
  - [WeChat Enterprise Integration](#wechat-enterprise-integration)
  - [DingTalk Integration](#dingtalk-integration)
- [Contributing](#contributing)
- [License](#license)

## Why Choose Agent2IM?

Agent2IM is a revolutionary enterprise AI assistant solution that seamlessly integrates advanced AutoAgents AI technology across multiple instant messaging platforms. It's not just a multi-platform chatbot, but a unified AI productivity multiplier for your entire organization.

- **🌐 Multi-Platform**: Unified AI experience across Feishu, WeChat Enterprise, and DingTalk
- **🚀 Ready to Use**: Deploy in 5 minutes and start experiencing AI assistant services immediately
- **🧠 Intelligent Conversations**: Context-aware, high-quality AI responses powered by AutoAgents
- **⚡ High Performance**: FastAPI + async processing, supporting high-concurrency scenarios
- **🔧 Easy Maintenance**: Modular design with clear code structure, easy to extend and maintain
- **🐳 Containerized**: Full Docker support for one-click deployment to production
- **📊 Enterprise-Grade**: Multi-platform, multi-group support with permission control for enterprise needs
- **🔄 Dynamic Routing**: Smart webhook routing allows different AI agents for different teams

## Supported Platforms

| Platform | Status | Features |
|----------|--------|----------|
| **Feishu** | ✅ **Fully Supported** | Group chat @mentions, Real-time typing, Interactive cards, Session management |
| **WeChat Enterprise** | 🚧 **In Development** | Coming soon |
| **DingTalk** | 🚧 **In Development** | Coming soon |

## Quick Start

**Requirements**
- Python 3.11+
- Docker & Docker Compose (recommended)
- At least one supported IM platform account:
  - Feishu Open Platform account (for Feishu integration)
  - WeChat Work account (for WeChat Enterprise integration) *Coming Soon*
  - DingTalk Open Platform account (for DingTalk integration) *Coming Soon*

**Get Started**
```bash
# 1. Clone the project
git clone https://github.com/AutoAgents-Algorithm-Group/Agent2IM.git
cd Agent2IM

# 2. Start services (no configuration file needed!)
cd docker
docker-compose up -d

# 3. Configure webhook URL in your IM platform
# URL format: https://your-domain.com/feishu/webhook/{agent_id}-{auth_key}-{auth_secret}/{app_id}-{app_secret}
```

## Deployment

**Docker**
```bash
cd Agent2IM

# Start services directly (no configuration file needed!)
cd docker
docker-compose up -d
```

**Troubleshooting**
```bash
# View application logs
docker compose -f docker/docker-compose.yml logs -f app

# Stop and remove containers
docker compose -f docker/docker-compose.yml down

# Rebuild and restart
docker compose -f docker/docker-compose.yml up -d --build
```

## Platform Integration

### Feishu Integration

**1. Create Feishu Application**
1. Visit [Feishu Open Platform](https://open.feishu.cn/)
2. Create an enterprise self-built application
3. Get `App ID` and `App Secret`

**2. Configure Application Permissions**
Add the following required permissions:
- `im:message` - Read user messages
- `im:message.group_at_msg` - Get group messages
- `im:message:send_as_bot` - Send messages

**3. Set Event Subscription**
- Enable event subscription
- Set request URL: `https://your-domain.com/feishu/webhook/{agent_id}-{auth_key}-{auth_secret}/{app_id}-{app_secret}`
- Subscribe to event: `im.message.receive_v1`

**4. Configure Bot**
- Enable bot functionality
- Set bot information
- Publish version

### WeChat Enterprise Integration

🚧 **Coming Soon** - WeChat Enterprise integration is under development.

**Planned Features:**
- Group chat support
- @mentions functionality
- Rich message cards
- Enterprise-grade security

### DingTalk Integration

🚧 **Coming Soon** - DingTalk integration is under development.

**Planned Features:**
- Group chat support
- @mentions functionality
- Interactive cards
- Enterprise application integration

## Contributing

We welcome all forms of contributions!

1. Fork the project
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.