# LightInfer

**LightInfer** is a lightweight, high-performance bridge for serving synchronous model inference code (PyTorch, TensorFlow, etc.) via an asynchronous FastAPI server.

It solves the "Blocking Loop" problem by efficiently isolating heavy computation in dedicated worker threads while maintaining a fully asynchronous, high-concurrency web frontend.

## Features

- **Zero-Blocking Architecture**: Async Web Frontend + Sync Worker Threads.
- **Efficient Bridge**: Uses `AsyncResponseBridge` for zero-thread-overhead waiting.
- **Streaming Support**: Native Server-Sent Events (SSE) support for streaming inference.
- **Easy Integration**: Wrap any Python class with an `infer` method.
- **Context Isolation**: Each worker runs in its own thread, ensuring safety for libraries like PyTorch.

## Installation

```bash
pip install lightinfer
```

## Quick Start

### 1. Define your Model

LightInfer expects a model class with an `infer` method.

```python
import time

class MyModel:
    def infer(self, args, kwargs):
        # Simulate heavy work
        time.sleep(1)
        prompt = args[0] if args else "world"
        return {"message": f"Hello, {prompt}!"}
```

### 2. Start the Server

```python
from lightinfer.server import LightServer

# Create your model instance(s)
model = MyModel()

# Start server (you can pass a list of models to start multiple workers)
server = LightServer([model])
server.start(port=8000)
```

### 3. Make Requests

**Standard Request:**

```python
import requests

resp = requests.post("http://localhost:8000/api/v1/infer", 
                     json={"args": ["LightInfer"]})
print(resp.json())
# Output: {'message': 'Hello, LightInfer!'}
```

**Streaming Request:**

If your model returns a generator, you can use streaming:

```python
class StreamingModel:
    def infer(self, args, kwargs):
        yield "Part 1"
        time.sleep(0.5)
        yield "Part 2"

server = LightServer([StreamingModel()])
server.start(port=8001)
```

Client side:

```python
resp = requests.post("http://localhost:8001/api/v1/infer", 
                     json={"stream": True}, stream=True)

for line in resp.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

### 4. CLI Usage (Recommended)

You can also run LightInfer directly from the command line without writing a server script.

**Format**: `lightinfer <module>:<Class> [options]`

Given a file `my_model.py`:
```python
class MyModel:
    def infer(self, args, kwargs):
        return {"ans": "42"}
```

Run:
```bash
lightinfer my_model:MyModel --port 8000 --workers 2
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT
