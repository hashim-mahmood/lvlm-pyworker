"""
Vast.ai Serverless PyWorker for LVLM inference.

This worker sits between the Vast.ai serverless router and your FastAPI app,
forwarding requests to /infer and reporting metrics for autoscaling.

Place this file + requirements.txt in a **public** GitHub repo and set
PYWORKER_REPO in your Vast.ai template to point to it.
"""

from vastai import Worker, WorkerConfig, HandlerConfig, BenchmarkConfig, LogActionConfig
import base64

# Tiny 1x1 white JPEG for benchmark/health probes (68 bytes)
TINY_JPEG_B64 = (
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoH"
    "BwYIDAoMCwsKCwsKDA0QDQsNEBEQDQ4OEhMSFA4SFBkUFBcYFxoeHh7/2wBDAQME"
    "BAUEBQkFBQkeEA0QHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4e"
    "Hh4eHh4eHh4eHh7/wAARCAABAAEDASIAAhEBAxEB/8QAFAABAAAAAAAAAAAAAAAAAAAACf"
    "/EABQQAQAAAAAAAAAAAAAAAAAAAAD/xAAUAQEAAAAAAAAAAAAAAAAAAAAA/8QAFBEBAAAA"
    "AAAAAAAAAAAAAAAAAP/aAAwDAQACEQMRAD8AKwA//9k="
)


worker_config = WorkerConfig(
    model_server_url="http://127.0.0.1",
    model_server_port=8080,                         # FastAPI/Uvicorn port
    model_log_file="/dev/null",                     # Logs go to stdout
    handlers=[
        HandlerConfig(
            route="/infer",                         # Your FastAPI endpoint
            allow_parallel_requests=True,           # vLLM handles batching
            max_queue_time=120.0,                   # Max time a request can wait in queue
            workload_calculator=lambda payload: 100.0,  # Fixed cost per request
            benchmark_config=BenchmarkConfig(
                generator=lambda: {
                    "file_b64": TINY_JPEG_B64,
                    "mime_type": "image/jpeg",
                },
                runs=2,
                concurrency=1,
            ),
        ),
        HandlerConfig(
            route="/health",                        # Health check passthrough
            allow_parallel_requests=True,
            max_queue_time=10.0,
            workload_calculator=lambda payload: 1.0,
        ),
    ],
    log_action_config=LogActionConfig(
        on_load=["Application startup complete.", "Uvicorn running on"],
        on_error=["Traceback (most recent call last):", "RuntimeError:", "Error initializing"],
        on_info=["Downloading model from GCS", "Download complete"],
    ),
)

Worker(worker_config).run()
