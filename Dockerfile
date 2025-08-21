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

# 创建数据存储目录并设置正确权限
RUN mkdir -p /app/data && chmod 777 /app/data

# 声明数据卷 - 这会将容器内的/app/data目录标记为可挂载点
VOLUME /app/data

# 设置启动命令
CMD ["python", "api/run.py"]

# 数据持久化说明：
# 运行容器时使用 -v 宿主机目录:/app/data 参数来挂载宿主机目录到容器内的数据目录
# 例如：docker run -d -p 8001:8001 -v /path/on/host/data:/app/data your_image_name