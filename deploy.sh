#!/bin/bash

# 自动化部署脚本
# 功能：拉取git代码，停止和删除当前容器、删除镜像，构建新镜像并启动项目

# 配置参数
REPO_URL="https://github.com/demoadminjie/a-share-platform-stocks-selection.git" # 替换为你的Git仓库URL
IMAGE_NAME="stock-platform-scanner" # 镜像名称
CONTAINER_NAME="stock-scanner-container" # 容器名称
HOST_PORT=8001 # 宿主机端口
CONTAINER_PORT=8001 # 容器端口
DATA_DIR="/home/ubuntu/scanner-data" # 宿主机数据目录，用于持久化存储

# 打印日志函数
echo_log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# 1. 拉取最新的git代码
echo_log "开始拉取最新的git代码..."
if [ -d ".git" ]; then
    git pull origin main # 替换为你的主分支名称
else
    echo_log "当前目录不是git仓库，正在克隆..."
    git clone $REPO_URL .
fi

# 2. 停止并删除当前运行的容器
echo_log "停止并删除当前运行的容器..."
if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
    echo_log "容器已停止并删除"
else
    echo_log "没有找到运行中的$CONTAINER_NAME容器"
fi

# 3. 删除旧的镜像
echo_log "删除旧的镜像..."
if [ "$(docker images -q $IMAGE_NAME)" ]; then
    docker rmi $IMAGE_NAME -f
    echo_log "旧镜像已删除"
else
    echo_log "没有找到$IMAGE_NAME镜像"
fi

# 4. 构建新的镜像
echo_log "构建新的镜像..."
docker build -t $IMAGE_NAME .

if [ $? -eq 0 ]; then
    echo_log "镜像构建成功"
else
    echo_log "错误：镜像构建失败"
    exit 1
fi

# 5. 启动新的容器
echo_log "启动新的容器..."

# 确保数据目录存在
if [ ! -d "$DATA_DIR" ]; then
    echo_log "创建数据目录: $DATA_DIR"
    mkdir -p $DATA_DIR
fi

# 启动容器并挂载数据卷
docker run -d \
    --name $CONTAINER_NAME \
    -p $HOST_PORT:$CONTAINER_PORT \
    -v $DATA_DIR:/app/data \
    $IMAGE_NAME

if [ $? -eq 0 ]; then
    echo_log "容器启动成功!"
    echo_log "服务已部署完成，请访问 http://43.153.175.167/:$HOST_PORT"
else
    echo_log "错误：容器启动失败"
    exit 1
fi

echo_log "部署脚本执行完毕"