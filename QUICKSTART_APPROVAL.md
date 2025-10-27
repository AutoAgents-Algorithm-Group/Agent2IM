# 🚀 HR小助手 - 5分钟快速开始

完成审批通过自动创建请假日历的最快配置方式

---

## 步骤 1: 获取飞书应用凭证 (2分钟)

1. 访问 https://open.feishu.cn/app
2. 点击你的应用，复制以下信息：
   ```
   App ID:     cli_xxxxxxxxxxxx
   App Secret: xxxxxxxxxxxx
   ```

---

## 步骤 2: 配置系统 (1分钟)

编辑 `backend/src/config/labor_hour.json`:

```json
{
  "feishu": {
    "app_id": "cli_xxxxxxxxxxxx",        // 👈 粘贴你的 App ID
    "app_secret": "xxxxxxxxxxxx",         // 👈 粘贴你的 App Secret
    "bitable_url": "你的多维表格URL"      // 工时表格URL
  },
  "webhook": {
    "url": "https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx",
    "secret": ""
  }
}
```

---

## 步骤 3: 添加权限 (1分钟)

在飞书开放平台 → 你的应用 → **权限管理**，添加：

```
✅ approval:approval              - 审批
✅ approval:approval:readonly     - 获取审批（只读）
✅ calendar:calendar              - 日历
✅ calendar:timeoffevent:write    - 创建请假日程
✅ calendar:timeoffevent:readonly - 查询请假日程
```

**⚠️ 添加完权限后等待管理员审批！**

---

## 步骤 4: 配置事件订阅 (1分钟)

在飞书开放平台 → 你的应用 → **事件订阅**:

1. **请求地址**: `https://your-domain.com/feishu/approval/callback`
   > 替换为你的服务器地址

2. **添加事件**: 搜索并添加 `approval_instance`

3. **保存配置**

---

## 步骤 5: 启动服务 (30秒)

```bash
cd /Users/forhheart/AIGC/Agent2IM

# 启动服务
docker compose -f docker/docker-compose.yml up -d

# 查看日志
docker compose -f docker/docker-compose.yml logs -f api
```

---

## 步骤 6: 验证配置 (30秒)

```bash
# 运行配置检查脚本
python backend/playground/check_approval_setup.py
```

如果看到：
```
🎉 恭喜！所有检查项都已通过！
```

说明配置成功！

---

## 步骤 7: 创建审批模板

在飞书管理后台 → **审批** → **创建审批**:

必需字段：
- ✅ **请假开始时间** (日期类型)
- ✅ **请假结束时间** (日期类型)
- 📝 请假原因 (文本类型，可选)

保存并发布审批模板

---

## 步骤 8: 测试功能

### 方法 1: 使用测试脚本

```bash
python backend/playground/test_approval.py
```

### 方法 2: 真实审批测试

1. 在飞书提交一个请假审批
2. 审批通过后
3. 检查日历是否自动创建了请假事件
4. 运行工时检查，验证请假人员不会被@

---

## ✅ 配置完成！

现在你的系统会：
- ✅ 审批通过时自动创建请假日历
- ✅ 工时检查时自动排除请假人员
- ✅ 请假人员不会被 @ 提醒

---

## 🆘 遇到问题？

### 快速诊断

```bash
# 1. 检查配置
python backend/playground/check_approval_setup.py

# 2. 查看服务日志
docker compose -f docker/docker-compose.yml logs -f api

# 3. 测试审批功能
python backend/playground/test_approval.py
```

### 常见问题

**Q: URL 验证失败**
- 确保服务已启动: `docker ps`
- 确保端口可访问: `curl http://localhost:8000/health`
- 检查域名和端口是否正确

**Q: 收不到事件回调**
- 确认应用已发布
- 确认权限已审批通过
- 查看飞书开放平台「事件推送日志」

**Q: 创建日历失败**
- 确认权限已添加
- 确认 Token 未过期
- 确认时间参数正确（start < end）

**Q: 请假查询失败**
- 确认有 `calendar:timeoffevent:readonly` 权限
- 检查用户 open_id 是否正确

---

## 📚 详细文档

查看完整配置指南: [SETUP_HR_ASSISTANT.md](./SETUP_HR_ASSISTANT.md)

---

## 💡 提示

- 首次配置建议使用测试环境
- 配置完成后记得发布应用
- 定期检查权限是否过期
- 监控事件推送日志

---

**🎉 祝你使用愉快！**

