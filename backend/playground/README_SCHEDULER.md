# 定时任务调度器使用说明

## 🚀 快速启动

### 方式1：使用启动脚本（推荐）

```bash
cd /Users/forhheart/AIGC/Agent2IM
python backend/playground/start_scheduler.py
```

启动后会看到菜单：
```
================================================================================
  选择测试模式
================================================================================
1. 手动触发任务（立即执行一次）
2. 启动定时调度器（按配置时间自动执行）
3. 查看配置信息
4. 测试Bitable连接
0. 退出
================================================================================
```

---

## 📋 功能说明

### 1️⃣ 手动触发任务
- **用途**: 立即执行一次任务，不等待定时时间
- **适用场景**: 测试任务是否正常工作
- **子选项**:
  - 晚上9点群聊提醒（检查今天）
  - 晚上11点私信提醒（检查今天）
  - 早上10点群聊补填提醒（检查昨天）

### 2️⃣ 启动定时调度器
- **用途**: 按照 `task.json` 配置的时间自动执行任务
- **适用场景**: 实际生产环境运行
- **注意**: 按 `Ctrl+C` 可以停止调度器

### 3️⃣ 查看配置信息
- 显示飞书配置（App ID、群聊ID等）
- 显示多维表格配置
- 显示所有定时任务
- 显示人员列表
- 显示消息模板

### 4️⃣ 测试Bitable连接
- 测试多维表格配置是否正确
- 验证能否正常访问

---

## ⚙️ 配置文件

### 📁 backend/config/task.json

```json
{
  "tasks": [
    {
      "id": "task_1",
      "name": "晚上9点群聊提醒",
      "enabled": true,         // ← 启用/禁用任务
      "time": "21:00",        // ← 执行时间
      "type": "group_mention",
      "message_template": "evening_first",
      "check_date": "today"
    }
  ],
  "config": {
    "app_id": "cli_xxxxx",              // ← 飞书应用ID
    "app_secret": "xxxxx",              // ← 飞书应用密钥
    "group_chat_id": "oc_xxxxx",        // ← 群聊ID
    "form_url": "https://xxx",          // ← 表单URL
    "bitable_app_token": "bascnxxx",    // ← 多维表格Token
    "bitable_table_id": "tblxxx",       // ← 数据表ID
    "timezone": "Asia/Shanghai"         // ← 时区
  }
}
```

### 📁 backend/config/people.json

```json
{
  "people": [
    {
      "id": "001",
      "name": "张三",
      "exceptions": ["星期二"],  // ← 例外日期（不提醒）
      "off": false              // ← 是否请假
    }
  ]
}
```

### 📁 backend/config/message.json

消息模板配置，定义提醒消息的内容和格式。

---

## 🔄 工作流程

```
启动调度器
    ↓
加载配置文件 (task.json, people.json, message.json)
    ↓
初始化飞书服务
    ↓
设置定时任务
    ↓
等待执行时间
    ↓
执行任务:
    1. 检查节假日（是 → 跳过）
    2. 获取人员名单（排除请假和例外日期）
    3. 检查多维表格填写情况
    4. 向未填写人员发送提醒
    ↓
等待下一次执行
```

---

## 🧪 测试步骤

### 步骤1: 检查配置

```bash
python backend/playground/start_scheduler.py
# 选择: 3 (查看配置信息)
```

确认以下信息正确：
- ✅ 飞书App ID和密钥
- ✅ 群聊ID
- ✅ 多维表格配置
- ✅ 人员列表

### 步骤2: 手动测试任务

```bash
python backend/playground/start_scheduler.py
# 选择: 1 (手动触发任务)
# 选择: 1 (晚上9点群聊提醒)
```

观察输出：
- 是否成功读取配置
- 是否正确判断节假日
- 是否正确过滤人员
- 是否成功发送消息

### 步骤3: 启动定时调度器

```bash
python backend/playground/start_scheduler.py
# 选择: 2 (启动定时调度器)
```

调度器会在后台运行，按配置时间自动执行任务。

---

## 💡 常见问题

### Q: 如何修改执行时间？
A: 编辑 `backend/config/task.json`，修改 `time` 字段：
```json
{
  "time": "09:00"  // 改为早上9点
}
```

### Q: 如何暂停某个任务？
A: 编辑 `backend/config/task.json`，设置 `enabled: false`：
```json
{
  "enabled": false  // 暂停任务
}
```

### Q: 如何添加新的人员？
A: 编辑 `backend/config/people.json`，添加新条目：
```json
{
  "id": "099",
  "name": "李四",
  "exceptions": [],
  "off": false
}
```

### Q: 节假日会发送提醒吗？
A: 不会，系统会自动判断节假日并跳过提醒。

### Q: 如何查看任务执行日志？
A: 查看控制台输出，或配置日志文件路径（`task.json` 中的 `log` 配置）。

### Q: 任务执行失败怎么办？
A: 检查：
1. 网络连接是否正常
2. 飞书应用权限是否完整
3. 配置信息是否正确
4. 查看错误日志

---

## 📊 任务说明

### 任务1: 晚上9点群聊提醒
- **时间**: 21:00
- **方式**: 群聊@未填写人员
- **检查**: 今天的填写情况
- **目的**: 首次提醒

### 任务2: 晚上11点私信提醒
- **时间**: 23:00
- **方式**: 私信未填写人员
- **检查**: 今天的填写情况
- **目的**: 二次提醒（更严肃）

### 任务3: 早上10点群聊补填提醒
- **时间**: 10:00
- **方式**: 群聊@未填写人员
- **检查**: 昨天的填写情况
- **目的**: 补填提醒

---

## 🛠️ 高级用法

### 后台运行（Linux/Mac）

```bash
nohup python backend/playground/start_scheduler.py > scheduler.log 2>&1 &
```

### 使用systemd（Linux）

创建服务文件 `/etc/systemd/system/feishu-scheduler.service`:

```ini
[Unit]
Description=Feishu Reminder Scheduler
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/Agent2IM
ExecStart=/usr/bin/python3 backend/playground/start_scheduler.py
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl start feishu-scheduler
sudo systemctl enable feishu-scheduler  # 开机自启
```

---

## 📝 注意事项

1. **配置安全**: 不要将包含密钥的配置文件提交到Git
2. **时区设置**: 确保 `timezone` 配置正确
3. **权限检查**: 确保飞书应用有足够的权限
4. **测试环境**: 建议先在测试群测试
5. **节假日**: 系统自动判断中国节假日

---

## 🔗 相关文档

- [Bitable功能说明](./README_BITABLE.md)
- [飞书开放平台](https://open.feishu.cn/)
- [APScheduler文档](https://apscheduler.readthedocs.io/)

