# API接口测试文档

## 🚀 快速开始

### 1. 启动API服务

```bash
cd /Users/forhheart/AIGC/Agent2IM
python backend/api/main.py
```

服务将在 `http://localhost:9000` 启动

### 2. 测试API接口

使用 VS Code REST Client 插件打开 `test_api.http` 文件，点击接口上方的 "Send Request" 按钮。

---

## 📋 API接口说明

### 工时检查接口

**接口地址:**
```
GET /feishu/labor_hour/{app_id}-{app_secret}/{group_chat_id}/{bitable_url}
```

**参数说明:**

| 参数 | 位置 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `app_id` | Path | ✅ | 飞书应用ID | `cli_a82e97f4de29501c` |
| `app_secret` | Path | ✅ | 飞书应用密钥 | `nEoauWe1YEt5luG6J4Ij8cvlTZKb3po3` |
| `group_chat_id` | Path | ✅ | 飞书群聊ID | `oc_xxxxxxxxxxxxx` |
| `bitable_url` | Path | ✅ | 多维表格完整URL | `https://xxx.feishu.cn/base/xxx?table=xxx&view=xxx` |
| `date` | Query | ❌ | 检查日期（YYYY-MM-DD） | `2025-09-30` |

**完整示例:**
```
http://localhost:9000/feishu/labor_hour/cli_a82e97f4de29501c-nEoauWe1YEt5luG6J4Ij8cvlTZKb3po3/oc_xxx/https://uxkpl4cba3j.feishu.cn/base/UfDPbov0Eal3RpsWAEBcyfe1nAb?table=tbla3OuZeDczpqZx&view=vewGyZRz6D?date=2025-09-30
```

---

## 📊 返回结果

### 成功响应（工作日）

```json
{
  "status": "success",
  "is_holiday": false,
  "date": "2025-09-30",
  "result": {
    "all_filled": false,
    "total": 15,
    "filled": 10,
    "not_filled": 5,
    "fill_rate": "66.7%",
    "on_leave": [],
    "exception_day": ["滕凯"]
  },
  "message_sent": true
}
```

### 成功响应（节假日）

```json
{
  "status": "success",
  "is_holiday": true,
  "message": "🎉 2025-10-01 是节假日，无需检查工时填写",
  "date": "2025-10-01"
}
```

### 错误响应

```json
{
  "status": "error",
  "message": "错误详细信息",
  "date": "2025-09-30"
}
```

---

## 🔧 配置群聊ID

### 如何获取群聊ID？

**方式1: 通过飞书开放平台**

1. 登录 [飞书开放平台](https://open.feishu.cn/)
2. 进入你的应用 → 功能配置 → 机器人
3. 将机器人添加到目标群聊
4. 在群聊中发送消息，查看webhook回调日志获取 `chat_id`

**方式2: 通过API获取**

```bash
# 获取机器人所在的群聊列表
curl -X GET \
  'https://open.feishu.cn/open-apis/im/v1/chats' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

**方式3: 从webhook回调获取**

发送消息到群聊时，在webhook回调数据中可以找到：
```json
{
  "event": {
    "message": {
      "chat_id": "oc_xxxxxxxxxxxxx"
    }
  }
}
```

---

## 🧪 测试步骤

### 步骤1: 修改配置

编辑 `test_api.http` 文件，修改变量：

```
@group_chat_id = oc_your_actual_group_chat_id
```

### 步骤2: 启动服务

```bash
cd /Users/forhheart/AIGC/Agent2IM
python backend/api/main.py
```

看到以下输出表示启动成功：
```
INFO:     Started server process [xxxxx]
INFO:     Uvicorn running on http://0.0.0.0:9000 (Press CTRL+C to quit)
```

### 步骤3: 测试接口

**使用 VS Code REST Client:**
1. 安装插件: `REST Client` by Huachao Mao
2. 打开 `test_api.http`
3. 点击接口上方的 "Send Request"

**使用 curl:**
```bash
curl "http://localhost:9000/feishu/labor_hour/cli_a82e97f4de29501c-nEoauWe1YEt5luG6J4Ij8cvlTZKb3po3/oc_xxx/https://uxkpl4cba3j.feishu.cn/base/UfDPbov0Eal3RpsWAEBcyfe1nAb?table=tbla3OuZeDczpqZx&view=vewGyZRz6D"
```

**使用浏览器:**

直接在浏览器打开URL（需要URL编码）

### 步骤4: 查看结果

- ✅ 控制台显示检查过程
- ✅ 飞书群聊收到卡片消息
- ✅ API返回JSON结果

---

## 🎯 测试场景

### 场景1: 检查今天的填写情况

```
GET /feishu/labor_hour/{app_id}-{app_secret}/{group_chat_id}/{bitable_url}
```

### 场景2: 检查指定日期

```
GET /feishu/labor_hour/{app_id}-{app_secret}/{group_chat_id}/{bitable_url}?date=2025-09-30
```

### 场景3: 检查节假日（应返回节假日提示）

```
GET /feishu/labor_hour/{app_id}-{app_secret}/{group_chat_id}/{bitable_url}?date=2025-10-01
```

### 场景4: 检查周末

```
GET /feishu/labor_hour/{app_id}-{app_secret}/{group_chat_id}/{bitable_url}?date=2025-10-25
```

### 场景5: 检查例外日期（如星期二 - 滕凯）

```
GET /feishu/labor_hour/{app_id}-{app_secret}/{group_chat_id}/{bitable_url}?date=2025-10-07
```

---

## 📱 飞书群聊效果

调用API后，群聊会收到如下卡片消息：

```
┌─────────────────────────────────────────┐
│  📊 工时填写情况 - 2025-09-30           │
├─────────────────────────────────────────┤
│                                         │
│  ⚠️ 还有 5 人未填写工时                │
│                                         │
│  📈 统计信息:                           │
│  - 应填写人数: 15 人                    │
│  - 已填写: 10 人 ✅                     │
│  - 未填写: 5 人 ❌                      │
│  - 填写率: 66.7%                        │
│                                         │
│  📅 例外日期人员 (1 人):                │
│    滕凯                                  │
│                                         │
│  ❗ 需要提醒的人员:                      │
│    • 刘安营                              │
│    • 韩宇轩                              │
│    • 徐俊朗                              │
│    • 耿蕾                                │
│    • 石国艳                              │
│                                         │
│  ⏰ 检查时间: 2025-10-23 14:30:00      │
├─────────────────────────────────────────┤
│  填写率: 66.7%                          │
└─────────────────────────────────────────┘
```

---

## 🛠️ 调试技巧

### 1. 查看服务日志

启动服务后，控制台会显示详细日志：

```
================================================================================
📋 开始检查工时填写情况
   App ID: cli_a82e97f4de29501c
   群聊ID: oc_xxx
   Bitable URL: https://xxx
   检查日期: 2025-09-30

🔍 正在检查人员填写情况...
📋 从配置文件读取人员名单...
📅 2025-09-30 是星期二
  ℹ️ 滕凯 在星期二无需填写（例外日期）
✅ 需要检查 15 名人员

📊 检查结果:
   应填写人数: 15
   已填写: 10 人
   未填写: 5 人
   填写率: 66.7%

✅ 消息已发送到群聊
================================================================================
```

### 2. 检查API响应

```bash
# 使用 curl -v 查看详细响应
curl -v "http://localhost:9000/feishu/labor_hour/..."
```

### 3. 验证配置

```bash
# 检查服务状态
curl http://localhost:9000/

# 查看定时任务状态
curl http://localhost:9000/scheduler/status
```

---

## ⚠️ 常见问题

### Q1: 群聊收不到消息？

**检查项:**
1. ✅ 群聊ID是否正确
2. ✅ 机器人是否已加入群聊
3. ✅ 应用是否有发送消息权限
4. ✅ 查看API返回结果和服务日志

### Q2: 接口返回401错误？

**原因:** 应用凭证过期或错误

**解决:**
1. 检查 `app_id` 和 `app_secret` 是否正确
2. 确认应用未被停用

### Q3: 接口返回91402错误？

**原因:** 多维表格不存在或无权限

**解决:**
1. 确认 `bitable_url` 是否正确
2. 将应用添加为多维表格的协作者
3. 检查应用是否有 `bitable:app:readonly` 权限

### Q4: 日期参数不生效？

**检查:** URL编码问题

**正确格式:**
```
?date=2025-09-30
```

---

## 🔗 相关文档

- [Bitable功能说明](./README_BITABLE.md)
- [调度器使用说明](./README_SCHEDULER.md)
- [飞书开放平台](https://open.feishu.cn/)
- [FastAPI文档](https://fastapi.tiangolo.com/)

---

## 📝 URL编码注意事项

由于URL中包含特殊字符（如 `?`, `&`, `=`），建议：

1. **使用HTTP工具** (REST Client, Postman) - 自动处理编码
2. **手动编码** - 使用在线URL编码工具
3. **curl命令** - 使用引号包裹URL

```bash
# 正确 ✅
curl "http://localhost:9000/feishu/labor_hour/..."

# 错误 ❌ (& 会被shell解析)
curl http://localhost:9000/feishu/labor_hour/...
```


