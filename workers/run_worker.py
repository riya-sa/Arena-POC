# """Standalone worker process - run separately from API."""

# import asyncio
# import sys
# import os
# from pathlib import Path

# # Add parent directory to path
# sys.path.insert(0, str(Path(__file__).parent.parent))

# from app.workers.task_processor import TaskProcessor
# from app.logger import logger
# from app.config import Settings


# async def main():
#     """Run worker process."""
#     settings = Settings()
    
#     logger.info("Worker starting")
#     logger.info(f"Environment: {settings.environment}")
#     logger.info(f"Database: {settings.database_url}")
    
#     # Create worker
#     worker = TaskProcessor(worker_id="worker-standalone", concurrency=4)
    
#     try:
#         # Run until interrupted
#         await worker.run()
#     except KeyboardInterrupt:
#         logger.info("Worker interrupted")
#     finally:
#         worker.stop()
#         logger.info(f"Worker stats: {worker.stats()}")


# if __name__ == "__main__":
#     asyncio.run(main())

"""Standalone worker process - run separately from API."""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.workers import TaskProcessor
from app.logger import logger
from app.config import Settings
from app.infrastructure.queue import init_queue


async def main():
    """Run worker process."""
    settings = Settings()
    
    logger.info("Worker starting")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database: {settings.database_url}")
    
    # Initialize queue
    try:
        init_queue(host="localhost", port=6379)
        logger.info("✅ Queue initialized")
    except Exception as e:
        logger.error(f"Failed to initialize queue: {str(e)}")
        return
    
    # Create worker
    worker = TaskProcessor(worker_id="worker-standalone", concurrency=4)
    
    try:
        # Run until interrupted
        await worker.run()
    except KeyboardInterrupt:
        logger.info("Worker interrupted")
    finally:
        worker.stop()
        logger.info(f"Worker stats: {worker.stats()}")


if __name__ == "__main__":
    asyncio.run(main())