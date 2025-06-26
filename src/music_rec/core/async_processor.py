"""
Async processing engine for music recommendation system
"""

import asyncio
import aiohttp
import time
from typing import List, Dict, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Task:
    id: str
    func: Callable
    args: tuple
    kwargs: dict
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[Exception] = None
    created_at: float = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()

class AsyncProcessor:
    """High-performance async processor for music data operations"""
    
    def __init__(self, max_concurrent: int = 10, timeout: float = 30.0):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self.thread_pool = ThreadPoolExecutor(max_workers=max_concurrent)
        self.tasks: Dict[str, Task] = {}
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        self.thread_pool.shutdown(wait=True)
    
    async def process_tracks_parallel(self, tracks: List[Dict[str, str]], 
                                    processor_func: Callable, 
                                    progress_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """Process multiple tracks in parallel with progress tracking"""
        
        async def process_single_track(track: Dict[str, str]) -> Dict[str, Any]:
            async with self.semaphore:
                try:
                    # Run CPU-bound tasks in thread pool
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        self.thread_pool, 
                        processor_func, 
                        track
                    )
                    
                    if progress_callback:
                        await asyncio.create_task(
                            self._safe_progress_callback(progress_callback, track, result)
                        )
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"Error processing track {track.get('artist', 'Unknown')} - {track.get('track', 'Unknown')}: {e}")
                    return {
                        'artist': track.get('artist', 'Unknown'),
                        'track': track.get('track', 'Unknown'),
                        'error': str(e),
                        'status': 'failed'
                    }
        
        # Create tasks for all tracks
        tasks = [process_single_track(track) for track in tracks]
        
        # Process with progress tracking
        results = []
        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)
        
        return results
    
    async def batch_api_requests(self, requests: List[Dict[str, Any]], 
                                request_func: Callable) -> List[Dict[str, Any]]:
        """Execute multiple API requests in parallel batches"""
        
        async def make_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
            async with self.semaphore:
                try:
                    if asyncio.iscoroutinefunction(request_func):
                        return await request_func(self.session, request_data)
                    else:
                        loop = asyncio.get_event_loop()
                        return await loop.run_in_executor(
                            self.thread_pool,
                            request_func,
                            request_data
                        )
                except Exception as e:
                    logger.error(f"API request failed: {e}")
                    return {
                        'error': str(e),
                        'status': 'failed',
                        'request_data': request_data
                    }
        
        # Create and execute all requests
        tasks = [make_request(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions in results
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({
                    'error': str(result),
                    'status': 'failed'
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def process_with_rate_limiting(self, items: List[Any], 
                                       processor_func: Callable,
                                       rate_limit: float = 1.0) -> List[Any]:
        """Process items with rate limiting (items per second)"""
        results = []
        last_request_time = 0
        
        for item in items:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - last_request_time
            if time_since_last < rate_limit:
                await asyncio.sleep(rate_limit - time_since_last)
            
            async with self.semaphore:
                try:
                    if asyncio.iscoroutinefunction(processor_func):
                        result = await processor_func(item)
                    else:
                        loop = asyncio.get_event_loop()
                        result = await loop.run_in_executor(
                            self.thread_pool,
                            processor_func,
                            item
                        )
                    results.append(result)
                    last_request_time = time.time()
                    
                except Exception as e:
                    logger.error(f"Error processing item {item}: {e}")
                    results.append({
                        'item': item,
                        'error': str(e),
                        'status': 'failed'
                    })
        
        return results
    
    async def _safe_progress_callback(self, callback: Callable, track: Dict, result: Dict):
        """Safely execute progress callback"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(track, result)
            else:
                callback(track, result)
        except Exception as e:
            logger.warning(f"Progress callback failed: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        completed_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]
        failed_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.FAILED]
        
        if completed_tasks:
            processing_times = [
                t.completed_at - t.started_at 
                for t in completed_tasks 
                if t.started_at and t.completed_at
            ]
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            
            return {
                'total_tasks': len(self.tasks),
                'completed_tasks': len(completed_tasks),
                'failed_tasks': len(failed_tasks),
                'success_rate': len(completed_tasks) / len(self.tasks) if self.tasks else 0,
                'avg_processing_time': avg_processing_time,
                'max_concurrent': self.max_concurrent
            }
        
        return {
            'total_tasks': len(self.tasks),
            'completed_tasks': 0,
            'failed_tasks': len(failed_tasks),
            'success_rate': 0,
            'avg_processing_time': 0,
            'max_concurrent': self.max_concurrent
        }

# Utility functions for common use cases
async def process_music_data_async(tracks: List[Dict[str, str]], 
                                 enrichment_func: Callable,
                                 max_concurrent: int = 10,
                                 progress_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
    """High-level async function for processing music data"""
    
    async with AsyncProcessor(max_concurrent=max_concurrent) as processor:
        results = await processor.process_tracks_parallel(
            tracks=tracks,
            processor_func=enrichment_func,
            progress_callback=progress_callback
        )
    
    return results

async def batch_spotify_requests(track_ids: List[str], 
                                spotify_func: Callable,
                                max_concurrent: int = 5) -> List[Dict[str, Any]]:
    """Batch Spotify API requests with proper rate limiting"""
    
    requests = [{'track_id': track_id} for track_id in track_ids]
    
    async with AsyncProcessor(max_concurrent=max_concurrent) as processor:
        results = await processor.batch_api_requests(
            requests=requests,
            request_func=spotify_func
        )
    
    return results