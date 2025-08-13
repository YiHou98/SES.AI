# 1. 使用官方的轻量级 Python 镜像
FROM python:3.11-slim

# 2. 设置容器内的工作目录
WORKDIR /app

# 3. 将 /app 目录添加到 Python 的模块搜索路径
ENV PYTHONPATH "${PYTHONPATH}:/app"

# 4. 优先复制依赖文件
COPY ./requirements.txt /app/requirements.txt

# 5. 安装 Python 依赖包
RUN pip install --timeout=600 --no-cache-dir --upgrade -r /app/requirements.txt

# 6. 最后复制你的应用程序代码
COPY ./app /app
