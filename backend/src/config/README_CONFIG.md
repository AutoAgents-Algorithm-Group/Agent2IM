# 配置文件说明

## 工时检查服务配置 (`labor_hour.json`)

### ❓ 为什么既需要 App 配置又需要 Webhook？

这是一个常见的疑问。让我们理清楚：

#### 1. **飞书应用配置** (`feishu.app_id` & `feishu.app_secret`)

**用途**: 读取飞书多维表格（Bitable）数据

**权限**: 需要飞书应用的以下权限：
- `bitable:app` - 读取多维表格应用
- `bitable:app:read` - 读取多维表格记录

**获取方式**:
1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 创建企业自建应用
3. 添加权限范围：多维表格
4. 获取 App ID 和 App Secret

**为什么需要**: 
- 工时检查服务需要读取多维表格中的工时填写记录
- 这些数据只能通过飞书应用 API 访问
- **这是必需的**，因为我们要检查谁填了、谁没填

#### 2. **群机器人 Webhook** (`webhook.url` & `webhook.secret`)

**用途**: 发送检查结果消息到飞书群组

**权限**: 无需特殊权限，群成员即可添加机器人

**获取方式**:
1. 打开飞书群聊
2. 点击群设置 → 群机器人 → 添加机器人
3. 选择"自定义机器人"
4. 获取 Webhook URL 和签名密钥（Secret）

**为什么使用 Webhook**:
- 简单直接，不需要额外的应用权限
- 类似新闻推送服务的设计
- 发送消息到群组最简单的方式

### 📊 完整流程

```
1. 使用 App 配置读取 Bitable
   ┌─────────────────────────────┐
   │ FeishuClient(app_id, secret)│
   │          ↓                   │
   │ BitableAPI.check_users()    │
   │          ↓                   │
   │ 获取填写情况数据            │
   └─────────────────────────────┘

2. 处理数据生成报告
   ┌─────────────────────────────┐
   │ 统计已填写/未填写人数       │
   │          ↓                   │
   │ 生成美观的卡片消息          │
   └─────────────────────────────┘

3. 使用 Webhook 发送到群组
   ┌─────────────────────────────┐
   │ 签名: timestamp + secret    │
   │          ↓                   │
   │ POST 到 webhook_url         │
   │          ↓                   │
   │ 消息出现在群聊中            │
   └─────────────────────────────┘
```

### 🔧 配置示例

```json
{
  "feishu": {
    "app_id": "cli_a1b2c3d4e5f6g7h8",
    "app_secret": "ABC123DEF456GHI789"
  },
  "bitable": {
    "url": "https://your-company.feishu.cn/base/UfDPbov0Eai3RpsWAEBcyfe1nAb?table=tbla3OuZeDczpqZx&view=vewGyZRz6D"
  },
  "webhook": {
    "url": "https://open.feishu.cn/open-apis/bot/v2/hook/ebe32443-795c-4e92-b28e-29fea8e611be",
    "secret": "WYDI1R5kaqfQpTxMUBzMbfwBJcZgw4e6"
  }
}
```

### 💡 常见问题

**Q: 能不能只用 Webhook，不配置 App？**
A: 不行。因为需要读取多维表格数据，这必须通过飞书应用 API。

**Q: 能不能只用 App，不配置 Webhook？**
A: 理论上可以，但需要修改代码，使用 Message API 发送消息，而且需要获取群聊 ID 和发送权限。Webhook 更简单。

**Q: App 和 Webhook 是同一个东西吗？**
A: 不是！
- **App**: 企业自建应用，需要管理员创建，有完整的API权限
- **Webhook**: 群机器人，任何群成员可添加，只能发送消息

**Q: 新闻服务为什么不需要 App 配置？**
A: 因为新闻服务不需要读取飞书数据，只需要推送消息。所以只用 Webhook 就够了。

### 🎯 对比：新闻服务 vs 工时检查服务

| 项目 | 新闻服务 | 工时检查服务 |
|-----|---------|------------|
| **需要读取数据** | ❌ 否（从网络爬取） | ✅ 是（从Bitable读取） |
| **需要App配置** | ❌ 否 | ✅ 是 |
| **需要Webhook** | ✅ 是 | ✅ 是 |
| **配置文件** | `news.yml` | `labor_hour.json` |

### 📝 配置步骤

1. **创建飞书应用** (获取 app_id 和 app_secret)
   ```
   1. 访问 https://open.feishu.cn/
   2. 开发者后台 → 创建企业自建应用
   3. 权限管理 → 添加权限：
      - bitable:app
      - bitable:app:read
   4. 凭证与基础信息 → 查看 App ID 和 App Secret
   ```

2. **配置多维表格** (获取 bitable url)
   ```
   1. 打开你的工时填写表格
   2. 复制浏览器地址栏的完整 URL
   3. 确保 URL 包含: base、table、view 三个参数
   ```

3. **添加群机器人** (获取 webhook_url 和 secret)
   ```
   1. 打开飞书群聊
   2. 群设置 → 群机器人 → 添加机器人
   3. 自定义机器人 → 设置名称和头像
   4. 添加后获取 Webhook 地址和签名密钥
   ```

4. **填写配置文件**
   ```bash
   cp config/labor_hour.example.json config/labor_hour.json
   # 编辑 labor_hour.json，填入上面获取的配置
   ```

5. **测试**
   ```bash
   cd backend/playground
   python run_labor_hour_check.py
   ```

### 🔐 安全建议

- ⚠️ 不要将配置文件提交到 Git
- ⚠️ App Secret 和 Webhook Secret 要妥善保管
- ⚠️ 定期轮换密钥
- ✅ 使用环境变量存储敏感信息（生产环境）

### 🚀 最佳实践

1. **开发环境**: 使用单独的测试应用和测试群组
2. **生产环境**: 使用专用的生产应用
3. **多环境**: 为不同环境准备不同的配置文件
   ```
   config/labor_hour.dev.json
   config/labor_hour.staging.json
   config/labor_hour.prod.json
   ```

---

如有其他疑问，请查看 [Backend README](../README.md) 或提交 Issue。



