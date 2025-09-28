FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制requirements.txt并安装依赖
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY src/ ./src/
COPY src/config/config.yaml .

# 暴露端口
EXPOSE 9000

# 启动应用
CMD ["python", "src/api/main.py"]
