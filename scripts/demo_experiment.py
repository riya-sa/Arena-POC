"""
Demo: End-to-end experiment execution.

Shows:
1. Create benchmark with Java tasks
2. Register model candidates
3. Submit experiment
4. Start worker to process jobs
5. Monitor results

Run this script, then start the worker in another terminal:
    python scripts/run_worker.py --worker-id demo-worker --max-jobs 6

This demo will:
- Create 1 benchmark with 2 tasks
- Register 1 Mock candidate (no cost)
- Submit experiment with 3 repetitions
- Generate 2 * 1 * 3 = 6 jobs
- Worker processes all 6 jobs
"""

import requests
import json
import time
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api/v1"


def pretty_print(title: str, data: Any):
    """Pretty print JSON response."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")
    if isinstance(data, dict) or isinstance(data, list):
        print(json.dumps(data, indent=2, default=str))
    else:
        print(data)


def wait_for_queue_empty(timeout: int = 60):
    """Wait for queue to be empty (all jobs processed)."""
    print(f"\n⏳ Waiting for queue to empty (max {timeout}s)...")
    start = time.time()
    
    while time.time() - start < timeout:
        response = requests.get(f"{BASE_URL}/queue/stats")
        stats = response.json()
        queue_size = stats.get("queue_size", 0)
        
        if queue_size == 0:
            print("✅ Queue is empty!")
            return True
        
        print(f"  Queue size: {queue_size}, Processed: {stats['statuses'].get('completed', 0)}")
        time.sleep(2)
    
    print(f"⏳ Timeout waiting for queue ({timeout}s)")
    return False


def main():
    """Run demo."""
    print("\n" + "#"*70)
    print("# C/AI Arena POC - Experiment Demo")
    print("#"*70)
    
    # Check API is running
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health")
        if response.status_code != 200:
            print("\n❌ API not responding. Start the API first:")
            print("   docker-compose up -d")
            return False
    except Exception as e:
        print(f"\n❌ Cannot connect to API: {str(e)}")
        print("   Start the API first: docker-compose up -d")
        return False
    
    print("\n✅ API is running!")
    
    # 1. Create benchmark with 2 tasks
    print("\n" + "="*70)
    print("1. Creating benchmark with 2 Java tasks...")
    print("="*70)
    
    benchmark_payload = {
        "name": "Demo Experiment Benchmark",
        "description": "Quick benchmark for demo",
        "tasks": [
            {
                "task_id": "demo-001",
                "problem_statement": "Write a function that returns the sum of two integers.",
                "category": "basics",
                "difficulty": 1,
                "public_tests": [
                    {"name": "test1", "input": "(1, 2)", "expected": "3"}
                ]
            },
            {
                "task_id": "demo-002",
                "problem_statement": "Check if a string is a palindrome.",
                "category": "strings",
                "difficulty": 1,
                "public_tests": [
                    {"name": "test1", "input": '"racecar"', "expected": "true"}
                ]
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/benchmarks", json=benchmark_payload)
    benchmark = response.json()
    benchmark_id = benchmark["id"]
    version_id = benchmark["versions"][0]["id"]
    
    pretty_print("Created Benchmark", {"id": benchmark_id, "tasks": 2})
    
    # Publish version
    print("\n2. Publishing benchmark version...")
    response = requests.post(
        f"{BASE_URL}/benchmarks/{benchmark_id}/versions/{version_id}/publish"
    )
    if response.status_code == 200:
        print("✅ Version published (immutable)")
    else:
        print(f"❌ Failed to publish: {response.text}")
        return False
    
    # 2. Register Mock candidate (for testing)
    print("\n" + "="*70)
    print("3. Registering Mock candidate...")
    print("="*70)
    
    candidate_payload = {
        "name": "Demo Mock",
        "provider": "mock",
        "description": "Mock for demo (no API cost)",
        "version": {
            "version_number": "1.0",
            "model_id": "demo-mock",
            "config": {"temperature": 0.7, "max_tokens": 2048}
        }
    }
    
    response = requests.post(f"{BASE_URL}/candidates", json=candidate_payload)
    candidate = response.json()
    candidate_id = candidate["id"]
    candidate_version_id = candidate["versions"][0]["id"]
    
    pretty_print("Registered Candidate", {"id": candidate_id, "versions": 1})
    
    # 3. Submit experiment
    print("\n" + "="*70)
    print("4. Submitting experiment...")
    print("="*70)
    print("   2 tasks × 1 candidate × 3 repetitions = 6 jobs")
    print("   Waiting for worker to process...")
    
    experiment_payload = {
        "benchmark_version_id": benchmark_id,
        "candidate_version_ids": [candidate_version_id],
        "name": "Demo Experiment",
        "repetitions": 3
    }
    
    response = requests.post(f"{BASE_URL}/experiments", json=experiment_payload)
    if response.status_code != 201:
        print(f"❌ Failed to create experiment: {response.text}")
        return False
    
    experiment = response.json()
    experiment_id = experiment["id"]
    
    pretty_print("Created Experiment", {
        "id": experiment_id,
        "status": experiment["status"],
        "submitted_at": experiment["submitted_at"]
    })
    
    # Check queue stats
    response = requests.get(f"{BASE_URL}/queue/stats")
    stats = response.json()
    pretty_print("Queue Stats (After Submission)", stats)
    
    # 4. Wait for worker to process jobs
    print("\n" + "="*70)
    print("5. Waiting for worker to process jobs...")
    print("="*70)
    print("\n📝 Open another terminal and run:")
    print("   python scripts/run_worker.py --worker-id demo-worker --max-jobs 6")
    print("\nThen press Enter when ready...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\n⏹️  Demo cancelled")
        return False
    
    # Wait for queue to empty
    if not wait_for_queue_empty(timeout=120):
        print("⚠️  Queue still has jobs. Worker may be running or failed.")
    
    # 5. Get experiment results
    print("\n" + "="*70)
    print("6. Experiment Results")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/experiments/{experiment_id}")
    experiment_result = response.json()
    pretty_print("Final Experiment Status", {
        "id": experiment_result["id"],
        "status": experiment_result["status"],
        "total_executions": experiment_result.get("total_executions"),
        "completed_executions": experiment_result.get("completed_executions"),
        "failed_executions": experiment_result.get("failed_executions")
    })
    
    # List executions
    response = requests.get(f"{BASE_URL}/experiments/{experiment_id}/executions")
    executions = response.json()
    
    print(f"\n✅ {len(executions)} Executions:")
    for i, exe in enumerate(executions[:3], 1):
        print(f"\n   Execution {i}:")
        print(f"     Status: {exe['status']}")
        print(f"     Latency: {exe['latency_ms']}ms")
        print(f"     Tokens: {exe['input_tokens']} in, {exe['output_tokens']} out")
        if exe['passed'] is not None:
            print(f"     Passed: {exe['passed']}")
    
    if len(executions) > 3:
        print(f"\n   ... and {len(executions) - 3} more")
    
    print("\n" + "="*70)
    print("✅ Demo Complete!")
    print("="*70)
    print(f"""
What happened:
  1. Created benchmark with 2 Java tasks
  2. Registered 1 Mock candidate (no API cost)
  3. Submitted experiment (3 repetitions = 6 jobs)
  4. Worker processed all 6 jobs
  5. Results stored in database

Next steps:
  • Metrics: Latency, tokens, cost collected per execution
  • Evaluation: (Week 7) Java code compilation + testing
  • Comparison: (Week 10) Compare models side-by-side

Run another demo with different candidates:
  • Create experiment with GPT-4 + Claude
  • Set budget_usd to cap spending
  • Worker will execute on all models in parallel
    """)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)