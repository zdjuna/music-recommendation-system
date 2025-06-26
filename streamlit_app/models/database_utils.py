"""
Database utilities and error handling
"""

import sqlite3
import logging
from typing import Any, Dict, Optional
from functools import wraps

logger = logging.getLogger(__name__)

def database_retry(max_retries: int = 3):
    """Decorator for database operations with retry logic"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    last_error = e
                    if "database is locked" in str(e).lower():
                        if attempt < max_retries - 1:
                            logger.warning(f"Database locked, retrying... (attempt {attempt + 1}/{max_retries})")
                            import time
                            time.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                            continue
                    raise e
                except Exception as e:
                    logger.error(f"Database operation failed: {e}")
                    raise e
            
            raise last_error
        return wrapper
    return decorator

def validate_database_connection(db_path: str) -> bool:
    """Validate database connection and basic operations"""
    try:
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()
        
        # Test basic operation
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
        cursor.fetchone()
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Database validation failed: {e}")
        return False

def get_database_info(db_path: str) -> Dict[str, Any]:
    """Get comprehensive database information"""
    try:
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()
        
        # Get table list
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Get database size
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        size_result = cursor.fetchone()
        db_size = size_result[0] if size_result else 0
        
        # Get row counts for each table
        table_counts = {}
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                table_counts[table] = count
            except:
                table_counts[table] = 0
        
        conn.close()
        
        return {
            'tables': tables,
            'table_counts': table_counts,
            'size_bytes': db_size,
            'size_mb': round(db_size / (1024 * 1024), 2)
        }
        
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {
            'tables': [],
            'table_counts': {},
            'size_bytes': 0,
            'size_mb': 0,
            'error': str(e)
        }

def repair_database(db_path: str) -> bool:
    """Attempt to repair database issues"""
    try:
        conn = sqlite3.connect(db_path, timeout=30.0)
        
        # Run integrity check
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        integrity_result = cursor.fetchone()
        
        if integrity_result[0] != "ok":
            logger.warning(f"Database integrity issues found: {integrity_result[0]}")
            
            # Attempt vacuum to repair
            cursor.execute("VACUUM")
            logger.info("Database vacuum completed")
        
        # Optimize database
        cursor.execute("PRAGMA optimize")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Database repair failed: {e}")
        return False