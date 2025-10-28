# Docker 部署指南

## 📋 服务说明

本项目包含两个 Docker 服务：

1. **API 服务** (`agent2im-api`)
   - 提供 HTTP API 接口
   - 处理飞书审批回调
   - 端口：9000

2. **调度器服务** (`agent2im-scheduler`)
   - 执行定时任务
   - 工时检查（晚上 19:30 和早上 10:30）
   - 月度总结（每月 28 号 10:00）
   - AI 新闻推送（可选）

## 🚀 快速启动

### 1. 准备配置文件

确保以下配置文件已正确配置：

```bash
backend/src/config/
├── labor_hour.yaml   # 工时检查配置（必需）
├── approval.yaml     # 审批服务配置（必需）
└── news.yaml         # 新闻推送配置（可选）
```

### 2. 构建并启动服务

```bash
# 进入 docker 目录
cd docker

# 启动所有服务
docker-compose up -d

# 或者分别启动
docker-compose up -d api        # 仅启动 API 服务
docker-compose up -d scheduler  # 仅启动调度器
```

### 3. 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f api
docker-compose logs -f scheduler
```

### 4. 停止服务

```bash
docker-compose down
```

## 📊 健康检查

### API 服务
```bash
curl http://localhost:9000/health
```

### 调度器服务
```bash
docker-compose exec scheduler pgrep -f unified_scheduler
```

## 🔧 配置说明

### docker-compose.yml

配置文件挂载（只读模式）：
- `labor_hour.yaml` - 工时检查配置
- `approval.yaml` - 审批服务配置
- `news.yaml` - 新闻推送配置

日志目录挂载：
- `./logs` - 应用日志输出目录

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `SERVICE_TYPE` | 服务类型 (api/scheduler) | api |
| `PYTHONPATH` | Python 模块路径 | /app/backend |
| `PYTHONUNBUFFERED` | 禁用 Python 缓冲 | 1 |
| `TZ` | 时区 | Asia/Shanghai |

## 📦 依赖要求

- Docker Engine 20.10+
- Docker Compose 2.0+
- 至少 512MB RAM
- 至少 1GB 磁盘空间

## 🔄 更新部署

```bash
# 拉取最新代码
git pull origin main

# 重新构建镜像
docker-compose build

# 重启服务
docker-compose up -d
```

## 🐛 故障排查

### 1. 配置文件找不到

**错误**: `config file not found`

**解决**: 
- 检查配置文件路径是否正确
- 确保配置文件存在于 `backend/src/config/` 目录

### 2. 调度器未运行

**错误**: 健康检查失败

**解决**:
```bash
# 查看详细日志
docker-compose logs scheduler

# 检查进程
docker-compose exec scheduler ps aux | grep python
```

### 3. API 服务无法访问

**错误**: `Connection refused`

**解决**:
- 检查端口 9000 是否被占用
- 查看 API 服务日志
- 确认防火墙设置

### 4. 时区不正确

**解决**:
- 确认 `TZ=Asia/Shanghai` 环境变量已设置
- 重新构建镜像

## 📝 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看资源使用
docker stats agent2im-api agent2im-scheduler

# 进入容器
docker-compose exec api bash
docker-compose exec scheduler bash

# 重启服务
docker-compose restart

# 清理所有容器和镜像
docker-compose down --rmi all -v
```

## 🔐 安全建议

1. **生产环境部署**:
   - 使用环境变量或 Docker secrets 管理敏感信息
   - 配置文件使用只读挂载 (`:ro`)
   - 限制容器权限

2. **网络安全**:
   - 使用反向代理（如 Nginx）
   - 启用 HTTPS
   - 配置防火墙规则

3. **日志管理**:
   - 定期清理日志文件
   - 使用日志聚合工具（如 ELK）
   - 设置日志轮转

## 📚 相关文档

- [配置文件说明](../backend/src/config/README_CONFIG.md)
- [API 文档](http://localhost:9000/docs) (启动后访问)
- [项目主 README](../README-CN.md)

