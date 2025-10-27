# 🚀 部署指南

快速部署 HR 小助手到你的服务器

---

## 📋 服务器信息

- **服务器 IP**: `45.78.224.30`
- **API 端口**: `9000`
- **回调地址**: `http://45.78.224.30:9000/feishu/approval/callback`

---

## 🔧 部署步骤

### 1. 确保防火墙开放端口

```bash
# 开放 9000 端口
sudo ufw allow 9000

# 查看防火墙状态
sudo ufw status
```

### 2. 配置文件检查

确保以下配置文件已正确填写：

```bash
# 检查配置文件
ls -la backend/src/config/

# 必需的配置文件:
# ✅ labor_hour.json  - 包含 app_id 和 app_secret
# ✅ people.json      - 人员名单
# ✅ scheduled_tasks.json - 定时任务配置
```

### 3. 启动服务

```bash
# 进入项目目录
cd /Users/forhheart/AIGC/Agent2IM

# 启动所有服务（API + 调度器）
docker compose -f docker/docker-compose.yml up -d

# 查看服务状态
docker compose -f docker/docker-compose.yml ps

# 应该看到两个服务:
# - agent2im-api        (运行中)
# - agent2im-scheduler  (运行中)
```

### 4. 验证服务

```bash
# 检查 API 服务健康状态
curl http://localhost:9000/health

# 预期响应:
# {"status":"ok"}

# 从外部访问（如果有公网 IP）
curl http://45.78.224.30:9000/health
```

### 5. 配置飞书事件订阅

在飞书开放平台配置：
- **请求地址**: `http://45.78.224.30:9000/feishu/approval/callback`
- **订阅事件**: `approval_instance`

### 6. 测试回调

```bash
# 测试 URL 验证
curl -X POST 'http://45.78.224.30:9000/feishu/approval/callback' \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "url_verification",
    "challenge": "test_challenge"
  }'

# 预期响应:
# {"challenge":"test_challenge"}
```

---

## 📊 查看日志

### API 服务日志

```bash
# 实时查看日志
docker compose -f docker/docker-compose.yml logs -f api

# 查看最近 100 行日志
docker compose -f docker/docker-compose.yml logs --tail=100 api
```

### 调度器日志

```bash
# 实时查看调度器日志
docker compose -f docker/docker-compose.yml logs -f scheduler

# 查看最近 100 行日志
docker compose -f docker/docker-compose.yml logs --tail=100 scheduler
```

### 查看所有服务日志

```bash
docker compose -f docker/docker-compose.yml logs -f
```

---

## 🔄 重启服务

```bash
# 重启所有服务
docker compose -f docker/docker-compose.yml restart

# 只重启 API 服务
docker compose -f docker/docker-compose.yml restart api

# 只重启调度器
docker compose -f docker/docker-compose.yml restart scheduler
```

---

## 🛑 停止服务

```bash
# 停止所有服务
docker compose -f docker/docker-compose.yml down

# 停止并删除数据卷
docker compose -f docker/docker-compose.yml down -v
```

---

## 🔍 故障排查

### 问题 1: 端口被占用

```bash
# 查看 9000 端口是否被占用
sudo lsof -i :9000

# 或使用
sudo netstat -tunlp | grep 9000

# 如果被占用，停止占用的进程或修改端口
```

### 问题 2: 服务无法启动

```bash
# 查看详细日志
docker compose -f docker/docker-compose.yml logs api

# 检查配置文件路径是否正确
docker compose -f docker/docker-compose.yml exec api ls -la /app/backend/src/config/
```

### 问题 3: 外部无法访问

```bash
# 1. 检查防火墙
sudo ufw status

# 2. 检查端口监听
sudo netstat -tunlp | grep 9000

# 3. 测试本地访问
curl http://localhost:9000/health

# 4. 如果本地可以，外部不行，检查云服务器安全组
# 确保在云服务商控制台开放了 9000 端口
```

### 问题 4: 飞书验证失败

```bash
# 1. 确认服务已启动
docker ps | grep agent2im-api

# 2. 测试回调接口
curl -X POST 'http://45.78.224.30:9000/feishu/approval/callback' \
  -H 'Content-Type: application/json' \
  -d '{"type":"url_verification","challenge":"test"}'

# 3. 查看实时日志
docker compose -f docker/docker-compose.yml logs -f api
```

---

## 📈 性能优化

### 1. 日志管理

日志配置（已在 docker-compose.yml 中配置）:
- 单个日志文件最大 10MB
- 保留最近 3 个日志文件
- 自动轮转

### 2. 资源限制（可选）

如需限制资源使用，可在 docker-compose.yml 中添加：

```yaml
api:
  deploy:
    resources:
      limits:
        cpus: '1.0'
        memory: 512M
      reservations:
        cpus: '0.5'
        memory: 256M
```

---

## 🔐 安全建议

### 1. 生产环境使用 HTTPS

**不推荐**（开发环境）:
```
http://45.78.224.30:9000/feishu/approval/callback
```

**推荐**（生产环境）:
```
https://your-domain.com/feishu/approval/callback
```

### 2. 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location /feishu/ {
        proxy_pass http://localhost:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. 配置文件权限

```bash
# 限制配置文件权限
chmod 600 backend/src/config/labor_hour.json
chmod 600 backend/src/config/people.json

# 只允许当前用户读取
ls -la backend/src/config/
```

---

## 🎯 部署检查清单

部署完成后，请确认：

- [ ] 防火墙已开放 9000 端口
- [ ] Docker 服务已启动
- [ ] API 服务健康检查通过 (`http://localhost:9000/health`)
- [ ] 外部可以访问 API (`http://45.78.224.30:9000/health`)
- [ ] 飞书事件订阅配置完成
- [ ] URL 验证测试通过
- [ ] 配置文件已正确填写
- [ ] 日志输出正常

---

## 📞 快速命令参考

```bash
# 启动服务
docker compose -f docker/docker-compose.yml up -d

# 查看状态
docker compose -f docker/docker-compose.yml ps

# 查看日志
docker compose -f docker/docker-compose.yml logs -f

# 重启服务
docker compose -f docker/docker-compose.yml restart

# 停止服务
docker compose -f docker/docker-compose.yml down

# 健康检查
curl http://localhost:9000/health

# 测试回调
curl -X POST http://45.78.224.30:9000/feishu/approval/callback \
  -H 'Content-Type: application/json' \
  -d '{"type":"url_verification","challenge":"test"}'
```

---

## 🔗 相关文档

- [快速开始](./QUICKSTART_APPROVAL.md) - 5分钟快速配置
- [详细配置指南](./SETUP_HR_ASSISTANT.md) - 完整配置步骤
- [Docker Compose 配置](./docker/docker-compose.yml) - 服务编排配置

---

**🎉 部署完成后，你的 HR 小助手就可以接收飞书审批回调了！**

