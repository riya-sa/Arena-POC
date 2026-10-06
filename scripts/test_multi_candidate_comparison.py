"""
Multi-Candidate Comparison Test - Week 7-9 Advanced

Tests evaluation with 3 candidates at different quality levels:
1. High-Quality Candidate → Scores ~100/100
2. Mid-Quality Candidate → Scores ~70/100
3. Low-Quality Candidate → Scores ~40/100

This demonstrates:
- Model comparison capability
- Scoring across different candidates
- Identifying best-performing models
- Cost vs performance trade-offs

Usage:
    # Terminal 1: API + Worker
    docker-compose up -d
    python scripts/run_worker.py --worker-id eval-worker
    
    # Terminal 2: Run comparison test
    python scripts/test_multi_candidate_comparison.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import json
from collections import defaultdict

BASE_URL = "http://localhost:8000/api/v1"


def test_multi_candidate_comparison():
    """Test evaluation with multiple candidates at different quality levels."""
    
    print("\n" + "="*80)
    print("  MULTI-CANDIDATE COMPARISON - Week 7-9")
    print("="*80)
    
    # 1. Create benchmark
    print("\n1️⃣  Creating benchmark with Java tasks...")
    
    benchmark_payload = {
        "name": "Multi-Candidate Comparison",
        "description": "Test different model quality levels",
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
            },
            {
                "task_id": "java-sorting",
                "problem_statement": "Sort an array of integers.",
                "category": "algorithms",
                "difficulty": 2,
                "public_tests": [
                    {"name": "test1", "input": "[3,1,2]", "expected": "[1,2,3]"},
                    {"name": "test2", "input": "[]", "expected": "[]"},
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
    print("\n2️⃣  Publishing benchmark version...")
    resp = requests.post(
        f"{BASE_URL}/benchmarks/{benchmark['id']}/versions/{benchmark_version_id}/publish",
        json={}
    )
    if resp.status_code != 200:
        print(f"❌ Failed to publish: {resp.text}")
        return False
    print("✅ Version published")
    
    # 3. Register 3 candidates at different quality levels
    print("\n3️⃣  Registering candidates at different quality levels...")
    
    candidates = [
        {
            "name": "High-Quality Model",
            "quality": "high",
            "description": "Elite model - expects perfect solutions",
        },
        {
            "name": "Mid-Quality Model",
            "quality": "medium",
            "description": "Solid model - gets most problems right",
        },
        {
            "name": "Low-Quality Model",
            "quality": "low",
            "description": "Basic model - struggles with harder problems",
        }
    ]
    
    candidate_versions = {}
    
    for candidate_info in candidates:
        payload = {
            "name": candidate_info["name"],
            "provider": "mock",
            "description": candidate_info["description"],
            "version": {
                "version_number": "1.0",
                "model_id": f"mock-{candidate_info['quality']}",
                "config": {
                    "temperature": 0.7,
                    "max_tokens": 2048,
                    "quality_level": candidate_info["quality"]  # Key for evaluation!
                }
            }
        }
        
        resp = requests.post(f"{BASE_URL}/candidates", json=payload)
        if resp.status_code != 201:
            print(f"❌ Failed to register {candidate_info['name']}: {resp.text}")
            return False
        
        candidate = resp.json()
        candidate_versions[candidate_info["quality"]] = {
            "id": candidate["versions"][0]["id"],
            "name": candidate_info["name"]
        }
        print(f"✅ Registered: {candidate_info['name']} (quality: {candidate_info['quality']})")
    
    # 4. Submit experiments for each candidate
    print("\n4️⃣  Submitting experiments for each candidate...")
    
    experiments = {}
    
    for quality, candidate_info in candidate_versions.items():
        experiment_payload = {
            "benchmark_version_id": benchmark_version_id,
            "candidate_version_ids": [candidate_info["id"]],
            "name": f"{candidates[[c['quality'] for c in candidates].index(quality)]['name']} - Full Run",
            "repetitions": 2
        }
        
        resp = requests.post(f"{BASE_URL}/experiments", json=experiment_payload)
        if resp.status_code != 201:
            print(f"❌ Failed to submit experiment: {resp.text}")
            return False
        
        experiment = resp.json()
        experiments[quality] = {
            "id": experiment["id"],
            "total_jobs": experiment.get("total_jobs", "unknown")
        }
        print(f"✅ Experiment submitted for {quality} candidate (ID: {experiment['id'][:8]}...)")
        print(f"   Jobs queued: {experiments[quality]['total_jobs']}")
    
    # 5. Wait for all experiments to complete
    print("\n5️⃣  Waiting for worker to process all jobs...")
    print("   ⏳ Polling for completion (max 60 seconds)...")
    
    all_completed = False
    start = time.time()

    while time.time() - start < 60 and not all_completed:
        all_completed = True
        total_progress = ""  # ← CHANGE TO EMPTY STRING
    
        for quality, exp_info in experiments.items():
            resp = requests.get(f"{BASE_URL}/experiments/{exp_info['id']}")
            if resp.status_code != 200:
                all_completed = False
                continue
        
            exp = resp.json()
            completed = exp.get("completed_executions", 0)
            total = exp.get("total_executions", 0)
        
            total_progress += f"{completed}/{total};"  # ← NOW ADDING STRING TO STRING
    
               
            if completed < total:
                all_completed = False
        
        if all_completed:
            print(f"   ✅ All jobs completed!")
        else:
            print(f"   Progress: {total_progress.rstrip(';')}")
            time.sleep(2)
    
    # 6. Collect and display results
    print("\n6️⃣  COMPARISON RESULTS:")
    print("="*80)
    
    comparison_data = defaultdict(list)
    all_results = []
    
    for quality, exp_info in experiments.items():
        resp = requests.get(f"{BASE_URL}/experiments/{exp_info['id']}/executions")
        if resp.status_code != 200:
            continue
        
        executions = resp.json()
        if isinstance(executions, dict) and "value" in executions:
            executions = executions["value"]
        
        candidate_name = candidate_versions[quality]["name"]
        
        print(f"\n{'='*80}")
        print(f"📊 {candidate_name}")
        print(f"{'='*80}")
        
        total_score = 0
        task_scores = defaultdict(list)
        
        for exe in executions:
            status = exe.get("status", "unknown")
            score = exe.get("score", 0)
            passed = exe.get("passed", None)
            latency = exe.get("latency_ms", 0)
            in_tokens = exe.get("input_tokens", 0)
            out_tokens = exe.get("output_tokens", 0)
            
            total_score += score
            all_results.append({
                "quality": quality,
                "candidate": candidate_name,
                "score": score,
                "passed": passed,
                "latency_ms": latency,
                "status": status
            })
            
            status_icon = "✅" if passed else "❌" if passed is False else "⚠️"
            print(f"{status_icon} Score: {score:3d}/100 | Latency: {latency:3d}ms | Tokens: {in_tokens}→{out_tokens}")
        
        avg_score = total_score / len(executions) if executions else 0
        
        print(f"\n📈 Metrics for {candidate_name}:")
        print(f"   Average Score: {avg_score:.1f}/100")
        print(f"   Total Executions: {len(executions)}")
        print(f"   Pass Rate: {sum(1 for e in executions if e.get('passed')) / len(executions) * 100:.0f}%" if executions else "N/A")
        
        comparison_data[quality] = {
            "name": candidate_name,
            "avg_score": avg_score,
            "total": len(executions),
            "passed": sum(1 for e in executions if e.get("passed"))
        }
    
    # 7. Summary comparison
    print("\n\n" + "="*80)
    print("🏆 RANKING SUMMARY")
    print("="*80 + "\n")
    
    ranked = sorted(comparison_data.items(), key=lambda x: x[1]["avg_score"], reverse=True)
    
    for rank, (quality, data) in enumerate(ranked, 1):
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉"
        print(f"{medal} #{rank}: {data['name']}")
        print(f"       Average Score: {data['avg_score']:.1f}/100")
        print(f"       Passed Tests: {data['passed']}/{data['total']}")
        print()
    
    # 8. Insights
    print("="*80)
    print("📊 KEY INSIGHTS")
    print("="*80)
    
    best_quality = ranked[0][0]
    best_score = ranked[0][1]["avg_score"]
    worst_quality = ranked[-1][0]
    worst_score = ranked[-1][1]["avg_score"]
    
    print(f"\n✅ Best Performer: {comparison_data[best_quality]['name']} ({best_score:.1f}/100)")
    print(f"⚠️  Weakest Performer: {comparison_data[worst_quality]['name']} ({worst_score:.1f}/100)")
    print(f"📈 Performance Gap: {best_score - worst_score:.1f} points")
    
    # Cost comparison (all mock, so 0 cost)
    print(f"\n💰 Cost Analysis:")
    print(f"   All candidates: $0.00 (mock provider)")
    print(f"   → In production: Would compare token costs vs performance")
    
    print("\n" + "="*80)
    print("✅ Multi-Candidate Comparison Complete!")
    print("="*80 + "\n")
    
    return True


if __name__ == "__main__":
    try:
        success = test_multi_candidate_comparison()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Test cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)