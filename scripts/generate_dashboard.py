"""
Week 10: Results Dashboard Generator

Generates an interactive HTML dashboard showing:
- Model rankings and scores
- Task-by-task performance breakdown
- Cost vs performance analysis
- Executive summary and insights

Usage:
    python scripts/generate_dashboard.py
    
Output:
    dashboard.html (opens in browser)
"""

import sys
from pathlib import Path
import json
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import Execution, CandidateVersion, Candidate, Task

# Connect to database
engine = create_engine(settings.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()


def get_dashboard_data():
    """Query database and aggregate results for dashboard."""
    
    # Get all completed executions with evaluations
    executions = db.query(Execution).filter(
        Execution.status == "complete",
        Execution.evaluation_details.isnot(None)
    ).all()
    
    if not executions:
        print("❌ No completed executions found with evaluation details")
        return None
    
    # Aggregate by candidate
    candidate_stats = {}
    task_scores = {}
    
    for exe in executions:
        # Get candidate info
        cv = exe.candidate_version
        candidate = cv.candidate
        candidate_key = candidate.name
        
        # Get task info
        task = exe.task
        task_key = task.task_id
        
        # Initialize
        if candidate_key not in candidate_stats:
            candidate_stats[candidate_key] = {
                "total_executions": 0,
                "completed_executions": 0,
                "passed_executions": 0,
                "total_score": 0,
                "latencies": [],
                "input_tokens": 0,
                "output_tokens": 0,
                "cost": 0,
                "scores": []
            }
        
        if task_key not in task_scores:
            task_scores[task_key] = {}
        
        if candidate_key not in task_scores[task_key]:
            task_scores[task_key][candidate_key] = {
                "scores": [],
                "passed": 0,
                "total": 0
            }
        
        # Aggregate metrics
        candidate_stats[candidate_key]["total_executions"] += 1
        candidate_stats[candidate_key]["completed_executions"] += 1
        candidate_stats[candidate_key]["total_score"] += exe.score or 0
        candidate_stats[candidate_key]["scores"].append(exe.score or 0)
        candidate_stats[candidate_key]["latencies"].append(exe.latency_ms or 0)
        candidate_stats[candidate_key]["input_tokens"] += exe.input_tokens or 0
        candidate_stats[candidate_key]["output_tokens"] += exe.output_tokens or 0
        candidate_stats[candidate_key]["cost"] += float(exe.cost_usd or 0)
        
        if exe.passed:
            candidate_stats[candidate_key]["passed_executions"] += 1
        
        # Task-level aggregation
        task_scores[task_key][candidate_key]["scores"].append(exe.score or 0)
        task_scores[task_key][candidate_key]["total"] += 1
        if exe.passed:
            task_scores[task_key][candidate_key]["passed"] += 1
    
    # Calculate averages
    for candidate_key, stats in candidate_stats.items():
        if stats["total_executions"] > 0:
            stats["avg_score"] = int(stats["total_score"] / stats["total_executions"])
            stats["avg_latency"] = int(sum(stats["latencies"]) / len(stats["latencies"]))
            stats["pass_rate"] = int((stats["passed_executions"] / stats["total_executions"]) * 100)
        else:
            stats["avg_score"] = 0
            stats["avg_latency"] = 0
            stats["pass_rate"] = 0
    
    # Calculate task averages
    for task_key, candidates in task_scores.items():
        for candidate_key, scores in candidates.items():
            if scores["scores"]:
                scores["avg_score"] = int(sum(scores["scores"]) / len(scores["scores"]))
            else:
                scores["avg_score"] = 0
    
    return {
        "candidates": candidate_stats,
        "tasks": task_scores,
        "timestamp": datetime.now().isoformat()
    }


def generate_html(data):
    """Generate HTML dashboard from data."""
    
    if not data:
        return None
    
    candidates = data["candidates"]
    tasks = data["tasks"]
    
    # Sort candidates by score (descending)
    sorted_candidates = sorted(
        candidates.items(),
        key=lambda x: x[1]["avg_score"],
        reverse=True
    )
    
    # Build task comparison table
    task_rows = ""
    for task_key, task_data in sorted(tasks.items()):
        row = f"<tr><td><strong>{task_key}</strong></td>"
        for candidate_key, _ in sorted_candidates:
            score = task_data.get(candidate_key, {}).get("avg_score", 0)
            row += f'<td><span class="score-badge" style="background: {get_score_color(score)}">{score}</span></td>'
        row += "</tr>"
        task_rows += row
    
    # Build comparison table header
    candidate_headers = "".join([
        f"<th>{name}</th>"
        for name, _ in sorted_candidates
    ])
    
    # Build ranking badges
    ranking_html = ""
    medals = ["🥇", "🥈", "🥉"]
    for rank, (candidate_key, stats) in enumerate(sorted_candidates):
        medal = medals[rank] if rank < 3 else "⭐"
        ranking_html += f"""
        <div class="ranking-card">
            <div class="medal">{medal}</div>
            <div class="rank">#{rank + 1}</div>
            <div class="name">{candidate_key}</div>
            <div class="score">{stats['avg_score']}/100</div>
            <div class="metrics">
                <span>✅ {stats['passed_executions']}/{stats['total_executions']} Passed</span>
                <span>⏱️  {stats['avg_latency']}ms Avg</span>
            </div>
        </div>
        """
    
    # Build detailed stats table
    detailed_rows = ""
    for candidate_key, stats in sorted_candidates:
        cost_str = f"${stats['cost']:.4f}" if stats['cost'] > 0 else "Free"
        detailed_rows += f"""
        <tr>
            <td><strong>{candidate_key}</strong></td>
            <td>{stats['avg_score']}</td>
            <td>{stats['passed_executions']}/{stats['total_executions']}</td>
            <td>{stats['pass_rate']}%</td>
            <td>{stats['avg_latency']}ms</td>
            <td>{stats['input_tokens']:,}</td>
            <td>{stats['output_tokens']:,}</td>
            <td>{cost_str}</td>
        </tr>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>C/AI Arena POC - Results Dashboard</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 40px 20px;
            }}
            
            .container {{
                max-width: 1400px;
                margin: 0 auto;
            }}
            
            header {{
                text-align: center;
                color: white;
                margin-bottom: 40px;
            }}
            
            header h1 {{
                font-size: 2.5em;
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
            }}
            
            header p {{
                font-size: 1.1em;
                opacity: 0.9;
            }}
            
            .dashboard {{
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
            }}
            
            .section {{
                padding: 40px;
                border-bottom: 1px solid #eee;
            }}
            
            .section:last-child {{
                border-bottom: none;
            }}
            
            .section h2 {{
                font-size: 1.8em;
                color: #333;
                margin-bottom: 30px;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            
            .ranking-container {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            
            .ranking-card {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                transition: transform 0.3s ease;
            }}
            
            .ranking-card:hover {{
                transform: translateY(-5px);
            }}
            
            .medal {{
                font-size: 3em;
                margin-bottom: 10px;
            }}
            
            .rank {{
                font-size: 0.9em;
                opacity: 0.9;
                margin-bottom: 10px;
            }}
            
            .ranking-card .name {{
                font-size: 1.3em;
                font-weight: 600;
                margin-bottom: 15px;
            }}
            
            .ranking-card .score {{
                font-size: 2.5em;
                font-weight: 700;
                margin-bottom: 20px;
            }}
            
            .ranking-card .metrics {{
                display: flex;
                flex-direction: column;
                gap: 8px;
                font-size: 0.9em;
                opacity: 0.95;
            }}
            
            .metrics span {{
                display: block;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            
            th {{
                background: #f5f5f5;
                padding: 15px;
                text-align: left;
                font-weight: 600;
                color: #333;
                border-bottom: 2px solid #667eea;
            }}
            
            td {{
                padding: 15px;
                border-bottom: 1px solid #eee;
            }}
            
            tr:hover {{
                background: #f9f9f9;
            }}
            
            .score-badge {{
                display: inline-block;
                padding: 8px 16px;
                border-radius: 20px;
                color: white;
                font-weight: 600;
                text-align: center;
                min-width: 60px;
            }}
            
            .insights {{
                background: #f0f7ff;
                border-left: 4px solid #667eea;
                padding: 20px;
                border-radius: 8px;
                margin-top: 20px;
            }}
            
            .insights h3 {{
                color: #667eea;
                margin-bottom: 15px;
                font-size: 1.2em;
            }}
            
            .insights ul {{
                list-style: none;
                padding-left: 0;
            }}
            
            .insights li {{
                padding: 8px 0;
                color: #333;
                line-height: 1.6;
            }}
            
            .insights li:before {{
                content: "✓ ";
                color: #667eea;
                font-weight: 700;
                margin-right: 8px;
            }}
            
            .chart-container {{
                position: relative;
                height: 400px;
                margin-top: 30px;
            }}
            
            .metric-row {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }}
            
            .metric-card {{
                background: #f5f5f5;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }}
            
            .metric-label {{
                color: #666;
                font-size: 0.9em;
                margin-bottom: 10px;
            }}
            
            .metric-value {{
                font-size: 2em;
                font-weight: 700;
                color: #667eea;
            }}
            
            .timestamp {{
                text-align: center;
                color: #999;
                font-size: 0.9em;
                margin-top: 20px;
                padding-top: 20px;
                border-top: 1px solid #eee;
            }}
            
            .footer {{
                background: #f5f5f5;
                padding: 20px;
                text-align: center;
                color: #666;
                font-size: 0.9em;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🎯 C/AI Arena POC - Results Dashboard</h1>
                <p>Multi-Candidate Benchmark Comparison Report</p>
            </header>
            
            <div class="dashboard">
                <!-- Rankings Section -->
                <div class="section">
                    <h2>🏆 Model Rankings</h2>
                    <div class="ranking-container">
                        {ranking_html}
                    </div>
                </div>
                
                <!-- Performance Summary -->
                <div class="section">
                    <h2>📊 Detailed Performance Metrics</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Model</th>
                                <th>Avg Score</th>
                                <th>Tests Passed</th>
                                <th>Pass Rate</th>
                                <th>Avg Latency</th>
                                <th>Input Tokens</th>
                                <th>Output Tokens</th>
                                <th>Cost</th>
                            </tr>
                        </thead>
                        <tbody>
                            {detailed_rows}
                        </tbody>
                    </table>
                </div>
                
                <!-- Task Breakdown -->
                <div class="section">
                    <h2>📋 Task-by-Task Score Breakdown</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Task</th>
                                {candidate_headers}
                            </tr>
                        </thead>
                        <tbody>
                            {task_rows}
                        </tbody>
                    </table>
                </div>
                
                <!-- Key Insights -->
                <div class="section">
                    <h2>💡 Key Insights</h2>
                    <div class="insights">
                        {generate_insights(sorted_candidates, tasks)}
                    </div>
                </div>
                
                <!-- Cost vs Performance -->
                <div class="section">
                    <h2>💰 Cost vs Performance Analysis</h2>
                    <div class="metric-row">
                        {generate_cost_metrics(sorted_candidates)}
                    </div>
                </div>
                
                <div class="timestamp">
                    Generated: {data['timestamp']}
                </div>
            </div>
            
            <div class="footer">
                <p>C/AI Arena POC - Week 1-10 Implementation</p>
                <p>Architecture: FastAPI + PostgreSQL + Worker Queue + Code Evaluator</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def get_score_color(score):
    """Get color based on score."""
    if score >= 90:
        return "#22c55e"  # Green
    elif score >= 70:
        return "#f59e0b"  # Orange
    else:
        return "#ef4444"  # Red


def generate_insights(sorted_candidates, tasks):
    """Generate key insights HTML."""
    
    best_model = sorted_candidates[0][0]
    best_score = sorted_candidates[0][1]["avg_score"]
    worst_model = sorted_candidates[-1][0]
    worst_score = sorted_candidates[-1][1]["avg_score"]
    gap = best_score - worst_score
    
    # Find best and worst tasks
    task_avgs = {}
    for task_key, candidates in tasks.items():
        scores = [c["avg_score"] for c in candidates.values()]
        task_avgs[task_key] = sum(scores) / len(scores) if scores else 0
    
    best_task = max(task_avgs.items(), key=lambda x: x[1])[0]
    worst_task = min(task_avgs.items(), key=lambda x: x[1])[0]
    
    html = f"""
    <h3>Executive Summary</h3>
    <ul>
        <li><strong>Clear Winner:</strong> {best_model} with {best_score}/100 average score</li>
        <li><strong>Performance Gap:</strong> {gap} points between best and worst performer</li>
        <li><strong>Best Task:</strong> {best_task} (avg {task_avgs[best_task]:.0f}/100)</li>
        <li><strong>Most Challenging Task:</strong> {worst_task} (avg {task_avgs[worst_task]:.0f}/100)</li>
        <li><strong>Recommendation:</strong> Deploy {best_model} for production use</li>
    </ul>
    """
    
    return html


def generate_cost_metrics(sorted_candidates):
    """Generate cost metrics HTML."""
    
    html = ""
    for candidate_key, stats in sorted_candidates:
        html += f"""
        <div class="metric-card">
            <div class="metric-label">{candidate_key}</div>
            <div class="metric-value">{stats['avg_score']}</div>
            <div class="metric-label">Performance Score</div>
        </div>
        """
    
    return html


def main():
    """Generate and save dashboard."""
    
    print("\n" + "="*70)
    print("  C/AI Arena POC - Results Dashboard Generator")
    print("="*70 + "\n")
    
    print("1️⃣  Querying database for results...")
    data = get_dashboard_data()
    
    if not data:
        print("❌ Failed to generate dashboard")
        return False
    
    print(f"✅ Found {sum(len(v['scores']) for v in data['candidates'].values())} total executions")
    
    print("\n2️⃣  Generating HTML dashboard...")
    html = generate_html(data)
    
    if not html:
        print("❌ Failed to generate HTML")
        return False
    
    # Save to file
    output_path = Path(__file__).parent.parent / "dashboard.html"
    with open(output_path, "w") as f:
        f.write(html)
    
    print(f"✅ Dashboard saved to: {output_path}")
    
    print("\n3️⃣  Opening dashboard in browser...")
    import webbrowser
    webbrowser.open(f"file://{output_path.absolute()}")
    
    print("\n" + "="*70)
    print("✅ Dashboard Generated Successfully!")
    print("="*70)
    print(f"\n📊 Models compared: {len(data['candidates'])}")
    print(f"📋 Tasks evaluated: {len(data['tasks'])}")
    print(f"⚡ Total executions: {sum(len(v['scores']) for v in data['candidates'].values())}")
    
    print("\n💡 Key Metrics:")
    for candidate_key, stats in sorted(
        data['candidates'].items(),
        key=lambda x: x[1]['avg_score'],
        reverse=True
    ):
        print(f"   {candidate_key}: {stats['avg_score']}/100")
    
    print("\n" + "="*70 + "\n")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()