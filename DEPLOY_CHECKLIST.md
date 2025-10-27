# ✅ 部署检查清单

快速检查部署是否完成

---

## 第一步：配置文件 ✏️

```bash
# 编辑配置文件
vim backend/src/config/labor_hour.json
```

必填项：
- [ ] `app_id`: `cli_xxxxxxxxxxxx`
- [ ] `app_secret`: `xxxxxxxxxxxx`
- [ ] `bitable_url`: 工时表格 URL
- [ ] `webhook.url`: 群机器人 URL

---

## 第二步：启动服务 🚀

```bash
cd /Users/forhheart/AIGC/Agent2IM

# 启动
docker compose -f docker/docker-compose.yml up -d

# 检查状态
docker compose -f docker/docker-compose.yml ps
```

预期结果：
- [ ] `agent2im-api` - Up
- [ ] `agent2im-scheduler` - Up

---

## 第三步：验证服务 🔍

```bash
# 本地测试
curl http://localhost:9000/health

# 外部测试（替换为你的 IP）
curl http://45.78.224.30:9000/health
```

预期响应：
- [ ] `{"status":"ok"}`

---

## 第四步：飞书配置 🔧

在飞书开放平台：

1. **权限管理** → 添加权限
   - [ ] `approval:approval`
   - [ ] `calendar:timeoffevent:write`
   - [ ] `calendar:timeoffevent:readonly`
   - [ ] 等待管理员审批通过

2. **事件订阅** → 请求地址
   - [ ] URL: `http://45.78.224.30:9000/feishu/approval/callback`
   - [ ] 保存成功（验证通过）

3. **事件订阅** → 添加事件
   - [ ] `approval_instance`

4. **版本管理** → 发布
   - [ ] 应用已发布

---

## 第五步：测试功能 🧪

```bash
# 运行配置检查
python backend/playground/check_approval_setup.py

# 运行功能测试
python backend/playground/test_approval.py
```

预期结果：
- [ ] 配置检查全部通过
- [ ] 功能测试无报错

---

## 第六步：真实测试 🎯

1. 在飞书提交一个请假审批
   - [ ] 审批已提交

2. 审批人审批通过
   - [ ] 审批已通过

3. 检查系统日志
   ```bash
   docker compose -f docker/docker-compose.yml logs -f api
   ```
   - [ ] 看到 "✅ 收到审批通过事件"
   - [ ] 看到 "📆 创建请假日历成功"

4. 检查飞书日历
   - [ ] 日历中有 "请假中(全天)" 事件

5. 测试工时检查
   ```bash
   python backend/playground/run_labor_hour_check.py
   ```
   - [ ] 请假人员已被排除
   - [ ] 请假人员不会被 @

---

## 🎉 全部完成！

所有步骤都打勾 ✅ 后，你的 HR 小助手就配置完成了！

---

## 🆘 遇到问题？

| 问题 | 解决方案 |
|------|---------|
| 端口被占用 | `sudo lsof -i :9000` |
| 服务无法启动 | `docker compose logs api` |
| 外部无法访问 | 检查防火墙和安全组 |
| 飞书验证失败 | 确保服务已启动并可访问 |
| 权限错误 | 等待管理员审批权限 |

**详细文档**：
- [快速开始](./QUICKSTART_APPROVAL.md)
- [完整配置](./SETUP_HR_ASSISTANT.md)
- [部署指南](./DEPLOYMENT_GUIDE.md)

---

**💡 提示**：把这个清单打印出来，逐项检查，避免遗漏！

