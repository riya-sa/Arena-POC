"""
Test Java code evaluation end-to-end.

Shows:
1. Submit experiment
2. Worker executes + evaluates code
3. See scores and pass/fail results

Usage:
    # Terminal 1: API + Worker
    docker-compose up -d
    python scripts/run_worker.py --worker-id eval-worker --max-jobs 4
    
    # Terminal 2: Run demo
    python scripts/test_java_evaluation.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"


def test_java_evaluation():
    """End-to-end test of Java evaluation."""
    
    print("\n" + "="*70)
    print("  Java Code Evaluation - Week 7-9 Test")
    print("="*70)
    
    # 1. Create benchmark with Java tasks
    print("\n1. Creating benchmark with Java tasks...")
    
    benchmark_payload = {
        "name": "Java Evaluation Test",
        "description": "Test Java code evaluation",
        "tasks": [
            {
                "task_id": "java-sum",
                "problem_statement": "Write a function that returns the sum of two integers.",
                "category": "basics",
                "difficulty": 1,
                "public_tests": [
                    {"name": "test1", "input": "(2, 3)", "expected": "5"},
                    {"name": "test2", "input": "(0, 0)", "expected": "0"},
                ]
            },
            {
                "task_id": "java-palindrome",
                "problem_statement": "Check if a string is a palindrome.",
                "category": "strings",
                "difficulty": 1,
                "public_tests": [
                    {"name": "test1", "input": '"racecar"', "expected": "true"},
                    {"name": "test2", "input": '"hello"', "expected": "false"},
                ]
            }
        ]
    }
    
    resp = requests.post(f"{BASE_URL}/benchmarks", json=benchmark_payload)
    if resp.status_code != 201:
        print(f"❌ Failed to create benchmark: {resp.text}")
        return False
    
    benchmark = resp.json()
    benchmark_version_id = benchmark["versions"][0]["id"]
    print(f"✅ Benchmark created with {len(benchmark_payload['tasks'])} tasks")
    
    # 2. Publish version
    print("\n2. Publishing benchmark version...")
    resp = requests.post(
        f"{BASE_URL}/benchmarks/{benchmark['id']}/versions/{benchmark_version_id}/publish",
        json={}
    )
    if resp.status_code != 200:
        print(f"❌ Failed to publish: {resp.text}")
        return False
    print("✅ Version published")
    
    # 3. Register candidate
    print("\n3. Registering Mock candidate...")
    candidate_payload = {
        "name": "Mock Evaluator",
        "provider": "mock",
        "description": "For evaluation testing",
        "version": {
            "version_number": "1.0",
            "model_id": "mock-eval",
            "config": {"temperature": 0.7, "max_tokens": 2048}
        }
    }
    
    resp = requests.post(f"{BASE_URL}/candidates", json=candidate_payload)
    if resp.status_code != 201:
        print(f"❌ Failed to register candidate: {resp.text}")
        return False
    
    candidate = resp.json()
    candidate_version_id = candidate["versions"][0]["id"]
    print(f"✅ Candidate registered: {candidate['name']}")
    
    # 4. Submit experiment
    print("\n4. Submitting experiment...")
    experiment_payload = {
        "benchmark_version_id": benchmark_version_id,
        "candidate_version_ids": [candidate_version_id],
        "name": "Java Evaluation Test",
        "repetitions": 1
    }
    
    resp = requests.post(f"{BASE_URL}/experiments", json=experiment_payload)
    if resp.status_code != 201:
        print(f"❌ Failed to submit experiment: {resp.text}")
        return False
    
    experiment = resp.json()
    experiment_id = experiment["id"]
    print(f"✅ Experiment submitted: {experiment_id}")
    print(f"   Jobs created: {experiment.get('total_jobs', 'unknown')}")
    
    # 5. Wait for worker to process
    print("\n5. Waiting for worker to process jobs...")
    print("   ⏳ Polling for completion (max 30 seconds)...")
    
    start = time.time()
    while time.time() - start < 30:
        resp = requests.get(f"{BASE_URL}/experiments/{experiment_id}")
        if resp.status_code != 200:
            continue
        
        exp = resp.json()
        completed = exp.get("completed_executions", 0)
        total = exp.get("total_executions", 0)
        
        if completed == total and total > 0:
            print(f"   ✅ All {total} jobs completed!")
            break
        
        print(f"   Progress: {completed}/{total}")
        time.sleep(1)
    
    # 6. Get results
    print("\n6. Evaluation Results:")
    print("="*70)
    
    resp = requests.get(f"{BASE_URL}/experiments/{experiment_id}/executions")
    if resp.status_code != 200:
        print(f"❌ Failed to get executions: {resp.text}")
        return False
    
    executions = resp.json()
    if isinstance(executions, dict) and "value" in executions:
        executions = executions["value"]
    
    if not executions:
        print("⚠️  No executions found")
        return False
    
    total_score = 0
    for exe in executions:
        task_id = exe.get("id", "unknown")[:8]
        status = exe.get("status", "unknown")
        score = exe.get("score", 0)
        passed = exe.get("passed", None)
        latency = exe.get("latency_ms", 0)
        
        total_score += score
        
        status_icon = "✅" if passed else "❌" if passed is False else "⚠️"
        print(f"\n{status_icon} Execution {task_id}")
        print(f"   Status: {status}")
        print(f"   Score: {score}/100")
        print(f"   Passed: {passed}")
        print(f"   Latency: {latency}ms")
    
    avg_score = total_score / len(executions) if executions else 0
    print("\n" + "="*70)
    print(f"Average Score: {avg_score:.1f}/100")
    print(f"Total Executions: {len(executions)}")
    
    return True


if __name__ == "__main__":
    try:
        success = test_java_evaluation()
        if success:
            print("\n✅ Java Evaluation Test Complete!")
        else:
            print("\n❌ Test Failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Test cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)