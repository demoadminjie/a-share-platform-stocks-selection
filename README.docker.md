# Docker 部署指南

本指南提供了如何在Linux环境中使用Docker部署股票平台期扫描工具后端服务的详细步骤。

## 前提条件

- 已安装Docker（请参考[Docker官方文档](https://docs.docker.com/engine/install/)进行安装）
- Linux系统用户权限（能够执行Docker命令）

## 构建Docker镜像

1. 进入项目根目录

```bash
cd /path/to/a-share-platform-stocks-selection
```

2. 构建Docker镜像

```bash
docker build -t stock-platform-scanner .
```

这将使用项目根目录中的`Dockerfile`构建一个名为`stock-platform-scanner`的Docker镜像。构建过程中会自动安装所有必要的依赖项。

## 运行Docker容器

### 基本运行方式

```bash
docker run -d -p 8001:8001 --name stock-scanner-container stock-platform-scanner
```

这个命令会：
- 以后台模式（-d）运行容器
- 将容器的8001端口映射到主机的8001端口（-p 8001:8001）
- 给容器命名为`stock-scanner-container`
- 使用之前构建的`stock-platform-scanner`镜像

### 持久化日志（可选）

如果你希望保存应用程序的日志，可以将日志目录映射到主机：

```bash
docker run -d -p 8001:8001 -v /path/to/logs:/app/logs --name stock-scanner-container stock-platform-scanner
```

请确保主机上的`/path/to/logs`目录已存在并具有正确的权限。

## 容器管理命令

### 查看容器状态

```bash
docker ps -a | grep stock-scanner-container
```

### 查看容器日志

```bash
docker logs stock-scanner-container
```

实时查看日志：

```bash
docker logs -f stock-scanner-container
```

### 进入容器内部（调试用）

```bash
docker exec -it stock-scanner-container /bin/bash
```

### 停止容器

```bash
docker stop stock-scanner-container
```

### 启动已停止的容器

```bash
docker start stock-scanner-container
```

### 删除容器

```bash
docker rm stock-scanner-container
```

## 服务访问

服务启动后，可以通过以下URL访问：

```
http://<your-server-ip>:8001
```

## 常见问题排查

1. **无法访问服务**
   - 检查Docker容器是否正在运行：`docker ps -a | grep stock-scanner-container`
   - 检查端口映射是否正确：`docker port stock-scanner-container`
   - 检查Linux防火墙是否允许8001端口的流量

2. **容器启动后立即退出**
   - 查看容器日志以获取错误信息：`docker logs stock-scanner-container`
   - 检查应用程序是否有配置问题

3. **构建镜像失败**
   - 检查网络连接是否正常
   - 查看构建过程中的错误信息，针对具体错误进行修复

## 性能优化建议

- 在生产环境中，可以考虑使用Docker Compose来管理服务
- 根据实际需求调整容器的资源限制（如CPU和内存）
- 定期更新Docker镜像以获取最新的依赖和安全修复

## 注意事项

- 本服务使用Baostock作为数据源，请确保网络连接能够访问Baostock API
- 容器内部的时间可能与主机时间不一致，如有时间相关的问题，可以考虑在启动容器时同步时区
- 在生产环境中，建议添加健康检查和自动重启策略，以提高服务的可靠性

```bash
docker run -d -p 8001:8001 --name stock-scanner-container --restart unless-stopped stock-platform-scanner
```