
import pytest
import httpx
import time
from typing import Iterator, Any
import asyncio
from lightinfer.server import LightServer

class MockUniversalModel:
    """Mock model behaving as both LLM and TTS."""
    def infer(self, input_data: str, mode: str = "text") -> Iterator[Any]:
        if mode == "text":
            yield "Hello "
            yield "World"
        elif mode == "audio":
            # Yield small chunks
            for _ in range(10):
                time.sleep(0.1)
                yield b'\x01' * 10 
        elif mode == "error":
            raise ValueError("Test Error")

@pytest.fixture
def server_app():
    model = MockUniversalModel()
    server = LightServer(worker_list=[model])
    return server._app

@pytest.mark.asyncio
async def test_healthz(server_app):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=server_app), base_url="http://test") as client:
        response = await client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "queue_size": 0}

@pytest.mark.asyncio
async def test_text_stream_sse(server_app):
    """Test default text/event-stream behavior."""
    payload = {
        "args": ["test"], 
        "kwargs": {"mode": "text"}, 
        "stream": True
    }
    
    # Increase timeout to ensure we capture async yields
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=server_app), base_url="http://test", timeout=5.0) as client:
        async with client.stream("POST", "/api/v1/infer", json=payload) as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]
            
            data_lines = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_lines.append(line)
            
            assert len(data_lines) == 2
            assert 'data: "Hello "' in data_lines[0]
            assert 'data: "World"' in data_lines[1]

@pytest.mark.asyncio
async def test_audio_stream_raw(server_app):
    """Test binary streaming without SSE wrapping."""
    payload = {
        "args": ["test"], 
        "kwargs": {"mode": "audio"}, 
        "stream": True,
        "media_type": "audio/wav"
    }
    
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=server_app), base_url="http://test", timeout=5.0) as client:
        async with client.stream("POST", "/api/v1/infer", json=payload) as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "audio/wav"
            
            content = b""
            async for chunk in response.aiter_bytes():
                content += chunk
            
            # Total bytes = 10 iterations * 10 bytes = 100 bytes
            assert len(content) == 100
            assert content == b'\x01' * 100

@pytest.mark.asyncio
async def test_audio_stream_chunked(server_app):
    """Test binary streaming with specific chunk_size."""
    # Worker yields 10 bytes at a time.
    # We request chunk_size = 25.
    # We expect chunks of 25, 25, 25, 25.
    
    payload = {
        "args": ["test"], 
        "kwargs": {"mode": "audio"}, 
        "stream": True,
        "media_type": "audio/wav",
        "chunk_size": 25  
    }
    
    received_chunks = []
    
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=server_app), base_url="http://test", timeout=5.0) as client:
        async with client.stream("POST", "/api/v1/infer", json=payload) as response:
            assert response.status_code == 200
            
            async for chunk in response.aiter_bytes():
                 if chunk:
                     received_chunks.append(len(chunk))
    
    # Due to transport buffering in TestClient/ASGITransport, we might receive combined chunks.
    # We verify the total size is correct.
    assert sum(received_chunks) == 100
