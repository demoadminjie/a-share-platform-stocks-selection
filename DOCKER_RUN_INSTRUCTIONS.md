# Docker部署说明

本文件提供了如何将Python API服务打包成Docker镜像并运行的详细步骤。

## 构建Docker镜像

在项目根目录下执行以下命令：

```bash
docker build -t stock-platform-scanner .
```

这个命令会根据当前目录下的Dockerfile构建一个名为`stock-platform-scanner`的镜像。

## 运行Docker容器

构建完成后，可以通过以下命令运行Docker容器：

```bash
docker run -d -p 8001:8001 --name stock-scanner-api stock-platform-scanner
```

这个命令会：
- 以后台模式运行容器 (`-d`)
- 将容器的8001端口映射到主机的8001端口 (`-p 8001:8001`)
- 给容器命名为`stock-scanner-api`
- 使用之前构建的`stock-platform-scanner`镜像

## 验证服务是否正常运行

服务启动后，可以通过以下方式验证服务是否正常运行：

1. 访问根端点检查健康状态：

```bash
curl http://localhost:8001/
```

如果服务正常运行，你应该会收到类似以下的响应：

```json
{
  "status": "ok",
  "message": "Stock Platform Scanner API is running",
  "version": "1.0.0"
}
```

2. 你也可以使用Postman或其他API测试工具来测试更复杂的API端点，例如：

- `POST http://localhost:8001/api/scan/start` - 开始股票扫描任务
- `GET http://localhost:8001/api/scan/test` - 获取测试数据

## 查看容器日志

如果需要查看容器运行日志，可以使用以下命令：

```bash
docker logs stock-scanner-api
```

如果需要持续查看日志，可以添加`-f`参数：

```bash
docker logs -f stock-scanner-api
```

## 停止和移除容器

要停止正在运行的容器：

```bash
docker stop stock-scanner-api
```

要移除已停止的容器：

```bash
docker rm stock-scanner-api
```

## 其他Docker命令

查看所有运行中的容器：
```bash
docker ps
```

查看所有镜像：
```bash
docker images
```

删除镜像：
```bash
docker rmi stock-platform-scanner
```

## 注意事项

1. 服务默认监听8001端口
2. 在生产环境中，建议使用Docker Compose或Kubernetes进行更复杂的部署管理
3. 如需修改API配置，可以通过环境变量或修改配置文件来实现