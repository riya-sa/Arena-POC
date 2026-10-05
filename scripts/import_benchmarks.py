"""
Import benchmark tasks from JSON file or create sample Java tasks.

Usage:
    python scripts/import_benchmarks.py --source file.json
    python scripts/import_benchmarks.py --samples 30
"""

import json
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, BenchmarkSuite, BenchmarkVersion, Task
from app.config import settings
from app.logger import setup_logger
import uuid
from datetime import datetime

logger = setup_logger(__name__)


# Sample Java benchmark tasks
SAMPLE_JAVA_TASKS = [
    {
        "task_id": "java-001",
        "problem_statement": "Write a function that returns the sum of two integers.",
        "category": "basics",
        "difficulty": 1,
        "public_tests": [
            {"name": "test_positive", "input": "(2, 3)", "expected": "5"},
            {"name": "test_zero", "input": "(0, 0)", "expected": "0"},
            {"name": "test_negative", "input": "(-1, 1)", "expected": "0"}
        ]
    },
    {
        "task_id": "java-002",
        "problem_statement": "Write a function to check if a string is a palindrome.",
        "category": "strings",
        "difficulty": 1,
        "public_tests": [
            {"name": "test_palindrome", "input": '"racecar"', "expected": "true"},
            {"name": "test_not_palindrome", "input": '"hello"', "expected": "false"},
            {"name": "test_single_char", "input": '"a"', "expected": "true"}
        ]
    },
    {
        "task_id": "java-003",
        "problem_statement": "Implement binary search in a sorted array.",
        "category": "algorithms",
        "difficulty": 2,
        "public_tests": [
            {"name": "test_found", "input": "([1,3,5,7,9], 5)", "expected": "2"},
            {"name": "test_not_found", "input": "([1,3,5,7,9], 4)", "expected": "-1"},
            {"name": "test_first", "input": "([1,3,5,7,9], 1)", "expected": "0"}
        ]
    },
    {
        "task_id": "java-004",
        "problem_statement": "Find two numbers that sum to a target in an array.",
        "category": "arrays",
        "difficulty": 2,
        "public_tests": [
            {"name": "test_found", "input": "([2,7,11,15], 9)", "expected": "[0,1]"},
            {"name": "test_different_order", "input": "([3,2,4], 6)", "expected": "[1,2]"},
            {"name": "test_duplicates", "input": "([3,3], 6)", "expected": "[0,1]"}
        ]
    },
    {
        "task_id": "java-005",
        "problem_statement": "Implement factorial using recursion.",
        "category": "recursion",
        "difficulty": 1,
        "public_tests": [
            {"name": "test_base", "input": "0", "expected": "1"},
            {"name": "test_small", "input": "5", "expected": "120"},
            {"name": "test_larger", "input": "10", "expected": "3628800"}
        ]
    },
    {
        "task_id": "java-006",
        "problem_statement": "Implement Fibonacci sequence.",
        "category": "recursion",
        "difficulty": 1,
        "public_tests": [
            {"name": "test_0", "input": "0", "expected": "0"},
            {"name": "test_1", "input": "1", "expected": "1"},
            {"name": "test_5", "input": "5", "expected": "5"}
        ]
    },
    {
        "task_id": "java-007",
        "problem_statement": "Sort an array using quicksort.",
        "category": "sorting",
        "difficulty": 2,
        "public_tests": [
            {"name": "test_unsorted", "input": "[3,1,4,1,5]", "expected": "[1,1,3,4,5]"},
            {"name": "test_already_sorted", "input": "[1,2,3]", "expected": "[1,2,3]"},
            {"name": "test_reverse", "input": "[5,4,3,2,1]", "expected": "[1,2,3,4,5]"}
        ]
    },
    {
        "task_id": "java-008",
        "problem_statement": "Find the longest common subsequence of two strings.",
        "category": "dynamic_programming",
        "difficulty": 3,
        "public_tests": [
            {"name": "test_common", "input": '("abcde", "ace")', "expected": "\"ace\""},
            {"name": "test_no_common", "input": '("abc", "def")', "expected": "\"\""},
            {"name": "test_same", "input": '("test", "test")', "expected": "\"test\""}
        ]
    },
    {
        "task_id": "java-009",
        "problem_statement": "Reverse a linked list.",
        "category": "data_structures",
        "difficulty": 2,
        "public_tests": [
            {"name": "test_normal", "input": "[1,2,3]", "expected": "[3,2,1]"},
            {"name": "test_single", "input": "[1]", "expected": "[1]"},
            {"name": "test_empty", "input": "[]", "expected": "[]"}
        ]
    },
    {
        "task_id": "java-010",
        "problem_statement": "Implement a stack using an array.",
        "category": "data_structures",
        "difficulty": 1,
        "public_tests": [
            {"name": "test_push_pop", "input": "push(1); push(2); pop();", "expected": "2"},
            {"name": "test_peek", "input": "push(1); peek();", "expected": "1"},
            {"name": "test_empty", "input": "isEmpty()", "expected": "true"}
        ]
    },
]


def create_sample_benchmark(session, benchmark_name: str = "Java Programming POC"):
    """Create a sample Java benchmark with tasks."""
    try:
        logger.info(f"Creating sample benchmark: {benchmark_name}")
        
        # Create benchmark suite
        suite = BenchmarkSuite(
            id=uuid.uuid4(),
            name=benchmark_name,
            description="Java programming tasks for POC evaluation"
        )
        session.add(suite)
        session.flush()
        
        # Create version
        version = BenchmarkVersion(
            id=uuid.uuid4(),
            suite_id=suite.id,
            version_number="v1.0",
            status="draft"
        )
        session.add(version)
        session.flush()
        
        # Add sample tasks
        for task_data in SAMPLE_JAVA_TASKS:
            task = Task(
                id=uuid.uuid4(),
                benchmark_version_id=version.id,
                task_id=task_data["task_id"],
                problem_statement=task_data["problem_statement"],
                category=task_data["category"],
                difficulty=task_data["difficulty"],
                public_tests=task_data["public_tests"]
            )
            session.add(task)
        
        session.commit()
        
        logger.info(f"✅ Benchmark created: {suite.id}")
        logger.info(f"   Name: {suite.name}")
        logger.info(f"   Version: {version.version_number}")
        logger.info(f"   Tasks: {len(SAMPLE_JAVA_TASKS)}")
        
        return suite.id
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error creating benchmark: {str(e)}")
        raise


def import_from_json(session, json_file: str, benchmark_name: str):
    """Import benchmark tasks from JSON file."""
    try:
        logger.info(f"Importing from JSON file: {json_file}")
        
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Create benchmark suite
        suite = BenchmarkSuite(
            id=uuid.uuid4(),
            name=benchmark_name,
            description=data.get("description", "Imported benchmark")
        )
        session.add(suite)
        session.flush()
        
        # Create version
        version = BenchmarkVersion(
            id=uuid.uuid4(),
            suite_id=suite.id,
            version_number=data.get("version", "v1.0"),
            status="draft"
        )
        session.add(version)
        session.flush()
        
        # Add tasks
        tasks = data.get("tasks", [])
        for task_data in tasks:
            task = Task(
                id=uuid.uuid4(),
                benchmark_version_id=version.id,
                task_id=task_data["task_id"],
                problem_statement=task_data["problem_statement"],
                category=task_data.get("category"),
                difficulty=task_data.get("difficulty"),
                public_tests=task_data.get("public_tests", [])
            )
            session.add(task)
        
        session.commit()
        
        logger.info(f"✅ Benchmark imported: {suite.id}")
        logger.info(f"   Name: {suite.name}")
        logger.info(f"   Tasks: {len(tasks)}")
        
        return suite.id
        
    except FileNotFoundError:
        logger.error(f"❌ File not found: {json_file}")
        raise
    except json.JSONDecodeError:
        logger.error(f"❌ Invalid JSON in file: {json_file}")
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error importing benchmark: {str(e)}")
        raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Import benchmark tasks for C/AI Arena POC"
    )
    parser.add_argument(
        "--source",
        type=str,
        help="Path to JSON file with benchmark tasks"
    )
    parser.add_argument(
        "--samples",
        type=int,
        help="Create N sample Java tasks (10 for demo, 30 for full POC)"
    )
    parser.add_argument(
        "--name",
        type=str,
        default="Java Programming POC",
        help="Benchmark name"
    )
    
    args = parser.parse_args()
    
    # Connect to database
    engine = create_engine(settings.DATABASE_URL, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        if args.source:
            # Import from JSON
            benchmark_id = import_from_json(session, args.source, args.name)
        elif args.samples:
            # Create sample tasks (use first N samples)
            logger.info(f"Creating {args.samples} sample Java tasks...")
            tasks = SAMPLE_JAVA_TASKS[:args.samples]
            
            suite = BenchmarkSuite(
                id=uuid.uuid4(),
                name=args.name,
                description="Sample Java programming tasks"
            )
            session.add(suite)
            session.flush()
            
            version = BenchmarkVersion(
                id=uuid.uuid4(),
                suite_id=suite.id,
                version_number="v1.0",
                status="draft"
            )
            session.add(version)
            session.flush()
            
            for task_data in tasks:
                task = Task(
                    id=uuid.uuid4(),
                    benchmark_version_id=version.id,
                    task_id=task_data["task_id"],
                    problem_statement=task_data["problem_statement"],
                    category=task_data["category"],
                    difficulty=task_data["difficulty"],
                    public_tests=task_data["public_tests"]
                )
                session.add(task)
            
            session.commit()
            benchmark_id = suite.id
            
            logger.info(f"✅ Sample benchmark created: {suite.id}")
            logger.info(f"   Tasks: {len(tasks)}")
        else:
            # Default: create standard sample benchmark
            benchmark_id = create_sample_benchmark(session, args.name)
        
        logger.info(f"\n✅ Import complete!")
        logger.info(f"Benchmark ID: {benchmark_id}")
        logger.info(f"\nNext steps:")
        logger.info(f"1. Register candidate models: POST /api/v1/candidates")
        logger.info(f"2. Create experiment: POST /api/v1/experiments")
        logger.info(f"3. Run tasks: Worker pool executes benchmark")
        
    except Exception as e:
        logger.error(f"\n❌ Import failed: {str(e)}")
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()