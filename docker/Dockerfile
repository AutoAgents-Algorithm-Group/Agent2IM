FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements.txt并安装依赖
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY backend/ ./backend/

# 复制启动脚本
COPY docker/start.sh ./
RUN chmod +x start.sh

# 设置环境变量
ENV PYTHONPATH=/app/backend
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 9000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:9000/ || exit 1

# 启动应用
CMD ["./start.sh"]