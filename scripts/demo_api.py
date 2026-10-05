"""
Demo script: Using C/AI Arena POC API

Shows how to:
1. Create benchmarks
2. Register candidate models
3. Check model health
4. Estimate model costs
5. (Future) Run experiments

Run after the API is started:
    python scripts/demo_api.py
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api/v1"


def pretty_print(title: str, data: Any):
    """Pretty print JSON response."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    if isinstance(data, dict) or isinstance(data, list):
        print(json.dumps(data, indent=2, default=str))
    else:
        print(data)


def demo_benchmarks():
    """Demo: Create and manage benchmarks."""
    print("\n" + "="*60)
    print("  BENCHMARKS API")
    print("="*60)
    
    # 1. Create a benchmark
    print("\n1. Creating benchmark...")
    benchmark_payload = {
        "name": "Java Programming Basics",
        "description": "Basic Java programming tasks",
        "tasks": [
            {
                "task_id": "java-001",
                "problem_statement": "Write a function that adds two numbers.",
                "category": "basics",
                "difficulty": 1,
                "public_tests": [
                    {"name": "test1", "input": "(1, 2)", "expected": "3"}
                ]
            },
            {
                "task_id": "java-002",
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
    
    pretty_print("Created Benchmark", benchmark)
    
    # 2. List benchmarks
    print("\n2. Listing benchmarks...")
    response = requests.get(f"{BASE_URL}/benchmarks")
    benchmarks = response.json()
    pretty_print("All Benchmarks", benchmarks)
    
    # 3. Get specific benchmark
    print("\n3. Getting specific benchmark...")
    response = requests.get(f"{BASE_URL}/benchmarks/{benchmark_id}")
    pretty_print("Specific Benchmark", response.json())
    
    # 4. Publish version
    print("\n4. Publishing benchmark version...")
    response = requests.post(
        f"{BASE_URL}/benchmarks/{benchmark_id}/versions/{version_id}/publish"
    )
    pretty_print("Published Version", response.json())
    
    return benchmark_id


def demo_candidates():
    """Demo: Register and manage model candidates."""
    print("\n" + "="*60)
    print("  CANDIDATES API")
    print("="*60)
    
    # 1. Register mock model (no API key needed)
    print("\n1. Registering mock model (for testing)...")
    candidate_payload = {
        "name": "Mock Claude",
        "provider": "mock",
        "description": "Mock adapter for testing (returns canned code)",
        "version": {
            "version_number": "1.0",
            "model_id": "mock-claude",
            "config": {
                "temperature": 0.7,
                "max_tokens": 2048
            }
        }
    }
    
    response = requests.post(f"{BASE_URL}/candidates", json=candidate_payload)
    candidate = response.json()
    candidate_id = candidate["id"]
    
    pretty_print("Created Candidate (Mock)", candidate)
    
    # 2. List candidates
    print("\n2. Listing all candidates...")
    response = requests.get(f"{BASE_URL}/candidates")
    candidates = response.json()
    pretty_print("All Candidates", candidates)
    
    # 3. Get specific candidate
    print("\n3. Getting specific candidate...")
    response = requests.get(f"{BASE_URL}/candidates/{candidate_id}")
    pretty_print("Specific Candidate", response.json())
    
    # 4. Check health
    print("\n4. Checking candidate health...")
    response = requests.post(f"{BASE_URL}/candidates/{candidate_id}/health")
    pretty_print("Health Check", response.json())
    
    # 5. Estimate cost
    print("\n5. Estimating cost for a task...")
    response = requests.get(f"{BASE_URL}/candidates/{candidate_id}/cost-estimate")
    pretty_print("Cost Estimate", response.json())
    
    # 6. Create a new version
    print("\n6. Creating new candidate version...")
    version_payload = {
        "version_number": "1.1",
        "model_id": "mock-claude-v1.1",
        "config": {
            "temperature": 0.5,
            "max_tokens": 4096
        }
    }
    response = requests.post(
        f"{BASE_URL}/candidates/{candidate_id}/versions",
        json=version_payload
    )
    pretty_print("New Candidate Version", response.json())
    
    # 7. List versions
    print("\n7. Listing candidate versions...")
    response = requests.get(f"{BASE_URL}/candidates/{candidate_id}/versions")
    pretty_print("Candidate Versions", response.json())
    
    # Also register OpenAI and Anthropic candidates (without real keys, they won't work)
    print("\n8. Registering OpenAI candidate (requires API key to use)...")
    openai_payload = {
        "name": "GPT-4",
        "provider": "openai",
        "description": "OpenAI GPT-4 (requires API key)",
        "version": {
            "version_number": "1.0",
            "model_id": "gpt-4",
            "config": {
                "temperature": 0.7,
                "max_tokens": 2048,
                "input_price_per_1k_tokens": 0.01,
                "output_price_per_1k_tokens": 0.03
            }
        }
    }
    response = requests.post(f"{BASE_URL}/candidates", json=openai_payload)
    pretty_print("Registered GPT-4", response.json())
    
    print("\n9. Registering Anthropic candidate (requires API key to use)...")
    anthropic_payload = {
        "name": "Claude 3.5 Sonnet",
        "provider": "anthropic",
        "description": "Anthropic Claude 3.5 Sonnet (requires API key)",
        "version": {
            "version_number": "1.0",
            "model_id": "claude-3-5-sonnet-20241022",
            "config": {
                "temperature": 0.7,
                "max_tokens": 2048,
                "input_price_per_1k_tokens": 0.003,
                "output_price_per_1k_tokens": 0.015
            }
        }
    }
    response = requests.post(f"{BASE_URL}/candidates", json=anthropic_payload)
    pretty_print("Registered Claude", response.json())
    
    return candidate_id


def main():
    """Run all demos."""
    print("\n" + "#"*60)
    print("# C/AI Arena POC - API Demo")
    print("#"*60)
    
    # Check API is running
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health")
        if response.status_code != 200:
            print("\n❌ API not responding. Start the API first:")
            print("   docker-compose up -d")
            return
    except Exception as e:
        print(f"\n❌ Cannot connect to API: {str(e)}")
        print("   Start the API first: docker-compose up -d")
        return
    
    print("\n✅ API is running!")
    
    try:
        # Run demos
        benchmark_id = demo_benchmarks()
        candidate_id = demo_candidates()
        
        print("\n" + "="*60)
        print("  NEXT STEPS")
        print("="*60)
        print(f"""
You now have:
  • Benchmark ID: {benchmark_id}
  • Candidate (Mock) ID: {candidate_id}

Next week (Week 5-6):
  1. Create Experiment API (queue tasks)
  2. Implement Worker Pool (execute tasks)
  3. Collect Metrics (latency, tokens, cost)
  4. Evaluate Code (Java compilation + tests)

Try the interactive API docs:
  • http://localhost:8000/docs
  • http://localhost:8000/redoc
        """)
        
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()