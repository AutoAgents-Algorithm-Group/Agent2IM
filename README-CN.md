<div align="center">

<img src="https://img.shields.io/badge/-Feishu-000000?style=for-the-badge&labelColor=faf9f6&color=faf9f6&logoColor=000000" alt="Feishu" width="280"/>

<h4>基于AutoAgents的智能飞书机器人</h4>

[English](README.md) | 简体中文

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/License-MIT-white.svg?style=flat-square" />
  <img alt="License MIT" src="https://img.shields.io/badge/License-MIT-black.svg?style=flat-square" />
</picture>

</div>

基于AutoAgents和FastAPI构建的企业级飞书AI机器人，为团队协作注入智能化体验。支持群聊@机器人进行AI对话，提供高质量的智能问答服务。

## 目录
- [目录](#目录)
- [为什么选择飞书AI机器人？](#为什么选择飞书ai机器人)
- [快速开始](#快速开始)
- [部署](#部署)
- [项目结构](#项目结构)
- [配置](#配置)
- [飞书集成](#飞书集成)
- [开发指南](#开发指南)
- [故障排除](#故障排除)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## 为什么选择飞书AI机器人？

飞书AI机器人是一个革命性的企业AI助手解决方案，将先进的AI技术无缝集成到飞书协作平台中。它不仅仅是一个聊天机器人，更是团队效率的倍增器。

- **🚀 即开即用**：5分钟完成部署，立即体验AI助手服务
- **🧠 智能对话**：基于AutoAgents提供上下文感知的高质量AI回复
- **⚡ 高性能**：FastAPI + 异步处理，支持高并发场景
- **🔧 易维护**：模块化设计，清晰的代码结构，易于扩展和维护  
- **🐳 容器化**：完整的Docker支持，一键部署到生产环境
- **📊 企业级**：支持多群组、权限控制，满足企业使用需求

## 快速开始

**环境要求**
- Python 3.11+
- Docker & Docker Compose（推荐）
- 飞书开放平台账号

**立即开始**
```bash
# 1. 克隆项目
git clone https://github.com/your-repo/feishu-ai-bot.git
cd feishu-ai-bot

# 2. 配置环境
cp src/config/config.yaml.example src/config/config.yaml
# 编辑config.yaml填入您的配置

# 3. 启动服务
cd docker
docker-compose up -d

# 4. 测试系统
cd ..
python playground/test.py
```

**本地开发**
```bash
# 安装依赖
pip install -r src/requirements.txt

# 启动开发服务器
python src/API/main.py
```

## 部署

**Docker 部署（推荐）**
```bash
cd feishu-ai-bot

# 编辑配置
nano src/config/config.yaml

# 启动服务
cd docker
docker-compose up -d
```

**生产环境部署**
```bash
# 部署到服务器
git clone https://github.com/your-repo/feishu-ai-bot.git /opt/feishu-bot
cd /opt/feishu-bot

# 配置环境
nano src/config/config.yaml

# 启动服务
cd docker
docker-compose up -d

# 查看日志
docker-compose logs -f
```

**故障排除**
```bash
# 查看应用日志
docker-compose logs -f feishu-bot

# 重启服务
docker-compose restart feishu-bot

# 完全重新部署
docker-compose down
docker-compose up -d --build
```

## 项目结构

```
├── src/                          # 源代码目录
│   ├── API/                      # FastAPI应用层
│   │   └── main.py              # API主入口
│   ├── config/                   # 配置管理
│   │   ├── config.yaml          # 配置文件
│   │   └── config_manager.py    # 配置管理器
│   ├── service/                  # 服务层
│   │   ├── autoagents_service.py # AI服务
│   │   └── feishu_service.py    # 飞书服务
│   └── requirements.txt         # Python依赖
├── docker/                      # Docker部署文件
│   ├── Dockerfile              # 镜像构建文件
│   └── docker-compose.yml      # 容器编排配置
├── playground/                  # 测试文件
│   └── test.py                 # 系统测试脚本
└── README.md                   # 项目说明文档
```

## 配置

编辑 `src/config/config.yaml` 文件：

```yaml
# 飞书应用配置
feishu:
  FEISHU_APP_ID: "your_app_id"
  FEISHU_APP_SECRET: "your_app_secret"

# AutoAgents AI服务配置
autoagents:
  AUTOAGENTS_AGENT_ID: "your_agent_id" 
  AUTOAGENTS_AUTH_KEY: "your_auth_key"
  AUTOAGENTS_AUTH_SECRET: "your_auth_secret"
```

## 飞书集成

### 1. 创建飞书应用
1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 创建企业自建应用
3. 获取 `App ID` 和 `App Secret`

### 2. 配置应用权限
添加以下必需权限：
- `im:message.p2p_msg:readonly` - 读取用户发给机器人的单聊消息
- `im:message.group_at_msg:readonly` - 接收群聊中@机器人消息事件
- `im:message:send_as_bot` - 以应用的身份发送消息

### 3. 设置事件订阅
- 启用事件订阅
- 设置请求网址：`https://your-domain.com/feishu/webhook`
- 订阅事件：`im.message.receive_v1`

### 4. 配置机器人
- 启用机器人功能
- 设置机器人信息
- 发布版本

## 开发指南

**API端点**
- `GET /` - 服务状态
- `POST /feishu/webhook` - 飞书消息回调

**使用方法**
1. 邀请机器人到飞书群聊
2. 使用 `@机器人 您的问题` 进行对话
3. 机器人自动回复AI生成的答案

**扩展开发**
```bash
# 添加新功能到服务层
nano src/service/your_new_service.py

# 添加API端点
nano src/API/main.py

# 运行测试
python playground/test.py
```

## 故障排除

**常见问题**

1. **机器人无响应**
   ```bash
   # 检查服务状态
   curl http://localhost:9000/
   
   # 查看日志
   docker-compose logs -f feishu-bot
   ```

2. **配置错误**
   ```bash
   # 验证配置
   python -c "from src.config.config_manager import ConfigManager; print(ConfigManager().get_config())"
   ```

3. **AI服务异常**
   ```bash
   # 测试AI服务
   python playground/test.py
   ```

## 贡献指南

我们欢迎所有形式的贡献！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

**开发规范**
- 遵循PEP 8代码规范
- 添加必要的注释和文档
- 确保所有测试通过

## 许可证

本项目基于 MIT 许可证开源 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

<div align="center">
<p>由 ❤️ 和 AI 驱动</p>
<p>如有问题，请提交 <a href="https://github.com/your-repo/feishu-ai-bot/issues">Issue</a></p>
</div>