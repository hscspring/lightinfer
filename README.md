# LightInfer：同步模型推理 × 异步 Web 服务的高性能桥接器

**LightInfer** 是一个**轻量、高性能**的模型服务框架，用于将 **同步推理代码**（如 PyTorch / TensorFlow / 任意 Python 推理逻辑）**安全、高效地暴露为异步 FastAPI 服务**。

它专门解决模型服务中的一个核心工程问题：

> **如何在不阻塞事件循环的前提下，稳定、高并发地服务“重计算型同步推理代码”？**

LightInfer 的核心思路是：
**异步 Web 前端 + 专用同步 Worker 线程 + 零阻塞等待桥接**。

------

## 适用场景

LightInfer 适合以下典型场景：

- 使用 **PyTorch / TensorFlow / NumPy** 等同步推理代码
- 希望通过 **FastAPI / HTTP API** 提供高并发服务
- 不希望因 `time.sleep()`、GPU 推理、IO 阻塞而拖垮 event loop
- 需要 **流式输出**（文本 / 音频 / 二进制数据）
- 不想引入复杂的分布式系统或重量级 Serving 框架

------

## 核心特性

### 1. 零阻塞架构（Zero-Blocking Architecture）

- **异步 Web 层**：基于 FastAPI，完全非阻塞
- **同步 Worker 层**：每个模型实例运行在独立线程中
- 推理过程不会阻塞 asyncio event loop

这是一个为 **“同步推理 × 异步服务”** 专门设计的结构，而不是简单的 `run_in_executor` 包装。

------

### 2. 高效的异步-同步桥接机制

- 内置 `AsyncResponseBridge`
- **等待结果时不占用线程**
- 无 busy-wait、无额外线程池消耗
- 特别适合 **长时间推理 + 高并发请求**

------

### 3. 原生流式推理支持

LightInfer 原生支持 **生成器式推理输出**：

- **文本流式输出**
    - Server-Sent Events (SSE)
    - 适合 LLM、流式生成任务
- **二进制流式输出**
    - 直接传输 bytes
    - 适合 TTS、音频、视频、Chunk-based 生成任务

模型只需 `yield`，无需关心底层协议。

------

### 4. 极简接入方式

- **无需继承基类**
- **无需侵入式改造**
- 只要你的类有一个 `infer` 方法即可

```python
class MyModel:
    def infer(self, prompt: str):
        ...
```

HTTP JSON 中的 `args / kwargs` 会自动映射到 `infer` 的参数。

------

### 5. 线程级上下文隔离

- 每个 Worker 运行在独立线程
- 避免 PyTorch / CUDA / 第三方库的线程安全问题
- 可通过多个 Worker 实例实现并行推理

------

## 快速开始

### 1. 定义你的模型

```python
import time

class MyModel:
    def infer(self, prompt: str = "world"):
        # 模拟耗时推理
        time.sleep(1)
        return {"message": f"Hello, {prompt}!"}
```

------

### 2. 启动服务

```python
from lightinfer.server import LightServer

model = MyModel()

# 传入模型列表即可启动多个 worker 线程
server = LightServer([model])
server.start(port=8000)
```

------

### 3. 发起请求

#### 普通请求

```python
import requests

resp = requests.post(
    "http://localhost:8000/api/v1/infer",
    json={"args": ["LightInfer"]}
)
print(resp.json())
```

返回结果：

```json
{"message": "Hello, LightInfer!"}
```

------

#### 流式请求（Streaming）

如果 `infer` 返回的是 **生成器**，LightInfer 会自动启用流式响应。

```python
class StreamingModel:
    def infer(self, prompt: str):
        yield "Part 1"
        time.sleep(0.5)
        yield "Part 2"
```

客户端示例：

```python
resp = requests.post(
    "http://localhost:8000/api/v1/infer",
    json={"args": ["test"], "stream": True},
    stream=True
)

for line in resp.iter_lines():
    if line:
        print(line.decode("utf-8"))
```

------

## 示例

`examples/` 目录包含可直接运行的完整示例：

- **Simple LLM**：文本生成 + SSE 流式输出
- **Streaming TTS**：文本转音频 + 二进制分块流式传输

------

## CLI 启动方式

你也可以直接通过命令行启动服务：

```bash
lightinfer <module>:<Class>
```

示例：

```python
# my_model.py
class MyModel:
    def infer(self, prompt: str):
        return f"Echo: {prompt}"
```

启动：

```bash
lightinfer my_model:MyModel --port 8000 --workers 2
```

# LightInfer

**LightInfer** is a lightweight, high-performance bridge for serving synchronous model inference code (PyTorch, TensorFlow, etc.) via an asynchronous FastAPI server.

It solves the "Blocking Loop" problem by efficiently isolating heavy computation in dedicated worker threads while maintaining a fully asynchronous, high-concurrency web frontend.

## Features

- **Zero-Blocking Architecture**: Async Web Frontend + Sync Worker Threads.
- **Efficient Bridge**: Uses `AsyncResponseBridge` for zero-thread-overhead waiting.
- **Streaming Support**: 
  - Native Server-Sent Events (SSE) for text streaming.
  - **Binary Streaming** for audio/video generation (with chunk buffering).
- **Easy Integration**: Wrap any Python class with an `infer` method.
- **Context Isolation**: Each worker runs in its own thread, ensuring safety for libraries like PyTorch.

## Installation

```bash
pip install lightinfer
```

## Quick Start

### 1. Define your Model

LightInfer wraps any class with an `infer` method. The arguments to `infer` are automatically mapped from the JSON request.

```python
import time

class MyModel:
    def infer(self, prompt: str = "world"):
        # Simulate heavy work
        time.sleep(1)
        return {"message": f"Hello, {prompt}!"}
```

### 2. Start the Server

```python
from lightinfer.server import LightServer

# Create your model instance
model = MyModel()

# Start server (you can pass a list of models to run multiple worker threads)
server = LightServer([model])
server.start(port=8000)
```

### 3. Make Requests

**Standard Request:**

```python
import requests

# 'args' in JSON maps to positional arguments of infer()
# 'kwargs' in JSON maps to keyword arguments of infer()
resp = requests.post("http://localhost:8000/api/v1/infer", 
                     json={"args": ["LightInfer"]})
print(resp.json())
# Output: {'message': 'Hello, LightInfer!'}
```

**Streaming Request:**

- Text: yield body, donnot dumps or encode
- Audio: yield binary directly

If your model returns a generator, you can use streaming:

```python
class StreamingModel:
    def infer(self, prompt: str):
        yield "Part 1"
        time.sleep(0.5)
        yield "Part 2"
```

Client side:

```python
resp = requests.post("http://localhost:8000/api/v1/infer", 
                     json={"args": ["test"], "stream": True}, stream=True)

for line in resp.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

## Examples

Check the `examples/` directory for ready-to-run scenarios:

- [**Simple LLM**](examples/simple_llm.py): Text-to-Text generation with SSE streaming.
- [**Streaming TTS**](examples/streaming_tts.py): Text-to-Audio generation with binary chunk streaming.

## CLI Usage

You can serve any model class directly from the terminal.

**Format**: `lightinfer <module>:<Class>`

Given a file `my_model.py`:
```python
class MyModel:
    def infer(self, prompt: str):
        return f"Echo: {prompt}"
```

Run:
```bash
lightinfer my_model:MyModel --port 8000 --workers 2
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT
