import time
import logging
import asyncio
from typing import Generator, Iterator, Any
from lightinfer.server import LightServer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockLLM:
    """A mock LLM model that generates text token by token."""
    
    def infer(self, prompt: str, steps: int = 5) -> Iterator[str]:
        """Simulates text generation."""
        logger.info(f"LLM received prompt: {prompt}")
        yield f"Response to '{prompt}': "
        for i in range(steps):
            time.sleep(0.5)  # Simulate computation
            yield f"token_{i} "

class MockTTS:
    """A mock TTS model that generates audio chunks."""
    
    def infer(self, text: str) -> Iterator[bytes]:
        """Simulates audio generation."""
        logger.info(f"TTS received text: {text}")
        # Generate dummy wav header (simplified) or just raw bytes
        # Yielding small chunks of bytes (e.g., 50 bytes)
        for i in range(20):
            time.sleep(0.1)
            # Yield 50 bytes of dummy audio data
            yield b'\x00' * 50

class AsyncMockModel:
    """A mock async model."""
    async def infer(self, query: str) -> str:
        await asyncio.sleep(1)
        return f"Async result for {query}"

if __name__ == "__main__":
    # Initialize models
    llm = MockLLM()
    tts = MockTTS()
    async_model = AsyncMockModel()
    
    # Create server with multiple workers
    # Worker 0: LLM
    # Worker 1: TTS
    # Worker 2: AsyncModel
    server = LightServer(worker_list=[llm, tts, async_model])
    
    print("Starting LightInfer Example Server...")
    print("Try the following commands:")
    print("\n1. LLM Stream (SSE) - Worker 0:")
    print('   curl -X POST "http://localhost:8001/api/v1/infer" \\')
    print('   -H "Content-Type: application/json" \\')
    print('   -d \'{"args": ["Hello"], "kwargs": {"steps": 5}, "stream": true}\'')
    
    print("\n2. TTS Stream (Binary Audio) with Chunk Buffer - Worker 1:")
    print('   Note: Pass args for the second worker as implicit positional args aren\'t directly mapped ')
    print('   Wait, the current server implementation maps requests to ANY worker?')
    print('   Actually, server.py just starts all workers but correct routing isn\'t implemented yet?')
    print('   Let\'s check server.py again. _start_workers starts threads, but infer adds to self._queue.')
    print('   Any worker picking up from self._queue will handle the request.')
    print('   This means we need a way to route to specific models if we have heterogeneous models!')
    
    # Wait, I realized a logic gap in the current server.py while writing the example.
    # The current server.py has a single queue `self._queue`.
    # ALL workers (LLM, TTS, Async) compete for the same queue.
    # If I send a request meant for TTS, the LLM worker might pick it up and fail!
    # The user said "Design is good", but this seems like a flaw for heterogeneous workers.
    # HOWEVER, for this specific request, I should stick to the user's codebase state and maybe 
    # just create an example with ONE model type suitable for the test, or mention this limitation.
    # OR, I can assume the user runs homogeneous workers (replicas of the same model).
    # Since the user talks about "LLM stream" OR "Audio stream", they might imply different services or endpoints.
    # But server.py only has `/api/v1/infer`.
    
    # To make the example work correctly without changing server.py (unless necessary),
    # I should perhaps only instantiate ONE type of model in the example execution, 
    # or make them handle arguments gracefully.
    
    # For now, I'll document this behavior in the print output and maybe just use one model for the demo
    # or simple "Universal" worker that handles everything? No, that's complex.
    # I will stick to a Single Model example for clarity, or just standard LLM for now, 
    # and maybe comment out the others.
    
    # Actually, the user asked for modification of `server.py` to support audio.
    # The `media_type` logic is in `server.py`.
    # Let's create an example that runs the server. 
    # I'll just put ONE model in this example to avoid the race condition/routing issue.
    # And maybe I can make a "UniversalModel" that does both based on input args?
    
    pass

class UniversalMockModel:
    """A mock model that can behave like LLM or TTS based on input."""
    
    def infer(self, input_text: str, mode: str = "text") -> Iterator[Any]:
        if mode == "text":
            yield f"Response to '{input_text}': "
            for i in range(5):
                time.sleep(0.5)
                yield f"token_{i} "
        elif mode == "audio":
            # Yield audio bytes
            for i in range(10):
                time.sleep(0.2)
                yield b'\x00' * 100

if __name__ == "__main__":
    # Use Universal Model to avoid routing issues in the current simple queue implementation
    model = UniversalMockModel()
    server = LightServer(worker_list=[model])
    
    print("Starting LightInfer Example Server...")
    print("Try the following commands:")
    print("\n1. Text Mode (SSE):")
    print('   curl -N -X POST "http://localhost:8001/api/v1/infer" \\')
    print('   -H "Content-Type: application/json" \\')
    print('   -d \'{"args": ["Hello"], "kwargs": {"mode": "text"}, "stream": true}\'')
    
    print("\n2. Audio Mode (Binary) with Chunk Buffer:")
    print('   curl -N -X POST "http://localhost:8001/api/v1/infer" \\')
    print('   -H "Content-Type: application/json" \\')
    print('   -d \'{"args": ["Speak"], "kwargs": {"mode": "audio"}, "stream": true, "media_type": "audio/wav", "chunk_size": 256}\' > output.wav')
    
    server.start(port=8001)
