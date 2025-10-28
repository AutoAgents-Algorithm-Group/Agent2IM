# 配置文件说明

本项目使用 YAML 格式的配置文件，主要包含三个配置文件：
- `labor_hour.yaml` - 工时检查服务配置
- `approval.yaml` - 审批服务配置
- `news.yaml` - AI新闻推送服务配置

---

## 工时检查服务配置 (`labor_hour.yaml`)

### 📋 配置项说明

#### 1. 飞书应用配置 (`feishu`)

统一使用飞书应用完成所有功能：
- 读取多维表格数据
- 发送群消息（替代 webhook）
- 获取群成员列表

**必需权限**：
- `bitable:app` - 读取多维表格
- `im:message` - 发送消息
- `im:chat.member` - 读取群成员列表
- `approval` - 读取审批记录（可选，用于请假检测）

```yaml
feishu:
  app_id: "cli_xxxxxxxxxxxxx"
  app_secret: "xxxxxxxxxxxxx"
  leave_approval_code: "A9D489DC-5F55-4418-99F1-01E1CE734CA1"  # 可选
```

#### 2. 多维表格配置 (`bitable`)

工时数据存储的多维表格 URL：

```yaml
bitable:
  url: "https://your-company.feishu.cn/base/UfDPbov0Eai3RpsWAEBcyfe1nAb?table=tbla3OuZeDczpqZx&view=vewGyZRz6D"
```

#### 3. 群聊配置 (`group_chat`)

用于发送消息、获取群成员列表以及管理例外规则：

```yaml
group_chat:
  chat_id: "oc_f4af22a11abbc9b68034b1b639a32cd7"
  # 排除成员 - 这些人完全不参与工时检查
  exclude_members:
    - "邹阳"
    - "杨劲松"
    - "高乐奇"
    - "邹鹏飞"
    - "张建全"
  # 例外日期配置 - 某些人在特定星期几不需要填写工时
  exceptions:
    滕凯:
      - "星期二"
```

**配置说明**：
- `chat_id`: 群聊ID（必需）
- `exclude_members`: 完全排除的成员列表（可选）
- `exceptions`: 特定日期例外规则（可选）

#### 4. 定时任务配置 (`schedules`)

配置工时检查和月报的定时任务：

```yaml
schedules:
  timezone: "Asia/Shanghai"
  
  tasks:
    # 工作日晚上 19:30 检查当天工时
    - id: "labor_evening_check"
      name: "工时检查 - 晚上19:30"
      type: "labor_hour"
      enabled: true
      schedule: "19:30"
      offset: 0  # 0=今天, -1=昨天, 1=明天
      description: "工作日晚上19:30检查当天工时填写情况"
    
    # 第二天早上 10:30 提醒昨天未填写的
    - id: "labor_morning_makeup"
      name: "工时检查 - 早上10:30补填提醒"
      type: "labor_hour"
      enabled: true
      schedule: "10:30"
      offset: -1
      description: "第二天早上10:30提醒昨天未填写的"
    
    # 每月 28 号上午 10:00 发送月报
    - id: "labor_month_summary"
      name: "工时月报 - 每月28号"
      type: "labor_month_summary"
      enabled: true
      schedule: "cron"
      cron: "0 10 28 * *"
      mention_users:
        - "刘华鑫"
      description: "每月28号总结过去一个月的工时填写情况"
```

### 📝 配置步骤

#### 步骤 1: 创建飞书应用

1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 创建企业自建应用
3. 添加权限：
   - `bitable:app` - 读取多维表格
   - `im:message` - 发送消息
   - `im:chat.member` - 读取群成员
   - `approval` - 读取审批（可选）
4. 获取 `app_id` 和 `app_secret`

#### 步骤 2: 将应用添加到群聊

1. 打开目标飞书群聊
2. 群设置 → 群机器人 → 添加机器人
3. 选择你创建的应用

#### 步骤 3: 获取群聊 chat_id

方法 1 - 通过开发者工具：
```bash
# 使用飞书 API 获取群列表
curl -X GET "https://open.feishu.cn/open-apis/im/v1/chats" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

方法 2 - 在代码中打印：
```python
from src.utils.feishu.message import MessageAPI
msg_api = MessageAPI(feishu_client)
# 发送消息时打印 chat_id
```

#### 步骤 4: 复制多维表格 URL

1. 打开你的工时填写表格
2. 复制浏览器地址栏的完整 URL
3. 确保 URL 包含 `base`、`table`、`view` 三个参数

#### 步骤 5: 填写配置文件

创建 `backend/src/config/labor_hour.yaml`：

```yaml
feishu:
  app_id: "cli_xxxxxxxxxxxxx"
  app_secret: "xxxxxxxxxxxxx"

bitable:
  url: "https://your-table-url"

group_chat:
  chat_id: "oc_xxxxxxxxxxxxx"
  exclude_members:
    - "邹阳"
    - "杨劲松"
  exceptions:
    滕凯:
      - "星期二"

schedules:
  timezone: "Asia/Shanghai"
  tasks:
    - id: "labor_evening_check"
      name: "工时检查 - 晚上19:30"
      type: "labor_hour"
      enabled: true
      schedule: "19:30"
      offset: 0
    - id: "labor_morning_makeup"
      name: "工时检查 - 早上10:30补填提醒"
      type: "labor_hour"
      enabled: true
      schedule: "10:30"
      offset: -1
    - id: "labor_month_summary"
      name: "工时月报 - 每月28号"
      type: "labor_month_summary"
      enabled: true
      schedule: "cron"
      cron: "0 10 28 * *"
      mention_users:
        - "刘华鑫"
```

#### 步骤 6: 测试

```bash
cd backend/playground/service/feishu
python test_labor_hour_daily.py
```

---

## 审批服务配置 (`approval.yaml`)

### 📋 配置项说明

审批服务用于监听飞书审批事件，自动创建请假日历。

```yaml
# 飞书应用配置
feishu:
  app_id: "cli_xxxxxxxxxxxxx"
  app_secret: "xxxxxxxxxxxxx"

# 审批定义编码配置
# 只有在此白名单中的审批类型才会被处理
approval_codes:
  # 请假审批列表
  leave:
    - "A9D489DC-5F55-4418-99F1-01E1CE734CA1"  # HR小助手 - 请假申请
  
  # 其他类型审批（预留）
  # overtime:
  #   - "XXXXX"  # 加班审批

# 日历配置（可选）
calendar:
  enabled: true  # 是否自动创建日历事件
  event:
    title_template: "{user_name} - 请假"
    color: 7  # 淡蓝色
```

### 📝 配置步骤

1. **创建飞书应用** - 需要 `approval:approval` 和 `calendar:calendar` 权限
2. **配置审批回调 URL** - 在飞书后台设置事件回调地址
3. **获取审批定义编码** - 在审批管理后台查看审批定义的编码
4. **添加到白名单** - 将需要处理的审批编码添加到 `approval_codes`

### 🧪 测试

```bash
cd backend/playground/service/feishu
python test_approval.py
```

---

## AI新闻推送服务配置 (`news.yaml`)

### 📋 配置项说明

```yaml
# 飞书机器人配置（支持多个群组）
lark:
  primary:
    api_url: "https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx"
    api_secret: "xxxxx"
    name: "主群组"
  
  secondary:
    api_url: "https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx"
    api_secret: "xxxxx"
    name: "备用群组"

# AutoAgents AI 配置
apis:
  autoagentsai:
    ai_agent:
      agent_id: "xxxxx"
      personal_auth_key: "xxxxx"
      personal_auth_secret: "xxxxx"

# Supabase 数据库配置
supabase:
  url: "https://xxxxx.supabase.co"
  anon_key: "xxxxx"

database:
  table_name: "ai_news"

# 定时任务配置
schedules:
  timezone: "Asia/Shanghai"
  tasks:
    - id: "news_daily"
      name: "每日AI新闻推送"
      type: "news"
      enabled: false
      schedule: "09:00"
      description: "每天早上9点推送AI新闻"
```

---

## 🔐 安全建议

- ⚠️ **不要将配置文件提交到 Git**
- ⚠️ App Secret 和 API Secret 要妥善保管
- ⚠️ 定期轮换密钥
- ✅ 使用环境变量存储敏感信息（生产环境）

---

## 💡 常见问题

### Q: 为什么不再使用 people.json？
A: 现在直接从飞书群成员 API 获取人员列表，更准确且无需手动维护。

### Q: 为什么不再使用 webhook？
A: 统一使用飞书应用发送消息，支持更丰富的功能（如 @提醒）。

### Q: 如何手动测试配置是否正确？
A: 运行测试脚本：
```bash
cd backend/playground/service/feishu
python test_labor_hour_daily.py
python test_labor_hour_monthly.py
```

---

如有其他疑问，请查看 [Backend README](../README.md) 或提交 Issue。
