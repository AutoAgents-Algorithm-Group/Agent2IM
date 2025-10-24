# Agent2IM Backend

通用AI驱动的即时通讯集成平台后端服务

## 📁 目录结构

```
backend/
├── config/                          # 配置文件目录
│   ├── message.json                 # 消息模板配置
│   ├── people.json                  # 人员配置
│   ├── task.json                    # 任务配置
│   ├── news.yml                     # 新闻服务配置
│   ├── labor_hour.json              # 工时检查配置
│   └── scheduled_tasks.json         # 统一定时任务配置
├── router/                          # API路由
│   └── main.py                      # 主应用入口
├── service/                         # 业务服务
│   ├── news_service.py              # 新闻采集和推送服务
│   ├── labor_hour_service.py        # 工时检查服务
│   ├── autoagents_service.py        # AutoAgents服务
│   ├── dingtalk_service.py          # 钉钉服务
│   └── wechat_service.py            # 微信服务
├── utils/                           # 工具类
│   ├── feishu/                      # 飞书相关工具
│   ├── schedule/                    # 定时任务
│   │   ├── scheduler.py             # 原有的提醒调度器
│   │   └── unified_scheduler.py     # 新的统一调度器
│   ├── scrapers/                    # 新闻爬虫
│   │   ├── techcrunch_scraper.py
│   │   ├── verge_scraper.py
│   │   ├── github_trending_scraper.py
│   │   ├── product_hunt_scraper.py
│   │   ├── a16z_scraper.py
│   │   └── kr36_scraper.py
│   └── news/                        # 新闻工具
│       ├── config_manager.py        # 配置管理器
│       └── database.py              # 数据库操作
└── playground/                      # 测试和手动执行脚本
    ├── run_news_manually.py         # 手动执行新闻推送
    ├── run_labor_hour_check.py      # 手动执行工时检查
    └── start_unified_scheduler.py   # 启动统一调度器
```

## 🚀 功能模块

### 1. 新闻采集和推送服务

自动从多个来源采集AI相关新闻，通过AI翻译和总结后，推送到飞书群组。

**支持的新闻源：**
- TechCrunch
- The Verge
- GitHub Trending
- Product Hunt
- Andreessen Horowitz (a16z)
- 36氪

**配置文件：** `config/news.yml`

**手动执行：**
```bash
cd backend/playground
python run_news_manually.py
```

**定时任务：** 每天早上9点自动推送

### 2. 工时检查服务

检查飞书多维表格中的工时填写情况，自动推送提醒消息到群组。

**配置文件：** `config/labor_hour.json`

**手动执行：**
```bash
cd backend/playground
python run_labor_hour_check.py
```

**定时任务：**
- 晚上9点：第一次检查提醒
- 晚上11点：第二次检查提醒
- 早上10点：检查昨天的补填提醒

### 3. 统一定时任务调度器

整合新闻推送和工时检查的定时任务调度器。

**配置文件：** `config/scheduled_tasks.json`

**独立启动：**
```bash
cd backend/playground
python start_unified_scheduler.py
```

**随API服务启动：**
```bash
# 设置环境变量启用统一调度器
export USE_UNIFIED_SCHEDULER=true
cd backend/router
python main.py
```

## ⚙️ 配置说明

### 新闻服务配置 (`config/news.yml`)

```yaml
# 飞书机器人配置（支持多个群组）
lark:
  primary:
    api_url: "https://open.feishu.cn/open-apis/bot/v2/hook/..."
    api_secret: "your_secret"
    name: "主群组"
  secondary:
    api_url: "https://open.feishu.cn/open-apis/bot/v2/hook/..."
    api_secret: "your_secret"
    name: "备用群组"

# AutoAgents AI 配置
apis:
  autoagentsai:
    ai_agent:
      agent_id: "your_agent_id"
      personal_auth_key: "your_key"
      personal_auth_secret: "your_secret"

# Supabase 数据库配置
supabase:
  url: "https://your-project.supabase.co"
  anon_key: "your_anon_key"

# 数据库表配置
database:
  table_name: "ai_news"
```

### 工时检查配置 (`config/labor_hour.json`)

```json
{
  "feishu": {
    "app_id": "cli_your_app_id",
    "app_secret": "your_app_secret"
  },
  "bitable": {
    "url": "https://your-company.feishu.cn/base/xxx?table=xxx&view=xxx"
  },
  "webhook": {
    "url": "https://open.feishu.cn/open-apis/bot/v2/hook/...",
    "secret": "your_webhook_secret"
  }
}
```

### 统一定时任务配置 (`config/scheduled_tasks.json`)

```json
{
  "timezone": "Asia/Shanghai",
  "tasks": [
    {
      "id": "news_daily",
      "name": "每日AI新闻推送",
      "type": "news",
      "enabled": true,
      "schedule": "09:00"
    },
    {
      "id": "labor_evening_first",
      "name": "工时检查 - 晚上9点",
      "type": "labor_hour",
      "enabled": true,
      "schedule": "21:00"
    }
  ]
}
```

## 🔧 部署方式

### 方式1：作为独立调度器运行

适用于只需要定时任务功能的场景。

```bash
cd backend/playground
python start_unified_scheduler.py
```

### 方式2：随API服务启动

适用于需要API和定时任务功能的场景。

```bash
# 使用统一调度器（新功能）
export USE_UNIFIED_SCHEDULER=true
cd backend/router
uvicorn main:app --host 0.0.0.0 --port 9000

# 或使用原有的提醒调度器
cd backend/router
uvicorn main:app --host 0.0.0.0 --port 9000
```

### 方式3：Docker部署

```bash
cd docker
docker-compose up -d
```

## 📝 API接口

### 查看调度器状态
```
GET /scheduler/status
```

### 查看所有定时任务
```
GET /scheduler/jobs
```

### 飞书消息回调
```
POST /feishu/webhook/{agent_id}-{auth_key}-{auth_secret}/{app_id}-{app_secret}
```

## 🔄 迁移说明

从 Poseidon 项目迁移的内容：

1. **Scrapers**: `Poseidon/backend/scraper/` → `backend/utils/scrapers/`
2. **Config Utils**: `Poseidon/backend/config/` → `backend/utils/news/`
3. **Agents**: `Poseidon/backend/agents/` → `backend/service/news_service.py`
4. **Config File**: `Poseidon/backend/config.yml` → `backend/config/news.yml`

## 📦 依赖安装

```bash
pip install -r requirements.txt
```

主要依赖：
- fastapi
- uvicorn
- apscheduler
- requests
- beautifulsoup4
- lxml
- supabase
- autoagentsai
- pyyaml

## 🛠️ 开发和测试

### 测试新闻推送
```bash
cd backend/playground
python run_news_manually.py
```

### 测试工时检查
```bash
cd backend/playground
python run_labor_hour_check.py
```

### 测试定时任务
```bash
cd backend/playground
python start_unified_scheduler.py
```

## 📚 更多文档

- [API文档](./playground/test_api.http)
- [Bitable使用说明](./playground/test_bitable.py)
- [调度器说明](./playground/test_scheduler.py)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

MIT License



