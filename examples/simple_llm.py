import time
import logging
from typing import Iterator

# Note: In a real environment, you would import from lightinfer directly
# from lightinfer.server import LightServer
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lightinfer.server import LightServer

# Configure logging to see server output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleLLM:
    """
    A minimal example of a Text-to-Text model (LLM).
    """
    
    def __init__(self):
        logger.info("Initializing SimpleLLM...")
    
    def infer(self, prompt: str, steps: int = 10) -> Iterator[str]:
        """
        Simulates generating text token by token.
        
        Args:
            prompt: The input text.
            steps: Number of tokens to generate.
            
        Yields:
            str: Generated text tokens.
        """
        logger.info(f"Received prompt: {prompt}")
        yield f"Thinking about '{prompt}'...\n"
        
        for i in range(steps):
            time.sleep(0.2)  # Simulate inference latency
            yield f"token_{i} "

if __name__ == "__main__":
    # Create an instance of your model
    model = SimpleLLM()
    
    # Initialize the server with your model worker(s)
    server = LightServer(worker_list=[model])
    
    print("Starting Simple LLM Server...")
    print("You can test it with:")
    print('  curl -N -X POST "http://localhost:8000/api/v1/infer" \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"args": ["Hello World"], "kwargs": {"steps": 5}, "stream": true}\'')
    
    server.start(port=8000)
