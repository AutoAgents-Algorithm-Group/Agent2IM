# Agent2IM Docker 部署指南

## 📦 服务架构

项目采用**微服务架构**，API 和 Scheduler 完全独立部署：

```
┌─────────────────────────────────────┐
│         agent2im-api                │
│   (处理飞书事件回调)                 │
│   Port: 9000                        │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│      agent2im-scheduler             │
│   (定时任务调度)                     │
│   No exposed port                   │
└─────────────────────────────────────┘
```

## 🚀 快速开始

### 本地开发
```bash
# 开发模式（支持热重载）
make dev
```

### 生产部署

#### 首次部署所有服务
```bash
make docker-up
```

#### 只部署 API 服务
```bash
make api-up
```

#### 只部署 Scheduler 服务
```bash
make scheduler-up
```

## 🔧 常用命令

### API 服务管理（独立部署）

| 命令 | 说明 | 使用场景 |
|------|------|----------|
| `make api-build` | 构建 API 镜像 | 修改了 Dockerfile 或依赖 |
| `make api-up` | 启动 API 服务 | 首次启动或停止后重新启动 |
| `make api-restart` | 重启 API 服务 | 修改了配置文件（热重载） |
| `make api-rebuild` | **重新构建并部署** | ⭐ 修改了 API 代码（推荐） |
| `make api-logs` | 查看 API 日志 | 调试和监控 |
| `make api-down` | 停止 API 服务 | 临时停止服务 |

### Scheduler 服务管理（独立部署）

| 命令 | 说明 | 使用场景 |
|------|------|----------|
| `make scheduler-build` | 构建 Scheduler 镜像 | 修改了 Dockerfile 或依赖 |
| `make scheduler-up` | 启动 Scheduler 服务 | 首次启动或停止后重新启动 |
| `make scheduler-restart` | 重启 Scheduler 服务 | 修改了配置文件（热重载） |
| `make scheduler-rebuild` | **重新构建并部署** | ⭐ 修改了 Scheduler 代码（推荐） |
| `make scheduler-logs` | 查看 Scheduler 日志 | 调试和监控 |
| `make scheduler-down` | 停止 Scheduler 服务 | 临时停止服务 |

### 综合管理

| 命令 | 说明 |
|------|------|
| `make docker-up` | 启动所有服务 |
| `make docker-down` | 停止所有服务 |
| `make docker-logs` | 查看所有服务日志 |
| `make docker-ps` | 查看容器状态 |
| `make help` | 查看所有可用命令 |

## 📋 典型使用场景

### 场景 1️⃣：只修改了 API 代码，重新部署 API

```bash
# 一键重新构建并部署 API（不影响 Scheduler）
make api-rebuild

# 命令会自动：
# 1. 构建新的 API 镜像
# 2. 停止旧的 API 容器
# 3. 启动新的 API 容器
# 4. 显示实时日志
```

**效果**：
- ✅ API 服务更新完成
- ✅ Scheduler 服务不受影响，继续运行
- ✅ 无需重启整个系统

### 场景 2️⃣：只修改了配置文件

```bash
# 修改配置文件后，只需重启服务即可
make api-restart
# 或
make scheduler-restart

# 配置文件通过 volumes 挂载，重启即可生效
```

### 场景 3️⃣：查看特定服务的日志

```bash
# 只查看 API 日志
make api-logs

# 只查看 Scheduler 日志
make scheduler-logs

# 查看所有服务日志
make docker-logs
```

### 场景 4️⃣：首次部署或更新所有服务

```bash
# 首次部署
make docker-up

# 更新所有服务
cd docker && docker compose up -d --build
```

### 场景 5️⃣：临时停止某个服务

```bash
# 停止 API（Scheduler 继续运行）
make api-down

# 停止 Scheduler（API 继续运行）
make scheduler-down

# 停止所有服务
make docker-down
```

## 🔍 监控和调试

### 查看容器状态
```bash
make docker-ps

# 输出示例：
# NAME                  IMAGE           STATUS         PORTS
# agent2im-api          ...            Up 2 hours     0.0.0.0:9000->9000/tcp
# agent2im-scheduler    ...            Up 2 hours
```

### 查看实时日志
```bash
# API 日志
make api-logs

# Scheduler 日志
make scheduler-logs

# 所有日志
make docker-logs
```

### 进入容器调试
```bash
# 进入 API 容器
docker exec -it agent2im-api bash

# 进入 Scheduler 容器
docker exec -it agent2im-scheduler bash
```

### 健康检查
```bash
# API 健康检查
curl http://localhost:9000/health

# 查看健康检查日志
docker inspect agent2im-api | jq '.[0].State.Health'
```

## 📝 配置文件管理

配置文件通过 volumes 挂载，修改后重启即可生效：

```yaml
volumes:
  # 配置文件（挂载为只读）
  - ../backend/src/config/labor_hour.yaml:/app/backend/src/config/labor_hour.yaml:ro
  - ../backend/src/config/approval.yaml:/app/backend/src/config/approval.yaml:ro
  - ../backend/src/config/news.yaml:/app/backend/src/config/news.yaml:ro
  # 日志目录（可读写）
  - ./logs:/app/logs
```

**修改配置后**：
```bash
# 只重启相关服务即可
make api-restart
# 或
make scheduler-restart
```

## 🐛 常见问题

### Q1: 修改代码后 API 没有更新？
```bash
# 确保使用 rebuild 命令（而不是 restart）
make api-rebuild
```

### Q2: 如何只更新一个服务而不影响另一个？
```bash
# API 和 Scheduler 完全独立，只需操作对应的服务
make api-rebuild        # 只更新 API
make scheduler-rebuild  # 只更新 Scheduler
```

### Q3: 端口被占用？
```bash
# 查看哪个进程占用了 9000 端口
lsof -i :9000

# 修改 docker-compose.yml 中的端口映射
ports:
  - "9001:9000"  # 改为其他端口
```

### Q4: 如何完全重新部署？
```bash
# 停止并删除所有容器和镜像
cd docker
docker compose down
docker compose up -d --build

# 或使用简化命令
make docker-down
make docker-up
```

### Q5: 日志文件在哪里？
```bash
# 容器日志
docker logs agent2im-api
docker logs agent2im-scheduler

# 应用日志（挂载到宿主机）
ls -la docker/logs/

# 实时查看
make api-logs
```

## 🔐 生产环境建议

1. **使用环境变量管理敏感信息**
   ```bash
   # 不要将敏感信息写入配置文件
   # 使用环境变量或 secrets 管理
   ```

2. **配置日志轮转**
   ```yaml
   logging:
     driver: "json-file"
     options:
       max-size: "10m"
       max-file: "3"
   ```

3. **设置资源限制**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '1'
         memory: 512M
   ```

4. **使用 restart 策略**
   ```yaml
   restart: unless-stopped
   ```

5. **定期备份日志**
   ```bash
   # 定期备份 docker/logs/ 目录
   ```

## 📊 性能优化

### 镜像大小优化
当前使用 `python:3.11-slim` 基础镜像，已经很精简。

### 启动时间优化
- API 服务约 10 秒启动
- Scheduler 服务约 5 秒启动

### 资源使用
- API: 约 100-200MB 内存
- Scheduler: 约 50-100MB 内存

## 🔗 相关链接

- [Docker Compose 文档](https://docs.docker.com/compose/)
- [飞书开放平台](https://open.feishu.cn/)
- [项目主 README](../README.md)

## 💡 技巧

```bash
# 快速查看所有可用命令
make help

# 一键重新部署 API 并查看日志
make api-rebuild

# 同时查看多个容器的日志
docker logs -f agent2im-api agent2im-scheduler

# 查看容器资源占用
docker stats agent2im-api agent2im-scheduler
```

---

**🎯 记住**：修改 API 代码后，使用 `make api-rebuild`，而不是 `make docker-up`！
