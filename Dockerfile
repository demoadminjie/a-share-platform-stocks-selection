# 使用官方Python镜像作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 更新apt源并安装必要的系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements.txt文件到工作目录
COPY api/requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制整个项目到工作目录
COPY . .

# 确保run.py可执行
RUN chmod +x api/run.py

# 暴露端口8001
EXPOSE 8001

# 设置启动命令
CMD ["python", "api/run.py"]