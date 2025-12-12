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
