FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# 设置时区为东八区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 复制requirements.txt并安装依赖
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY backend/ ./backend/

# 复制启动脚本
COPY docker/start.sh ./start.sh
RUN chmod +x start.sh

# 设置环境变量
ENV PYTHONPATH=/app/backend
ENV PYTHONUNBUFFERED=1

# 创建日志目录
RUN mkdir -p /app/logs

# 暴露API端口
EXPOSE 9000

# 健康检查
HEALTHCHECK --interval=60s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:9000/health || exit 1

# 启动应用
CMD ["/app/start.sh"]
