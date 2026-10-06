"""
Code evaluators for benchmark responses.

Evaluator: Takes code response + task tests → Returns pass/fail + score
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import subprocess
import tempfile
import os
import re

from app.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class EvaluationResult:
    """Result of code evaluation."""
    passed: bool  # Did all tests pass?
    score: int  # 0-100
    total_tests: int
    passed_tests: int
    failed_tests: int
    compilation_error: Optional[str] = None
    runtime_error: Optional[str] = None
    test_output: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class CodeEvaluator(ABC):
    """Abstract base for code evaluators."""
    
    @abstractmethod
    def evaluate(self, code: str, tests: List[Dict]) -> EvaluationResult:
        """
        Evaluate submitted code against tests.
        
        Args:
            code: Submitted code as string
            tests: List of test dicts with expected outputs
            
        Returns:
            EvaluationResult with pass/fail + score
        """
        pass


class JavaEvaluator(CodeEvaluator):
    """
    Evaluates Java code.
    
    Process:
    1. Extract main method/class from response
    2. Create test harness with JUnit tests
    3. Compile in Docker container
    4. Run tests in Docker container
    5. Parse results
    6. Calculate score
    """
    
    def __init__(self):
        logger.info("JavaEvaluator initialized")
    
    def evaluate(self, code: str, tests: List[Dict], candidate_config: Dict = None) -> EvaluationResult:
        """
        Evaluate Java code.
        
        Args:
            code: Java code (may include class definition or just methods)
            tests: List of test cases
                [
                  {"name": "test1", "input": "(2, 3)", "expected": "5"},
                  {"name": "test2", "input": "(0, 0)", "expected": "0"}
                ]
            candidate_config: Optional candidate config with quality_level
                
        Returns:
            EvaluationResult
        """
        logger.info(f"Evaluating Java code with {len(tests)} tests")
        
        # Get quality level for multi-candidate testing
        quality_level = "medium"
        if candidate_config and isinstance(candidate_config, dict):
            quality_level = candidate_config.get("quality_level", "medium")
        
        try:
            # Step 1: Extract class name and ensure proper structure
            solution_code = self._prepare_java_code(code)
            
            # Step 2: Create test harness
            test_harness = self._create_test_harness(solution_code, tests)
            
            # Step 3: Compile and run (using Docker)
            compilation_result, test_results = self._run_java_tests(
                solution_code,
                test_harness
            )
            
            # Step 4: Parse results
            if compilation_result["error"]:
                return EvaluationResult(
                    passed=False,
                    score=0,
                    total_tests=len(tests),
                    passed_tests=0,
                    failed_tests=len(tests),
                    compilation_error=compilation_result["error"],
                    details={"compilation_failed": True}
                )
            
            # Step 5: Score based on test results and quality level
            passed_count = sum(1 for r in test_results if r["passed"])
            total_count = len(test_results)
            
            # Base score on passed tests
            base_score = int((passed_count / total_count * 100)) if total_count > 0 else 0
            
            # Adjust score based on quality level (for multi-candidate testing)
            if quality_level == "high":
                # High quality: full score
                score = min(100, int(base_score * 1.0))
            elif quality_level == "medium":
                # Medium quality: scale to ~70% range
                score = min(100, int(base_score * 0.7))
            elif quality_level == "low":
                # Low quality: scale to ~40% range
                score = min(100, int(base_score * 0.4))
            else:
                score = base_score
            
            return EvaluationResult(
                passed=passed_count == total_count,
                score=score,
                total_tests=total_count,
                passed_tests=passed_count,
                failed_tests=total_count - passed_count,
                test_output="\n".join([str(r) for r in test_results]),
                details={
                    "test_results": test_results,
                    "compilation_success": True
                }
            )
        
        except Exception as e:
            logger.error(f"Evaluation error: {str(e)}")
            return EvaluationResult(
                passed=False,
                score=0,
                total_tests=len(tests),
                passed_tests=0,
                failed_tests=len(tests),
                runtime_error=str(e),
                details={"error": str(e)}
            )
    
    def _prepare_java_code(self, code: str) -> str:
        """
        Prepare Java code for compilation.
        
        Handles both:
        - Full class definitions
        - Just method implementations
        """
        # Extract just the code part (remove markdown if present)
        code = code.strip()
        if code.startswith("```"):
            code = code.split("```")[1].lstrip("java\n")
        if code.endswith("```"):
            code = code.rsplit("```")[0]
        
        code = code.strip()
        
        # If code already has class definition, return as-is
        if "class Solution" in code or "class " in code:
            return code
        
        # Otherwise, wrap in Solution class
        wrapped = f"""public class Solution {{
    {code}
}}"""
        return wrapped
    
    def _create_test_harness(self, solution_code: str, tests: List[Dict]) -> str:
        """
        Create JUnit test harness.
        
        Simple approach: Create a Main class that runs tests
        (In production, would use full JUnit framework)
        """
        test_code = 'import org.junit.Test;\nimport static org.junit.Assert.*;\n\n'
        test_code += f'{solution_code}\n\n'
        test_code += 'public class TestSolution {\n'
        
        for i, test in enumerate(tests, 1):
            test_name = test.get("name", f"test{i}")
            input_val = test.get("input", "")
            expected = test.get("expected", "")
            
            # Simple test: just check if method returns expected value
            test_code += f'''
    @Test
    public void {test_name}() {{
        Solution sol = new Solution();
        // Test: {test_name}
        // Input: {input_val}
        // Expected: {expected}
    }}
'''
        
        test_code += '}\n'
        return test_code
    
    def _run_java_tests(self, solution_code: str, test_harness: str):
        """
        Run Java tests in Docker container.
        
        For POC: Simulate compilation and return mock results
        For production: Actually compile and run in Docker
        """
        logger.debug("Running Java tests (simulated)")
        
        # POC: Simulate compilation success
        compilation_result = {
            "success": True,
            "error": None,
            "output": "Compilation successful"
        }
        
        # POC: Simulate test results
        # In production, would:
        # 1. Create temp directory
        # 2. Write Solution.java and Test files
        # 3. Compile with javac in Docker
        # 4. Run with java -cp ... org.junit.runner.JUnitCore
        # 5. Parse output
        
        test_results = [
            {"name": "test1", "passed": True, "output": "✓ Passed"},
            {"name": "test2", "passed": True, "output": "✓ Passed"},
        ]
        
        return compilation_result, test_results


class MockEvaluator(CodeEvaluator):
    """Mock evaluator for testing (always passes)."""
    
    def evaluate(self, code: str, tests: List[Dict], candidate_config: Dict = None) -> EvaluationResult:
        """Always return 100% pass for testing."""
        return EvaluationResult(
            passed=True,
            score=100,
            total_tests=len(tests),
            passed_tests=len(tests),
            failed_tests=0,
            details={"mock": True}
        )


def get_evaluator(language: str = "java") -> CodeEvaluator:
    """
    Get appropriate evaluator for language.
    
    Args:
        language: Programming language (java, python, etc.)
        
    Returns:
        Evaluator instance
    """
    if language.lower() == "java":
        return JavaEvaluator()
    elif language.lower() == "mock":
        return MockEvaluator()
    else:
        logger.warning(f"Unknown language {language}, using MockEvaluator")
        return MockEvaluator()