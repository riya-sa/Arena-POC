"""Integration tests for distributed execution."""

import pytest
import asyncio
from app.domain.jobs.service import Job, Task, JobStatus, JobService
from app.infrastructure.queue import RedisJobQueue, get_queue


@pytest.fixture
def job_queue():
    """Create test job queue."""
    queue = get_queue()
    yield queue
    queue.clear_queue()


@pytest.fixture
def sample_job():
    """Create sample job."""
    tasks = [
        Task(
            id="t1",
            benchmark_id="b1",
            task_name="Task 1",
            input_data="hello",
            expected_output="hello"
        ),
        Task(
            id="t2",
            benchmark_id="b1",
            task_name="Task 2",
            input_data="world",
            expected_output="world"
        )
    ]
    
    return Job(
        experiment_id="exp-001",
        candidate_id="cand-001",
        candidate_name="Test Candidate",
        status=JobStatus.QUEUED,
        tasks=tasks,
        total_tasks=len(tasks)
    )


def test_job_queue_enqueue(job_queue, sample_job):
    """Test enqueueing a job."""
    assert job_queue.enqueue_job(sample_job)
    assert job_queue.get_queue_length() == 1


def test_job_queue_dequeue(job_queue, sample_job):
    """Test dequeueing a job."""
    job_queue.enqueue_job(sample_job)
    dequeued = job_queue.dequeue_job()
    
    assert dequeued is not None
    assert dequeued.id == sample_job.id
    assert dequeued.status == JobStatus.QUEUED


def test_job_serialization(sample_job):
    """Test job serialization."""
    json_str = sample_job.to_json()
    deserialized = Job.from_json(json_str)
    
    assert deserialized.id == sample_job.id
    assert deserialized.total_tasks == sample_job.total_tasks
    assert len(deserialized.tasks) == len(sample_job.tasks)


def test_job_progress(sample_job):
    """Test job progress calculation."""
    assert sample_job.progress_percent() == 0
    
    sample_job.completed_tasks = 1
    assert sample_job.progress_percent() == 50
    
    sample_job.completed_tasks = 2
    assert sample_job.progress_percent() == 100


@pytest.mark.asyncio
async def test_job_service_submit():
    """Test job submission via service."""
    tasks = [
        Task(
            id="t1",
            benchmark_id="b1",
            task_name="Task",
            input_data="test",
            expected_output="test"
        )
    ]
    
    job = JobService.submit_job(
        experiment_id="exp-001",
        candidate_id="cand-001",
        candidate_name="Test",
        tasks=tasks
    )
    
    assert job.id is not None
    assert job.status == JobStatus.QUEUED
    assert job.total_tasks == 1


@pytest.mark.asyncio
async def test_job_service_get():
    """Test job retrieval via service."""
    tasks = [Task(
        id="t1",
        benchmark_id="b1",
        task_name="Task",
        input_data="test",
        expected_output="test"
    )]
    
    job = JobService.submit_job(
        experiment_id="exp-001",
        candidate_id="cand-001",
        candidate_name="Test",
        tasks=tasks
    )
    
    retrieved = JobService.get_job(job.id)
    assert retrieved is not None
    assert retrieved.id == job.id


def test_retry_policy():
    """Test retry policy calculation."""
    from app.workers.retry_manager import RetryPolicy
    
    policy = RetryPolicy(
        max_retries=3,
        initial_delay_seconds=1,
        max_delay_seconds=60,
        backoff_multiplier=2.0
    )
    
    assert policy.get_delay(0) == 1
    assert policy.get_delay(1) == 2
    assert policy.get_delay(2) == 4
    assert policy.get_delay(10) == 60


def test_error_categorization():
    """Test error categorization."""
    from app.domain.jobs.error_handler import ErrorHandler, ErrorType
    
    timeout_error = TimeoutError("Operation timed out")
    assert ErrorHandler.categorize_error(timeout_error) == ErrorType.TIMEOUT
    
    adapter_error = Exception("Adapter connection failed")
    assert ErrorHandler.categorize_error(adapter_error) == ErrorType.ADAPTER_ERROR
    
    unknown_error = Exception("Something went wrong")
    assert ErrorHandler.categorize_error(unknown_error) == ErrorType.UNKNOWN


def test_metrics_collector():
    """Test metrics collection."""
    from app.infrastructure.metrics import MetricsCollector
    
    metrics = MetricsCollector()
    
    metrics.record_job_submitted()
    metrics.record_job_submitted()
    metrics.record_job_completed(1000)
    metrics.record_job_failed()
    metrics.record_task_completed()
    metrics.record_task_completed()
    metrics.record_task_failed("Test error")
    
    stats = metrics.get_metrics()
    
    assert stats["jobs"]["submitted"] == 2
    assert stats["jobs"]["completed"] == 1
    assert stats["jobs"]["failed"] == 1
    assert stats["tasks"]["completed"] == 2
    assert stats["tasks"]["failed"] == 1