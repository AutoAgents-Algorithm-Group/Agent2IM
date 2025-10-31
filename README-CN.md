<div align="center">

<img src="https://img.shields.io/badge/Agent2IM-000000?style=for-the-badge&labelColor=faf9f6&color=faf9f6&logoColor=000000" alt="Agent2IM" width="280"/>

<h4>通用AI驱动的即时通讯集成平台</h4>

[English](README.md) | 简体中文

<a href="LICENSE">
  <img alt="License GNU" src="https://img.shields.io/badge/License-GNU-yellow.svg?style=for-the-badge" />
</a>

</div>

基于AutoAgents和FastAPI构建的企业级AI驱动消息平台，无缝集成AutoAgents智能技术到多个即时通讯平台，包括飞书、企业微信和钉钉。让AI智能对话在您团队沟通的每个角落都能发挥作用，全面转型团队协作体验。

## 目录
- [目录](#目录)
- [为什么选择Agent2IM？](#为什么选择agent2im)
- [支持的平台](#支持的平台)
- [快速开始](#快速开始)
- [部署](#部署)
- [平台集成](#平台集成)
  - [飞书集成](#飞书集成)
  - [企业微信集成](#企业微信集成)
  - [钉钉集成](#钉钉集成)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## 为什么选择Agent2IM？

Agent2IM是一个革命性的企业AI助手解决方案，将先进的AutoAgents AI技术无缝集成到多个即时通讯平台中。它不仅仅是一个多平台聊天机器人，更是整个组织的统一AI生产力倍增器。

- **🌐 多平台支持**：在飞书、企业微信和钉钉上提供统一的AI体验
- **🚀 即开即用**：5分钟完成部署，立即体验AI助手服务
- **🧠 智能对话**：基于AutoAgents提供上下文感知的高质量AI回复
- **⚡ 高性能**：FastAPI + 异步处理，支持高并发场景
- **🔧 易维护**：模块化设计，清晰的代码结构，易于扩展和维护  
- **🐳 容器化**：完整的Docker支持，一键部署到生产环境
- **📊 企业级**：多平台、多群组支持，权限控制，满足企业使用需求
- **🔄 动态路由**：智能webhook路由允许不同团队使用不同的AI代理

## 支持的平台

| 平台 | 状态 | 功能特性 |
|----------|--------|----------|
| **飞书** | ✅ **完全支持** | 群聊@提及、实时打字效果、交互式卡片、会话管理 |
| **企业微信** | 🚧 **开发中** | 即将推出 |
| **钉钉** | 🚧 **开发中** | 即将推出 |

## 快速开始

**环境要求**
- Python 3.11+
- Docker & Docker Compose（推荐）
- 至少一个支持的即时通讯平台账号：
  - 飞书开放平台账号（用于飞书集成）
  - 企业微信账号（用于企业微信集成）*即将推出*
  - 钉钉开放平台账号（用于钉钉集成）*即将推出*

**立即开始**
```bash
# 1. 克隆项目
git clone https://github.com/AutoAgents-Algorithm-Group/Agent2IM.git
cd Agent2IM

# 2. 启动服务（无需配置文件！）
cd docker
docker-compose up -d

# 3. 配置webhook URL到您的即时通讯平台
# URL格式: https://your-domain.com/feishu/webhook/{agent_id}-{auth_key}-{auth_secret}/{app_id}-{app_secret}
```

## 部署

**Docker**
```bash
cd Agent2IM

# 直接启动服务（无需配置文件！）
cd docker
docker-compose up -d
```

**故障排除**
```bash
# 查看应用日志
docker compose -f docker/docker-compose.yml logs -f app

# 停止并移除容器
docker compose -f docker/docker-compose.yml down

# 重新构建并启动
docker compose -f docker/docker-compose.yml up -d --build
```

## 平台集成

### 飞书集成

**1. 创建飞书应用**
1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 创建企业自建应用
3. 获取 `App ID` 和 `App Secret`

**2. 配置应用权限**
添加以下必需权限：
- `im:message` - 读取用户消息
- `im:message.group_at_msg` - 获取群组消息
- `im:message:send_as_bot` - 发送消息

**3. 设置事件订阅**
- 启用事件订阅
- 设置请求网址：`https://your-domain.com/feishu/webhook/{agent_id}-{auth_key}-{auth_secret}/{app_id}-{app_secret}`
- 订阅事件：`im.message.receive_v1`

**4. 配置机器人**
- 启用机器人功能
- 设置机器人信息
- 发布版本

### 企业微信集成

🚧 **即将推出** - 企业微信集成正在开发中。

**计划功能：**
- 群聊支持
- @提及功能
- 丰富消息卡片
- 企业级安全

### 钉钉集成

🚧 **即将推出** - 钉钉集成正在开发中。

**计划功能：**
- 群聊支持
- @提及功能
- 交互式卡片
- 企业应用集成


## 贡献指南

我们欢迎所有形式的贡献！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目基于 MIT 许可证开源 - 查看 [LICENSE](LICENSE) 文件了解详情。