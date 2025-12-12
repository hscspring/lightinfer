import time
import logging
import math
from typing import Iterator

# Note: In a real environment, you would import from lightinfer directly
# from lightinfer.server import LightServer
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lightinfer.server import LightServer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StreamingTTS:
    """
    A minimal example of a Text-to-Audio model (TTS).
    
    Demonstrates:
    - Returning binary data (Generator[bytes])
    - Setting up the request for correct buffering
    """
    
    def __init__(self):
        logger.info("Initializing StreamingTTS...")
    
    def infer(self, text: str) -> Iterator[bytes]:
        """
        Simulates generating audio chunks.
        
        Args:
            text: Input text to synthesize.
            
        Yields:
            bytes: Raw audio data (simulated).
        """
        logger.info(f"Synthesizing audio for: '{text}'")
        
        # Simulate generating a wav header or just raw samples
        # Here we just generate silence/noise for demonstration
        sample_rate = 24000
        duration_sec = 2
        num_chunks = 20
        chunk_size = int(sample_rate * duration_sec / num_chunks)
        
        for i in range(num_chunks):
            time.sleep(0.1)  # Simulate real-time factor
            
            # Generate dummy bytes
            # meaningful audio would go here
            yield b'\x00' * chunk_size

if __name__ == "__main__":
    model = StreamingTTS()
    server = LightServer(worker_list=[model])
    
    print("Starting Streaming TTS Server...")
    print("You can test it with:")
    print('  curl -N -X POST "http://localhost:8001/api/v1/infer" \\')
    print('  -H "Content-Type: application/json" \\')
    # Note: chunk_size=4096 is just an example, it tells the server how to buffer response chunks
    print('  -d \'{"args": ["Hello"], "stream": true, "media_type": "audio/wav", "chunk_size": 4096}\' > output.wav')
    
    server.start(port=8001)
