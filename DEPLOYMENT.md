# 🚀 快速部署指南

## 常用命令速查

### 🔥 最常用

```bash
# 修改 API 代码后，一键重新部署
make api-rebuild

# 查看 API 日志
make api-logs

# 查看所有可用命令
make help
```

### 📦 本地开发

```bash
# 开发模式（支持热重载）
make dev
```

访问：
- API: http://localhost:9000
- 文档: http://localhost:9000/docs
- 健康检查: http://localhost:9000/health

### 🐳 Docker 部署

#### API 服务（独立管理）
```bash
make api-build      # 构建镜像
make api-up         # 启动服务
make api-restart    # 重启服务（配置文件修改后）
make api-rebuild    # 重新构建并部署（代码修改后）⭐
make api-logs       # 查看日志
make api-down       # 停止服务
```

#### Scheduler 服务（独立管理）
```bash
make scheduler-build      # 构建镜像
make scheduler-up         # 启动服务
make scheduler-restart    # 重启服务
make scheduler-rebuild    # 重新构建并部署⭐
make scheduler-logs       # 查看日志
make scheduler-down       # 停止服务
```

#### 所有服务
```bash
make docker-up      # 启动所有服务
make docker-down    # 停止所有服务
make docker-logs    # 查看所有日志
make docker-ps      # 查看容器状态
```

## 🎯 典型场景

### 场景 1: 修改了 API 代码
```bash
# 在本地测试
make dev

# 部署到服务器（只更新 API，不影响 Scheduler）
make api-rebuild
```

### 场景 2: 修改了配置文件
```bash
# 编辑配置
vim backend/src/config/approval.yaml

# 重启服务（无需重新构建）
make api-restart
```

### 场景 3: 首次部署
```bash
# 启动所有服务
make docker-up

# 查看状态
make docker-ps

# 查看日志
make docker-logs
```

### 场景 4: 查看特定服务日志
```bash
# 只看 API 日志
make api-logs

# 只看 Scheduler 日志
make scheduler-logs
```

## 🔍 监控和调试

```bash
# 查看容器状态
make docker-ps

# 查看 API 健康状态
curl http://localhost:9000/health

# 进入容器调试
docker exec -it agent2im-api bash

# 查看容器资源使用
docker stats agent2im-api agent2im-scheduler
```

## 📁 项目结构

```
Agent2IM/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── main.py              # API 主入口
│   │   │   └── feishu/
│   │   │       └── approval.py      # 审批回调接口
│   │   ├── service/
│   │   │   └── feishu/
│   │   │       └── approval.py      # 审批业务逻辑
│   │   ├── config/
│   │   │   ├── approval.yaml        # 审批配置
│   │   │   ├── labor_hour.yaml      # 工时配置
│   │   │   └── news.yaml            # 新闻配置
│   │   └── utils/
│   └── requirements.txt
├── docker/
│   ├── docker-compose.yml           # Docker Compose 配置
│   ├── Dockerfile                   # 镜像构建文件
│   ├── start.sh                     # API 启动脚本
│   ├── schedule.sh                  # Scheduler 启动脚本
│   └── README.md                    # 详细部署文档
├── Makefile                         # 命令快捷方式
└── DEPLOYMENT.md                    # 本文件
```

## 🔗 API 端点

### 审批回调接口
```
POST http://YOUR_HOST:9000/feishu/approval
```

支持的事件类型：
- `url_verification` - URL 验证
- `leave_approval` - 请假审批通过（基础版）
- `leave_approvalV2` - 请假审批通过（增强版）
- `leave_approval_revert` - 请假审批撤销
- `approval_instance` - 通用审批实例

### 其他接口
```
GET  http://localhost:9000/              # 根路径
GET  http://localhost:9000/health        # 健康检查
GET  http://localhost:9000/docs          # API 文档
GET  http://localhost:9000/redoc         # ReDoc 文档
GET  http://localhost:9000/feishu/schedule/status  # 调度器状态
GET  http://localhost:9000/feishu/schedule/jobs    # 任务列表
```

## ⚙️ 配置说明

### 审批配置 (approval.yaml)
```yaml
feishu:
  app_id: "your_app_id"
  app_secret: "your_app_secret"

approval_codes:
  leave:
    - "A9D489DC-5F55-4418-99F1-01E1CE734CA1"  # 请假审批编码
```

### 飞书开放平台配置

1. **事件订阅 URL**
   ```
   http://45.78.224.30:9000/feishu/approval
   ```

2. **需要订阅的事件**
   - 审批实例状态变更
   - 通过 API 订阅特定审批定义

3. **必需权限**
   - `approval:approval` - 审批应用
   - `calendar:calendar` - 日历
   - `contact:user.id:readonly` - 用户信息

详见：[飞书事件配置指南](上一次回复的内容)

## 🐛 故障排查

### API 无法访问
```bash
# 检查容器状态
make docker-ps

# 检查端口是否被占用
lsof -i :9000

# 查看日志
make api-logs
```

### 代码修改未生效
```bash
# 确保使用 rebuild（而不是 restart）
make api-rebuild
```

### 配置修改未生效
```bash
# 确保配置文件路径正确
# 然后重启服务
make api-restart
```

### 查看详细错误
```bash
# 查看实时日志
make api-logs

# 或直接查看 Docker 日志
docker logs agent2im-api --tail 100 -f
```

## 📚 更多文档

- [Docker 详细部署文档](docker/README.md)
- [审批事件测试用例](backend/playground/api/test_approval.http)
- [项目主 README](README.md)

## 💡 最佳实践

1. **本地开发使用 `make dev`**
   - 支持热重载，修改代码立即生效

2. **生产部署使用 Docker**
   - 环境一致，易于管理

3. **独立管理服务**
   - API 和 Scheduler 互不影响
   - 修改 API 只需 `make api-rebuild`

4. **定期查看日志**
   - `make api-logs` 监控运行状态

5. **使用配置文件管理**
   - 不要硬编码配置
   - 修改配置后重启即可

---

**快速开始**：`make dev` 本地测试 → `make api-rebuild` 部署生产 → `make api-logs` 查看日志

