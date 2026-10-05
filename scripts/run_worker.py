# """
# Run a benchmark task worker.

# The worker pulls jobs from the queue and executes them.

# Usage:
#     # Run a single worker
#     python scripts/run_worker.py
    
#     # Run with custom worker ID
#     python scripts/run_worker.py --worker-id worker-1
    
#     # Run and stop after 10 jobs (for testing)
#     python scripts/run_worker.py --max-jobs 10
    
#     # Run multiple workers in parallel
#     python scripts/run_worker.py --worker-id worker-1 &
#     python scripts/run_worker.py --worker-id worker-2 &
#     python scripts/run_worker.py --worker-id worker-3 &
# """

# import sys
# import argparse
# from pathlib import Path

# # Add parent directory to path
# sys.path.insert(0, str(Path(__file__).parent.parent))

# from app.worker import run_worker
# from app.logger import setup_logger

# logger = setup_logger(__name__)


# def main():
#     """Main entry point."""
#     parser = argparse.ArgumentParser(
#         description="Run a benchmark task worker"
#     )
#     parser.add_argument(
#         "--worker-id",
#         type=str,
#         default="worker-1",
#         help="Unique worker identifier"
#     )
#     parser.add_argument(
#         "--max-jobs",
#         type=int,
#         default=None,
#         help="Stop after processing N jobs (for testing)"
#     )
#     parser.add_argument(
#         "--poll-interval",
#         type=float,
#         default=1.0,
#         help="Seconds to wait between queue polls"
#     )
    
#     args = parser.parse_args()
    
#     logger.info("="*60)
#     logger.info("C/AI Arena POC - Worker")
#     logger.info("="*60)
#     logger.info(f"Worker ID: {args.worker_id}")
#     logger.info(f"Poll interval: {args.poll_interval}s")
#     if args.max_jobs:
#         logger.info(f"Max jobs: {args.max_jobs}")
#     logger.info("")
    
#     try:
#         run_worker(
#             worker_id=args.worker_id,
#             max_jobs=args.max_jobs
#         )
#     except KeyboardInterrupt:
#         logger.info("Worker stopped by user")
#     except Exception as e:
#         logger.error(f"Worker error: {str(e)}")
#         sys.exit(1)


# if __name__ == "__main__":
#     main()

"""
Run a benchmark task worker.

The worker pulls jobs from the queue and executes them.

Usage:
    # Run a single worker
    python scripts/run_worker.py
    
    # Run with custom worker ID
    python scripts/run_worker.py --worker-id worker-1
    
    # Run and stop after 10 jobs (for testing)
    python scripts/run_worker.py --max-jobs 10
    
    # Run multiple workers in parallel
    python scripts/run_worker.py --worker-id worker-1 &
    python scripts/run_worker.py --worker-id worker-2 &
    python scripts/run_worker.py --worker-id worker-3 &
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.worker_v2 import run_worker
from app.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run a benchmark task worker"
    )
    parser.add_argument(
        "--worker-id",
        type=str,
        default="worker-1",
        help="Unique worker identifier"
    )
    parser.add_argument(
        "--max-jobs",
        type=int,
        default=None,
        help="Stop after processing N jobs (for testing)"
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=1.0,
        help="Seconds to wait between queue polls"
    )
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("C/AI Arena POC - Worker")
    logger.info("="*60)
    logger.info(f"Worker ID: {args.worker_id}")
    logger.info(f"Poll interval: {args.poll_interval}s")
    if args.max_jobs:
        logger.info(f"Max jobs: {args.max_jobs}")
    logger.info("")
    
    try:
        run_worker(
            worker_id=args.worker_id,
            max_jobs=args.max_jobs
        )
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()