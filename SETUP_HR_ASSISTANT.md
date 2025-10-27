# 🤖 HR 小助手配置指南

完整配置指南：实现**审批通过自动创建请假日历**

---

## 📋 功能说明

当员工的请假审批通过时，系统会自动：
1. ✅ 接收审批通过事件
2. 📅 提取请假时间信息
3. 🗓️ 自动创建请假日历
4. 🔍 工时检查时自动排除请假人员

---

## 🚀 配置步骤

### 第一步：飞书开放平台配置

#### 1.1 创建应用（如果已创建可跳过）

1. 访问 [飞书开放平台](https://open.feishu.cn/app)
2. 点击「创建企业自建应用」
3. 填写应用信息：
   - **应用名称**: `HR 小助手`
   - **应用描述**: `自动处理请假审批，创建请假日历`
   - **应用图标**: 上传一个图标
4. 点击「创建」

#### 1.2 获取应用凭证

创建完成后，在应用详情页找到：
- **App ID**: `cli_xxxxxxxxxxxx`
- **App Secret**: `xxxxxxxxxxxxxxxxxxxx`

> ⚠️ 请保存这两个值，稍后需要配置到系统中

---

#### 1.3 配置权限

在应用详情页 → **权限管理** → 添加以下权限：

##### 审批权限（必需）
```
✅ approval:approval         - 审批
✅ approval:approval:readonly - 获取审批定义（只读）
```

##### 日历权限（必需）
```
✅ calendar:calendar                  - 日历
✅ calendar:timeoffevent:write        - 创建请假日程（可写）
✅ calendar:timeoffevent:readonly     - 查询请假日程（只读）
```

##### 多维表格权限（工时检查需要）
```
✅ bitable:app                - 多维表格应用（只读）
```

##### 其他权限（可选）
```
✅ im:message                 - 发送消息
✅ im:message:send_as_bot     - 以应用身份发消息
```

**配置步骤**:
1. 点击「添加权限」
2. 搜索上述权限
3. 逐个添加
4. 点击「保存」

> 💡 添加权限后，需要管理员审批通过才能生效

---

#### 1.4 配置事件订阅

##### 步骤 1: 配置请求地址

1. 进入应用详情页 → **事件订阅** → **请求地址配置**
2. 填写 URL: `https://your-domain.com/feishu/approval/callback`
   
   > 📌 替换 `your-domain.com` 为你的服务器域名

3. 点击「保存」

> ⚠️ 注意：
> - 必须使用 **HTTPS**
> - 端口如果不是 443，需要加上端口号，如 `https://your-domain.com:8000/feishu/approval/callback`
> - 首次保存时，飞书会发送验证请求，确保服务已启动

##### 步骤 2: 订阅事件

1. 在 **事件订阅** → **添加事件**
2. 搜索并添加以下事件：

```
✅ 审批实例状态变更 (approval_instance)
```

3. 点击「保存」

**事件说明**:
- 当审批状态变更时（提交/通过/拒绝），飞书会推送事件到你的服务器
- 系统只会处理 `APPROVED`（通过）状态的审批

---

#### 1.5 配置 Encrypt Key（可选）

如果需要加密验证：
1. 在 **事件订阅** → **Encrypt Key**
2. 复制 **Encrypt Key**
3. 配置到系统中

> 💡 不配置也可以，系统会自动处理

---

#### 1.6 发布应用

1. 在应用详情页 → **版本管理与发布**
2. 点击「创建版本」
3. 填写版本信息
4. 提交审核
5. 审核通过后，点击「发布」

> ⚠️ 只有发布后的应用才能接收事件回调

---

### 第二步：配置系统

#### 2.1 配置 labor_hour.json

编辑 `backend/src/config/labor_hour.json`：

```json
{
  "feishu": {
    "app_id": "cli_xxxxxxxxxxxx",        // 👈 填写你的 App ID
    "app_secret": "xxxxxxxxxxxx",         // 👈 填写你的 App Secret
    "bitable_url": "https://xxx.feishu.cn/base/xxx?table=xxx"  // 工时表格URL
  },
  "webhook": {
    "url": "https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx",  // 群机器人URL
    "secret": ""  // 群机器人签名校验（可选）
  },
  "check_dates": [
    "周一", "周二", "周三", "周四", "周五"
  ]
}
```

#### 2.2 配置 people.json

编辑 `backend/src/config/people.json`：

```json
{
  "people": [
    {
      "name": "张三",
      "off": false,
      "exceptions": []
    },
    {
      "name": "李四",
      "off": false,
      "exceptions": ["周五"]  // 周五不需要填写工时
    },
    {
      "name": "王五",
      "off": true  // 已离职，不需要检查
    }
  ]
}
```

---

### 第三步：部署服务

#### 3.1 使用 Docker 部署（推荐）

```bash
# 1. 进入项目目录
cd /Users/forhheart/AIGC/Agent2IM

# 2. 确保配置文件已正确填写
ls backend/src/config/

# 3. 启动服务
docker compose -f docker/docker-compose.yml up -d

# 4. 查看日志
docker compose -f docker/docker-compose.yml logs -f api
```

#### 3.2 验证服务启动

```bash
# 检查服务状态
curl http://localhost:8000/health

# 预期响应
{
  "status": "ok",
  "service": "Agent2IM API"
}
```

#### 3.3 配置外网访问

如果服务器在内网，需要配置内网穿透或反向代理：

**方案 1: 使用 Nginx 反向代理**
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location /feishu/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**方案 2: 使用 frp/ngrok 内网穿透**
```bash
# 使用 ngrok 示例
ngrok http 8000
```

---

### 第四步：创建请假审批模板

#### 4.1 在飞书管理后台创建审批

1. 打开飞书管理后台 → **工作台** → **审批**
2. 点击「创建审批」
3. 选择「从空白创建」

#### 4.2 配置审批表单

**必需字段**:

1. **请假开始时间** (必填)
   - 字段类型: `日期`
   - 字段 ID: `start_time` 或包含「开始」
   - 显示格式: `YYYY-MM-DD`

2. **请假结束时间** (必填)
   - 字段类型: `日期`
   - 字段 ID: `end_time` 或包含「结束」
   - 显示格式: `YYYY-MM-DD`

3. **请假类型** (可选)
   - 字段类型: `单选`
   - 选项: 年假、病假、事假、调休

4. **请假原因** (可选)
   - 字段类型: `多行文本`
   - 字段 ID: `reason`

**示例表单结构**:
```
审批名称: 请假申请
────────────────────────
请假类型:     [单选框] ▼
请假开始时间: [2025-10-27]
请假结束时间: [2025-10-28]
请假天数:     [自动计算]
请假原因:     [文本框]
────────────────────────
```

#### 4.3 配置审批流程

1. 设置审批人（部门主管/HR）
2. 保存并发布审批模板

#### 4.4 获取审批定义编码

1. 在审批管理后台，找到刚创建的审批
2. 点击「设置」→ 「高级设置」
3. 复制「审批定义编码」(格式如: `7C468A54-8745-2245-9675-08654A59C265`)

> 💡 这个编码可以用来区分不同类型的审批

---

### 第五步：测试功能

#### 5.1 测试 URL 验证

```bash
# 测试验证端点
curl -X POST 'http://localhost:8000/feishu/approval/callback' \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "url_verification",
    "challenge": "test_challenge"
  }'

# 预期响应
{
  "challenge": "test_challenge"
}
```

#### 5.2 使用测试脚本

```bash
# 运行审批功能测试
cd /Users/forhheart/AIGC/Agent2IM
python backend/playground/test_approval.py
```

测试脚本会模拟：
- ✅ URL 验证
- ✅ 审批通过事件
- ✅ 审批拒绝事件
- ✅ 创建请假日历

#### 5.3 真实审批测试

1. **提交请假审批**
   - 在飞书客户端提交一个请假审批
   - 选择日期: 2025-10-27 ~ 2025-10-28
   - 填写原因

2. **审批通过**
   - 审批人审批通过

3. **检查日志**
   ```bash
   # 查看服务日志
   docker compose -f docker/docker-compose.yml logs -f api
   
   # 应该看到类似日志
   ✅ 收到审批通过事件
   📋 审批信息:
      审批定义: 7C468A54-8745-2245-9675-08654A59C265
      实例编码: 81D31358-93AF-92C6-7425-01A5D67C4E71
      申请人: ou_xxx
   📅 请假信息:
      开始时间: 2025-10-27
      结束时间: 2025-10-28
   📆 创建请假日历成功
   ```

4. **验证日历**
   - 打开飞书日历
   - 检查是否有「请假中(全天) / Time Off」事件

5. **测试工时检查**
   ```bash
   # 手动运行工时检查
   python backend/playground/run_labor_hour_check.py
   
   # 应该看到
   🔍 检查未填写人员的请假状态...
      📅 张三 在 2025-10-27 请假
   ✅ 发现 1 人请假
   
   # 张三不会被 @ 提醒
   ```

---

## 🎯 完整工作流程

```
1. 员工提交请假审批
   ↓
2. 主管审批通过
   ↓
3. 飞书推送 approval_instance 事件
   ↓
4. 系统接收事件回调
   ↓
5. 提取请假信息（开始时间、结束时间、原因）
   ↓
6. 调用飞书日历 API 创建请假日程
   ↓
7. 工时检查时自动查询请假日历
   ↓
8. 请假人员不会被 @ 提醒
```

---

## 🔍 故障排查

### 问题 1: URL 验证失败

**症状**: 配置事件订阅时提示「请求地址验证失败」

**解决方案**:
1. 确认服务已启动: `docker ps`
2. 确认端口可访问: `curl http://localhost:8000/health`
3. 确认域名解析正确
4. 确认防火墙已开放端口
5. 查看服务日志: `docker logs agent2im-api`

### 问题 2: 收不到事件回调

**症状**: 审批通过后，系统没有收到事件

**解决方案**:
1. 检查应用是否已发布
2. 检查事件订阅配置是否正确
3. 在飞书开放平台查看「事件推送日志」
4. 检查服务日志是否有错误

### 问题 3: 创建日历失败

**症状**: 收到事件，但日历创建失败

**解决方案**:
1. 检查权限是否已审批通过
2. 检查 Token 是否过期
3. 检查时间格式是否正确（必须 start < end）
4. 查看错误日志中的 code 和 msg

**常见错误码**:
- `code=190014`: 时间参数错误（start_time >= end_time）
- `code=9499`: 权限不足或 Token 过期
- `code=99991663`: 缺少必要权限

### 问题 4: 请假查询失败

**症状**: 工时检查时无法查询请假状态

**解决方案**:
1. 确认有 `calendar:timeoffevent:readonly` 权限
2. 检查用户的 open_id 是否正确
3. 检查时间戳格式（秒级，不是毫秒）

---

## 📊 监控和日志

### 查看实时日志

```bash
# API 服务日志
docker compose -f docker/docker-compose.yml logs -f api

# 定时任务日志
docker compose -f docker/docker-compose.yml logs -f scheduler
```

### 关键日志标识

```
✅ - 成功操作
❌ - 错误/失败
⚠️ - 警告
📋 - 审批信息
📅 - 请假信息
🔍 - 查询操作
📆 - 日历操作
```

---

## 💡 最佳实践

### 1. 审批模板设计

**推荐字段命名**:
- `start_time` / `end_time` - 方便系统自动识别
- `leave_type` - 请假类型
- `reason` - 请假原因

**避免**:
- 使用中文字段 ID
- 字段 ID 不明确（如 `field_1`）

### 2. 时间格式

**推荐格式**: `YYYY-MM-DD`
```
✅ 2025-10-27
✅ 2025-10-27 00:00:00
❌ 10/27/2025
❌ 2025-10-27T00:00:00Z
```

### 3. 权限管理

- 定期检查权限是否过期
- 及时更新 Token
- 使用最小权限原则

### 4. 监控告警

建议配置：
- 审批事件处理失败告警
- 日历创建失败告警
- Token 过期提醒

---

## 🔗 相关文档

- [飞书审批 API 文档](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/approval-v4/instance/list)
- [飞书日历 API 文档](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/calendar-v4/timeoff_event/create)
- [事件订阅配置](https://open.feishu.cn/document/ukTMukTMukTM/uUTNz4SN1MjL1UzM)
- [飞书开放平台](https://open.feishu.cn/app)

---

## 📞 技术支持

如有问题，请：
1. 查看服务日志
2. 查看飞书开放平台「事件推送日志」
3. 运行测试脚本 `test_approval.py`
4. 检查配置文件是否正确

---

## ✅ 配置检查清单

部署前请确认：

### 飞书开放平台
- [ ] 应用已创建
- [ ] App ID 和 App Secret 已获取
- [ ] 审批权限已添加并审批通过
- [ ] 日历权限已添加并审批通过
- [ ] 事件订阅已配置
- [ ] approval_instance 事件已订阅
- [ ] 应用已发布

### 系统配置
- [ ] labor_hour.json 已配置 app_id
- [ ] labor_hour.json 已配置 app_secret
- [ ] labor_hour.json 已配置 bitable_url
- [ ] labor_hour.json 已配置 webhook
- [ ] people.json 已配置人员列表

### 服务部署
- [ ] Docker 服务已启动
- [ ] 端口可访问（8000）
- [ ] 外网可访问（HTTPS）
- [ ] URL 验证通过

### 审批模板
- [ ] 审批模板已创建
- [ ] 包含开始时间字段
- [ ] 包含结束时间字段
- [ ] 审批流程已配置
- [ ] 审批模板已发布

### 测试验证
- [ ] URL 验证测试通过
- [ ] test_approval.py 测试通过
- [ ] 真实审批测试通过
- [ ] 日历创建成功
- [ ] 工时检查排除请假人员

---

🎉 **恭喜！配置完成后，你的 HR 小助手就可以自动处理请假审批了！**

