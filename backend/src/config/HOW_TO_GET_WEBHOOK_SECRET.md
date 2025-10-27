# 如何获取飞书群机器人的 Webhook Secret

## 📝 步骤说明

### 1. 打开飞书群聊
找到你想要接收工时检查消息的群组

### 2. 添加自定义机器人
1. 点击群聊右上角的 **设置** 图标
2. 选择 **群机器人**
3. 点击 **添加机器人**
4. 选择 **自定义机器人**

### 3. 配置机器人
1. 给机器人起个名字，比如：**工时检查助手**
2. 可以选择一个图标
3. **重要**：选择 **签名校验** 方式
4. 点击 **添加**

### 4. 获取配置信息
添加成功后，会显示两个信息：

```
Webhook 地址: https://open.feishu.cn/open-apis/bot/v2/hook/ebe32443-795c-4e92-b28e-29fea8e611be
签名密钥: WYDI1R5kaqfQpTxMUBzMbfwBJcZgw4e6
```

### 5. 填写到配置文件

编辑 `backend/config/labor_hour.json`：

```json
{
  "webhook": {
    "url": "https://open.feishu.cn/open-apis/bot/v2/hook/ebe32443-795c-4e92-b28e-29fea8e611be",
    "secret": "WYDI1R5kaqfQpTxMUBzMbfwBJcZgw4e6"  // ← 填写真实的签名密钥
  }
}
```

## ⚠️ 常见问题

### Q: 没有看到"签名校验"选项？
A: 确保你选择的是"自定义机器人"，而不是其他类型的机器人。

### Q: 忘记了签名密钥怎么办？
A: 可以删除原来的机器人，重新添加一个。

### Q: 可以不用签名吗？
A: 不建议。签名校验能防止恶意请求。如果实在不想用，可以在代码中修改，但不推荐。

## ✅ 验证配置

填写完成后，运行测试：

```bash
cd backend/playground
python run_labor_hour_check.py
```

如果配置正确，你会在群里收到消息！

## 🎯 完整配置示例

```json
{
  "feishu": {
    "app_id": "cli_a87352e3c577900e",
    "app_secret": "DlVXx6WbRuDh4PnJkhZeUpjlaXcthWwY"
  },
  "bitable": {
    "url": "https://uxkpl4cba3j.feishu.cn/base/UfDPbov0Eai3RpsWAEBcyfe1nAb?table=tbla3OuZeDczpqZx&view=vewGyZRz6D"
  },
  "webhook": {
    "url": "https://open.feishu.cn/open-apis/bot/v2/hook/ebe32443-795c-4e92-b28e-29fea8e611be",
    "secret": "WYDI1R5kaqfQpTxMUBzMbfwBJcZgw4e6"  // ← 这是真实的密钥！
  }
}
```

---

**提示**：签名密钥是敏感信息，不要提交到 Git！



