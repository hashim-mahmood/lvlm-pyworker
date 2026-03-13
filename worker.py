import os
from vastai import Worker, WorkerConfig, HandlerConfig, BenchmarkConfig

def calculate_workload(req_body):
    """
    Estimates the compute cost of the request for the autoscaler.
    For a VLM, you could parse the prompt length, but a flat rate is
    often sufficient to tell the engine that the worker is occupied.
    """
    return 100.0

def main():
    # 1. Route Handler: Proxies Vast payload to your FastAPI app
    infer_handler = HandlerConfig(
        route="/infer",
        backend_url="http://127.0.0.1:8080/infer",  # Matches the Uvicorn host/port
        allow_parallel_requests=True,               # vLLM handles concurrent batching
        workload_calculator=calculate_workload
    )

    # 2. Benchmark Configuration: Allows Vast to score the H200's throughput
    # Vast runs this once on boot to ensure the instance is healthy.
    benchmark = BenchmarkConfig(
        backend_url="http://127.0.0.1:8080/infer",
        # This dummy payload matches your InferenceRequest Pydantic model
        payload={
            "file_b64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=", # 1x1 pixel base64 PNG
            "mime_type": "image/png",
            "prompt": "benchmark test",
            "custom_flag": False,
            "aggregated_page_context": False
        },
        complexity_score=100.0 
    )

    # 3. Initialize and run the PyWorker
    config = WorkerConfig(
        handlers=[infer_handler],
        benchmark=benchmark,
    )
    
    worker = Worker(config)
    worker.run()

if __name__ == "__main__":
    main()