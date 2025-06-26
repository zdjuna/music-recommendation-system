"""
API health monitoring and circuit breaker implementation
"""

import time
import asyncio
import aiohttp
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import deque
import json

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service has recovered

@dataclass
class HealthCheck:
    timestamp: float
    success: bool
    response_time: float
    error: Optional[str] = None

@dataclass
class ServiceHealth:
    name: str
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_check: Optional[float] = None
    response_time: float = 0.0
    success_rate: float = 0.0
    error_count: int = 0
    checks: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def add_check(self, check: HealthCheck):
        """Add a health check result"""
        self.checks.append(check)
        self.last_check = check.timestamp
        
        # Calculate success rate from recent checks
        recent_checks = list(self.checks)[-20:]  # Last 20 checks
        if recent_checks:
            successes = sum(1 for c in recent_checks if c.success)
            self.success_rate = successes / len(recent_checks)
            
            # Calculate average response time
            successful_checks = [c for c in recent_checks if c.success]
            if successful_checks:
                self.response_time = sum(c.response_time for c in successful_checks) / len(successful_checks)
        
        # Update status based on success rate
        if self.success_rate >= 0.9:
            self.status = ServiceStatus.HEALTHY
        elif self.success_rate >= 0.5:
            self.status = ServiceStatus.DEGRADED
        else:
            self.status = ServiceStatus.UNHEALTHY

class CircuitBreaker:
    """Circuit breaker implementation for API calls"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN - service unavailable")
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        return (self.last_failure_time and 
                time.time() - self.last_failure_time >= self.recovery_timeout)
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

class HealthMonitor:
    """Comprehensive health monitoring system"""
    
    def __init__(self):
        self.services: Dict[str, ServiceHealth] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.monitoring_active = False
        self.check_interval = 60.0  # Check every minute
    
    def register_service(self, name: str, health_check_func: Callable, 
                        circuit_breaker_config: Optional[Dict] = None):
        """Register a service for monitoring"""
        self.services[name] = ServiceHealth(name=name)
        
        # Set up circuit breaker
        if circuit_breaker_config:
            self.circuit_breakers[name] = CircuitBreaker(**circuit_breaker_config)
        else:
            self.circuit_breakers[name] = CircuitBreaker()
        
        # Store the health check function
        setattr(self, f"_check_{name}", health_check_func)
    
    async def check_service_health(self, service_name: str) -> HealthCheck:
        """Perform health check for a specific service"""
        start_time = time.time()
        
        try:
            check_func = getattr(self, f"_check_{service_name}")
            
            if asyncio.iscoroutinefunction(check_func):
                await check_func()
            else:
                check_func()
            
            response_time = time.time() - start_time
            return HealthCheck(
                timestamp=time.time(),
                success=True,
                response_time=response_time
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheck(
                timestamp=time.time(),
                success=False,
                response_time=response_time,
                error=str(e)
            )
    
    async def check_all_services(self) -> Dict[str, HealthCheck]:
        """Check health of all registered services"""
        results = {}
        
        for service_name in self.services.keys():
            try:
                health_check = await self.check_service_health(service_name)
                self.services[service_name].add_check(health_check)
                results[service_name] = health_check
                
            except Exception as e:
                logger.error(f"Health check failed for {service_name}: {e}")
                error_check = HealthCheck(
                    timestamp=time.time(),
                    success=False,
                    response_time=0.0,
                    error=str(e)
                )
                self.services[service_name].add_check(error_check)
                results[service_name] = error_check
        
        return results
    
    async def start_monitoring(self):
        """Start continuous health monitoring"""
        self.monitoring_active = True
        
        while self.monitoring_active:
            try:
                await self.check_all_services()
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health report"""
        return {
            'timestamp': time.time(),
            'overall_status': self._calculate_overall_status(),
            'services': {
                name: {
                    'status': health.status.value,
                    'success_rate': health.success_rate,
                    'response_time': health.response_time,
                    'last_check': health.last_check,
                    'circuit_breaker_state': self.circuit_breakers[name].state.value
                }
                for name, health in self.services.items()
            }
        }
    
    def _calculate_overall_status(self) -> str:
        """Calculate overall system health status"""
        if not self.services:
            return ServiceStatus.UNKNOWN.value
        
        statuses = [health.status for health in self.services.values()]
        
        if all(status == ServiceStatus.HEALTHY for status in statuses):
            return ServiceStatus.HEALTHY.value
        elif any(status == ServiceStatus.UNHEALTHY for status in statuses):
            return ServiceStatus.DEGRADED.value
        else:
            return ServiceStatus.DEGRADED.value
    
    async def call_with_circuit_breaker(self, service_name: str, func: Callable, *args, **kwargs) -> Any:
        """Make a service call protected by circuit breaker"""
        if service_name not in self.circuit_breakers:
            raise ValueError(f"Service {service_name} not registered")
        
        circuit_breaker = self.circuit_breakers[service_name]
        return await circuit_breaker.call(func, *args, **kwargs)

# Pre-configured health checks for common services
async def check_lastfm_health():
    """Health check for Last.fm API"""
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "http://ws.audioscrobbler.com/2.0/?method=chart.gettopartists&api_key=test&format=json",
            timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            if response.status == 200:
                return True
            else:
                raise Exception(f"Last.fm API returned status {response.status}")

async def check_spotify_health():
    """Health check for Spotify API"""
    # This would require a valid token, so we'll just check if the endpoint is reachable
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.spotify.com/v1/",
            timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            # Spotify returns 401 for unauthenticated requests, which is expected
            if response.status in [200, 401]:
                return True
            else:
                raise Exception(f"Spotify API returned status {response.status}")

def check_database_health():
    """Health check for database"""
    try:
        from streamlit_app.models.database import db
        stats = db.get_user_stats("health_check_user")
        return True
    except Exception as e:
        raise Exception(f"Database health check failed: {e}")

# Global health monitor instance
health_monitor = HealthMonitor()

# Register common services
health_monitor.register_service("lastfm", check_lastfm_health)
health_monitor.register_service("spotify", check_spotify_health)
health_monitor.register_service("database", check_database_health)