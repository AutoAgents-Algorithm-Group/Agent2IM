# 审批事件订阅使用指南

## 📋 功能说明

当飞书审批通过时，自动创建请假日历事件，实现审批与日历的联动。

## 🎯 工作流程

```
飞书审批 → 审批通过 → Webhook 回调 → 提取请假信息 → 创建请假日历
```

## 🔧 配置步骤

### 1. 配置飞书应用权限

在飞书开放平台配置以下权限：

**审批权限**:
- `approval:approval:readonly` - 查看审批应用
- `approval:instance` - 获取审批实例详情

**日历权限**:
- `calendar:calendar` - 管理日历
- `calendar:timeoffevent:write` - 创建请假日程

### 2. 配置事件订阅

在飞书开放平台 → 事件订阅 → 添加事件：

**订阅事件**:
- `approval_instance` - 审批实例状态变更

**请求地址**:
```
https://your-domain.com/feishu/approval/callback
```

**加密方式**: 不加密（或根据需要配置）

### 3. 部署服务

```bash
# 部署 API 服务
docker compose -f docker/docker-compose.yml up -d
```

### 4. 配置审批模板

在飞书审批中创建请假审批模板，确保包含以下字段：

**必需字段**:
- 请假开始时间（日期类型或日期区间）
- 请假结束时间（日期类型）
- 请假原因（文本类型，可选）

**字段 ID 建议**（便于自动识别）:
- `start_time` 或包含 "开始" 的字段
- `end_time` 或包含 "结束" 的字段
- `reason` 或包含 "原因" 的字段

## 📡 API 接口

### 审批事件回调

**URL**: `POST /feishu/approval/callback`

**说明**: 接收飞书审批事件回调

**请求示例**:
```json
{
  "type": "event_callback",
  "event_id": "xxx",
  "event": {
    "type": "approval_instance",
    "status": "APPROVED",
    "approval_code": "xxx",
    "instance_code": "xxx",
    "user_id": "ou_xxx",
    "open_id": "ou_xxx"
  }
}
```

**响应示例**:
```json
{
  "code": 0,
  "msg": "success"
}
```

## 🧪 测试

### 1. URL 验证测试

飞书首次配置 webhook 时会发送验证请求：

```bash
curl -X POST 'https://your-domain.com/feishu/approval/callback' \
-H 'Content-Type: application/json' \
-d '{
  "type": "url_verification",
  "challenge": "test_challenge"
}'
```

**期望响应**:
```json
{
  "challenge": "test_challenge"
}
```

### 2. 模拟审批通过事件

```bash
curl -X POST 'https://your-domain.com/feishu/approval/callback' \
-H 'Content-Type: application/json' \
-d '{
  "type": "event_callback",
  "event_id": "test_event_001",
  "event": {
    "type": "approval_instance",
    "status": "APPROVED",
    "approval_code": "7C468A54-8745-2245-9675-08654A59C265",
    "instance_code": "81D31358-93AF-92C6-7425-01A5D67C4E71",
    "user_id": "ou_xxx",
    "open_id": "ou_xxx"
  }
}'
```

## 📝 日志输出

审批事件处理时会输出详细日志：

```
================================================================================
📨 收到审批事件回调
   时间: 2025-10-27 14:30:00
✅ 收到审批通过事件
📋 审批信息:
   审批定义: 7C468A54-8745-2245-9675-08654A59C265
   实例编码: 81D31358-93AF-92C6-7425-01A5D67C4E71
   申请人: ou_xxx / ou_xxx
📅 创建请假日历:
   用户: ou_xxx
   开始: 2025-10-27 (1761532800)
   结束: 2025-10-28 (1761619200)
✅ 请假日历创建成功: 6962888606377328652
📊 处理结果: {'status': 'success', 'message': '请假日历创建成功', 'calendar_event_id': '6962888606377328652'}
================================================================================
```

## 🔍 故障排查

### 1. 审批通过但没有创建日历

**可能原因**:
- 审批表单字段不包含请假时间信息
- 字段 ID 或名称无法识别
- 权限不足

**排查步骤**:
```bash
# 查看日志
docker logs agent2im-scheduler -f

# 检查审批详情 API
curl -X GET 'https://open.feishu.cn/open-apis/approval/v4/instances/{instance_code}' \
-H 'Authorization: Bearer {token}'
```

### 2. 日历 API 返回错误

**常见错误**:

- `code=190014`: 时间参数错误
  - 检查 `start_time` 是否早于 `end_time`
  - 确认时间戳格式正确（秒级）

- `code=9499`: Bad Request
  - Token 可能已过期
  - 检查权限配置
  - 验证时间格式

### 3. 重复处理问题

系统使用 `event_id` 进行幂等性控制，相同事件只会处理一次。

## 💡 最佳实践

### 1. 审批模板设计

**推荐结构**:
```
审批名称: 请假申请
表单字段:
  - 请假类型: 单选（年假/病假/事假）
  - 请假时间: 日期区间（start_time/end_time）
  - 请假天数: 数字（自动计算）
  - 请假原因: 多行文本
```

### 2. 时间格式

支持以下时间格式：
- `YYYY-MM-DD` - 例如: `2025-10-27`
- `YYYY-MM-DD HH:MM:SS` - 例如: `2025-10-27 00:00:00`
- 时间戳（秒） - 例如: `1761532800`

### 3. 监控和告警

建议配置：
- 审批事件处理失败告警
- 日历创建失败告警
- 定期检查事件处理日志

## 🔗 相关文档

- [飞书审批 API](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/approval-v4/instance/list)
- [飞书日历 API](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/calendar-v4/timeoff_event/create)
- [事件订阅](https://open.feishu.cn/document/ukTMukTMukTM/uUTNz4SN1MjL1UzM)

## 📞 技术支持

如有问题，请查看：
1. 日志输出
2. 飞书开放平台事件推送日志
3. API 响应错误信息

