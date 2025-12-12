# LightInfer Examples

This directory contains examples of how to use `LightInfer` for different scenarios.

## Scenarios

### 1. Simple LLM (Text-to-Text)
**File**: `simple_llm.py`
Demonstrates basic text generation with streaming support.

**Run with Python**:
```bash
# Ensure root directory is in PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)/..
python examples/simple_llm.py
```

**Run with CLI**:
```bash
# Ensure root directory is in PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)
# Uses the class MockLLM defined inside the file (or SimpleLLM if that's the class name)
python -m lightinfer.cli examples.simple_llm:SimpleLLM --host 0.0.0.0 --port 8000
```

### 2. Streaming TTS (Text-to-Audio)
**File**: `streaming_tts.py`
Demonstrates generating binary audio data (bytes validation) with chunk buffering.

**Run with Python**:
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/..
python examples/streaming_tts.py
```

**Run with CLI**:
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
python -m lightinfer.cli examples.streaming_tts:StreamingTTS --host 0.0.0.0 --port 8001
```

## Testing Requests

**Text Mode (SSE)**:
```bash
curl -N -X POST "http://localhost:8000/api/v1/infer" \
  -H "Content-Type: application/json" \
  -d '{"args": ["Hello"], "kwargs": {"steps": 10}, "stream": true}'
```

**Audio Mode (Binary)**:
```bash
curl -N -X POST "http://localhost:8001/api/v1/infer" \
  -H "Content-Type: application/json" \
  -d '{"args": ["Speak"], "stream": true, "media_type": "audio/wav", "chunk_size": 4096}' > output.wav
```
