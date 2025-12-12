
"""Lightweight inference server module.

This module provides a LightServer class to easily wrap synchronous model inference logic
into an asynchronous FastAPI service with thread-safe communication.
"""

import asyncio
import inspect
import json
import logging
import queue
import threading
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

# Configure library logger
logger = logging.getLogger("LightInfer")
handler = logging.StreamHandler()
formatter = logging.Formatter("[LightInfer] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class InferRequest(BaseModel):
    """Request schema for inference."""
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}
    stream: bool = False
    media_type: str = "text/event-stream"
    chunk_size: Optional[int] = None


class AsyncResponseBridge:
    """Bridge for communication between Sync Worker and Async Consumer.

    Allows a synchronous worker thread to feed data into an asyncio queue without blocking
    waiting threads on the consumer side.
    """

    def __init__(self):
        self._loop = asyncio.get_running_loop()
        self._queue = asyncio.Queue()

    def put(self, item: Any) -> None:
        """Put an item into the queue from a synchronous thread.

        Args:
            item: The item to put into the queue.
        """
        self._loop.call_soon_threadsafe(self._queue.put_nowait, item)

    async def get(self) -> Any:
        """Get an item from the queue asynchronously.

        Returns:
            The next item from the queue.
        """
        return await self._queue.get()


class LightServer:
    """A lightweight server for wrapping model inference code."""

    def __init__(self, worker_list: List[Any]):
        """Initialize the LightServer.

        Args:
            worker_list: A list of model instances to be used as workers.
        """
        self._worker_list = worker_list
        self._app = FastAPI()
        # Input Queue: Thread-safe queue for sending tasks to workers.
        self._queue = queue.Queue()
        self._setup_routes()
        self._start_workers()

    def _start_workers(self) -> None:
        """Start worker threads for each model in the worker list."""
        for i, model in enumerate(self._worker_list):
            t = threading.Thread(
                target=self._worker_loop, args=(i, model), daemon=True
            )
            t.start()
            logger.info(f"Worker thread {i} started")

    def _setup_routes(self) -> None:
        """Define and register FastAPI routes."""

        @self._app.post("/api/v1/infer")
        async def infer(request: InferRequest):
            """Handle inference requests."""
            stream = request.stream
            media_type = request.media_type
            chunk_size = request.chunk_size
            # use bridge for efficient async waiting
            response_channel = AsyncResponseBridge()

            self._queue.put(
                (request.args, request.kwargs, stream, response_channel)
            )

            if stream:
                return StreamingResponse(
                    self._stream_generator(response_channel, media_type, chunk_size),
                    media_type=media_type,
                )
            else:
                try:
                    # Non-blocking wait
                    result = await response_channel.get()

                    if isinstance(result, Exception):
                        raise result

                    return JSONResponse(content=result)
                except Exception as e:
                    logger.error(f"Inference error: {e}")
                    raise HTTPException(status_code=500, detail=str(e))

        @self._app.get("/healthz")
        async def healthz():
            """Health check endpoint."""
            return {"status": "ok", "queue_size": self._queue.qsize()}

    async def _stream_generator(
        self,
        channel: AsyncResponseBridge,
        media_type: str,
        chunk_size: Optional[int] = None,
    ):
        """Generate streaming response from the bridge channel.

        Args:
            channel: The bridge channel to read from.
            media_type: The media type of the response.
            chunk_size: The size of data chunks to yield (for binary data).

        Yields:
            Server-Sent Event (SSE) formatted strings or raw data.
        """
        buffer = b""
        while True:
            item = await channel.get()

            if item is None:  # End of stream sentinel
                if buffer:
                    yield buffer
                break

            if isinstance(item, Exception):
                logger.error(f"Stream error: {item}")
                if media_type == "text/event-stream":
                    yield f"data: Error: {str(item)}\n\n"
                break

            if media_type == "text/event-stream":
                # JSON encode the result for transport
                yield f"data: {json.dumps(item)}\n\n"
            else:
                if chunk_size and isinstance(item, bytes):
                    buffer += item
                    while len(buffer) >= chunk_size:
                        yield buffer[:chunk_size]
                        buffer = buffer[chunk_size:]
                else:
                    yield item

    def _worker_loop(self, worker_id: int, model: Any) -> None:
        """Main loop for worker threads.

        Args:
            worker_id: The ID of the worker.
            model: The model instance for this worker.
        """
        # Determine if the model's infer method is async or sync
        infer_func = getattr(model, "infer")
        is_async_model = inspect.iscoroutinefunction(infer_func)

        while True:
            try:
                args, kwargs, stream, channel = self._queue.get()

                try:
                    if is_async_model:
                        # Run async model in a new event loop (synchronously for this thread)
                        res = asyncio.run(infer_func(*args, **kwargs))
                    else:
                        res = infer_func(*args, **kwargs)

                    if stream:
                        # Handle generator output
                        if inspect.isgenerator(res) or inspect.isiterator(res):
                            iterator = res
                        else:
                            iterator = iter(res)

                        for item in iterator:
                            channel.put(item)
                        channel.put(None)  # End sentinel
                    else:
                        channel.put(res)

                except Exception as e:
                    logger.error(f"Worker {worker_id} prediction failed: {e}")
                    if stream:
                        channel.put(e)
                        channel.put(None)
                    else:
                        channel.put(e)

            except Exception as outer_e:
                logger.critical(f"Critical error in worker {worker_id}: {outer_e}")

    def start(self, port: int = 8000, host: str = "0.0.0.0") -> None:
        """Start the HTTP server.

        Args:
            port: The port to listen on.
            host: The host to bind to.
        """
        loading_msg = (
            f"Starting server on {host}:{port} with "
            f"{len(self._worker_list)} workers"
        )
        logger.info(loading_msg)
        uvicorn.run(self._app, host=host, port=port)
