"""
Stress Test & Performance Benchmarks for APEX API
Tests sustained load, concurrent sessions, and resource usage
Run with: python stress_test.py
"""

import asyncio
import time
import statistics
import logging
from typing import List, Dict
import httpx
from uuid import uuid4

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

API_BASE_URL = "http://localhost:7860"
CONCURRENT_SESSIONS = 10  # Number of concurrent sessions
STEPS_PER_SESSION = 5  # Steps per session
WARMUP_REQUESTS = 5  # Requests to warm up


# ============================================================================
# METRICS COLLECTION
# ============================================================================

class PerformanceMetrics:
    """Collect and report performance metrics"""
    
    def __init__(self, name: str):
        self.name = name
        self.latencies: List[float] = []
        self.errors = 0
        self.successes = 0
    
    def add_latency(self, latency_ms: float):
        self.latencies.append(latency_ms)
        self.successes += 1
    
    def add_error(self):
        self.errors += 1
    
    def report(self):
        """Print performance report"""
        if self.successes == 0:
            logger.error(f"{self.name}: All requests failed!")
            return
        
        p50 = statistics.median(self.latencies)
        p95 = statistics.quantiles(self.latencies, n=20)[18] if len(self.latencies) > 20 else max(self.latencies)
        p99 = statistics.quantiles(self.latencies, n=100)[98] if len(self.latencies) > 100 else max(self.latencies)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"{self.name} Performance Report")
        logger.info(f"{'='*60}")
        logger.info(f"  Successes: {self.successes}")
        logger.info(f"  Errors: {self.errors}")
        logger.info(f"  Error Rate: {(self.errors/(self.successes+self.errors)*100):.1f}%")
        logger.info(f"  P50 Latency: {p50:.1f}ms")
        logger.info(f"  P95 Latency: {p95:.1f}ms")
        logger.info(f"  P99 Latency: {p99:.1f}ms")
        logger.info(f"  Min Latency: {min(self.latencies):.1f}ms")
        logger.info(f"  Max Latency: {max(self.latencies):.1f}ms")
        logger.info(f"  Avg Latency: {statistics.mean(self.latencies):.1f}ms")
        logger.info(f"{'='*60}\n")


# ============================================================================
# STRESS TEST SCENARIOS
# ============================================================================

async def warmup(client: httpx.AsyncClient):
    """Warm up the API"""
    logger.info(f"Warming up with {WARMUP_REQUESTS} requests...")
    for i in range(WARMUP_REQUESTS):
        try:
            await client.get(f"{API_BASE_URL}/health")
        except Exception as e:
            logger.error(f"Warmup request {i+1} failed: {e}")
    logger.info("Warmup complete\n")


async def benchmark_reset(client: httpx.AsyncClient) -> PerformanceMetrics:
    """Benchmark reset endpoint"""
    metrics = PerformanceMetrics("Reset /reset endpoint")
    logger.info("Running reset benchmarks...")
    
    payloads = [
        {"domain": "data_pipeline", "difficulty": "easy"},
        {"domain": "code_review", "difficulty": "medium"},
        {"domain": "incident_debug", "difficulty": "hard"},
    ]
    
    for payload in payloads * 10:  # 30 resets total
        try:
            start = time.time()
            response = await client.post(
                f"{API_BASE_URL}/reset",
                json=payload,
                timeout=10.0
            )
            elapsed = (time.time() - start) * 1000
            
            if response.status_code == 200:
                metrics.add_latency(elapsed)
            else:
                logger.warning(f"Reset failed: {response.status_code}")
                metrics.add_error()
        
        except Exception as e:
            logger.error(f"Reset request error: {e}")
            metrics.add_error()
    
    metrics.report()
    return metrics


async def benchmark_step(client: httpx.AsyncClient) -> PerformanceMetrics:
    """Benchmark step endpoint"""
    metrics = PerformanceMetrics("Step /step endpoint")
    logger.info("Running step benchmarks...")
    
    # Reset first
    try:
        reset_response = await client.post(
            f"{API_BASE_URL}/reset",
            json={"domain": "data_pipeline", "difficulty": "easy"},
            timeout=10.0
        )
        if reset_response.status_code != 200:
            logger.error("Failed to reset for step benchmark")
            return metrics
        
        session_id = reset_response.json()["session_id"]
    
    except Exception as e:
        logger.error(f"Reset failed: {e}")
        return metrics
    
    # Multiple steps
    code_samples = [
        "def process(df): return df.head()",
        "def aggregate(df): return df.groupby('id').sum()",
        "def filter_data(df): return df[df['value'] > 0]",
        "def transform(df): return df.fillna(0)",
        "def clean(df): return df.dropna()",
    ]
    
    for code in code_samples * 6:  # 30 steps
        try:
            start = time.time()
            response = await client.post(
                f"{API_BASE_URL}/step",
                json={
                    "session_id": session_id,
                    "code": code
                },
                timeout=10.0
            )
            elapsed = (time.time() - start) * 1000
            
            if response.status_code == 200:
                metrics.add_latency(elapsed)
            else:
                logger.warning(f"Step failed: {response.status_code}")
                metrics.add_error()
        
        except Exception as e:
            logger.error(f"Step request error: {e}")
            metrics.add_error()
    
    metrics.report()
    return metrics


async def benchmark_health(client: httpx.AsyncClient) -> PerformanceMetrics:
    """Benchmark health endpoint"""
    metrics = PerformanceMetrics("Health /health endpoint")
    logger.info("Running health check benchmarks...")
    
    for _ in range(50):  # 50 health checks
        try:
            start = time.time()
            response = await client.get(
                f"{API_BASE_URL}/health",
                timeout=10.0
            )
            elapsed = (time.time() - start) * 1000
            
            if response.status_code == 200:
                metrics.add_latency(elapsed)
            else:
                metrics.add_error()
        
        except Exception as e:
            logger.error(f"Health check error: {e}")
            metrics.add_error()
    
    metrics.report()
    return metrics


async def concurrent_sessions_test(client: httpx.AsyncClient) -> PerformanceMetrics:
    """Test concurrent sessions"""
    metrics = PerformanceMetrics(f"Concurrent Sessions ({CONCURRENT_SESSIONS} sessions)")
    logger.info(f"Testing {CONCURRENT_SESSIONS} concurrent sessions...")
    
    async def run_session():
        try:
            # Reset
            start = time.time()
            reset_response = await client.post(
                f"{API_BASE_URL}/reset",
                json={"domain": "data_pipeline", "difficulty": "easy"},
                timeout=10.0
            )
            
            if reset_response.status_code != 200:
                return False
            
            session_id = reset_response.json()["session_id"]
            
            # Multiple steps
            for i in range(STEPS_PER_SESSION):
                step_response = await client.post(
                    f"{API_BASE_URL}/step",
                    json={
                        "session_id": session_id,
                        "code": f"# Step {i+1}\ndef process(df): return df"
                    },
                    timeout=10.0
                )
                
                if step_response.status_code != 200:
                    return False
            
            elapsed = (time.time() - start) * 1000
            metrics.add_latency(elapsed)
            return True
        
        except Exception as e:
            logger.error(f"Session error: {e}")
            metrics.add_error()
            return False
    
    # Run sessions
    tasks = [run_session() for _ in range(CONCURRENT_SESSIONS)]
    results = await asyncio.gather(*tasks)
    
    success_count = sum(1 for r in results if r)
    logger.info(f"Concurrent sessions: {success_count}/{CONCURRENT_SESSIONS} succeeded")
    
    metrics.report()
    return metrics


async def stress_test_sustained_load(client: httpx.AsyncClient, duration_seconds: int = 30):
    """Sustained load test"""
    metrics = PerformanceMetrics(f"Sustained Load ({duration_seconds}s)")
    logger.info(f"Running sustained load test for {duration_seconds} seconds...")
    
    start_time = time.time()
    request_count = 0
    
    try:
        reset_response = await client.post(
            f"{API_BASE_URL}/reset",
            json={"domain": "data_pipeline", "difficulty": "easy"},
            timeout=10.0
        )
        session_id = reset_response.json()["session_id"]
    except Exception as e:
        logger.error(f"Failed to reset: {e}")
        return metrics
    
    code_samples = [
        "def a(df): return df",
        "def b(df): return df.head()",
        "def c(df): return df.dropna()",
    ]
    code_idx = 0
    
    while time.time() - start_time < duration_seconds:
        try:
            start = time.time()
            response = await client.post(
                f"{API_BASE_URL}/step",
                json={
                    "session_id": session_id,
                    "code": code_samples[code_idx % len(code_samples)]
                },
                timeout=10.0
            )
            elapsed = (time.time() - start) * 1000
            
            if response.status_code == 200:
                metrics.add_latency(elapsed)
                code_idx += 1
            else:
                metrics.add_error()
        
        except Exception as e:
            logger.error(f"Sustained load error: {e}")
            metrics.add_error()
        
        request_count += 1
    
    requests_per_second = request_count / (time.time() - start_time)
    logger.info(f"Throughput: {requests_per_second:.1f} requests/second")
    
    metrics.report()
    return metrics


# ============================================================================
# MAIN EXECUTION
# ============================================================================

async def main():
    """Run all stress tests"""
    logger.info(f"Starting APEX API Stress Tests")
    logger.info(f"Target: {API_BASE_URL}\n")
    
    async with httpx.AsyncClient() as client:
        # Health check first
        try:
            response = await client.get(f"{API_BASE_URL}/health", timeout=5.0)
            if response.status_code != 200:
                logger.error(f"API not responding: {response.status_code}")
                return
            logger.info("✅ API is healthy\n")
        except Exception as e:
            logger.error(f"Cannot connect to API: {e}")
            logger.info(f"Make sure API is running at {API_BASE_URL}")
            return
        
        # Warmup
        await warmup(client)
        
        # Benchmarks
        reset_metrics = await benchmark_reset(client)
        health_metrics = await benchmark_health(client)
        step_metrics = await benchmark_step(client)
        concurrent_metrics = await concurrent_sessions_test(client)
        sustained_metrics = await stress_test_sustained_load(client, duration_seconds=30)
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("STRESS TEST COMPLETE - Summary")
        logger.info("="*60)
        logger.info(f"✅ Health: {health_metrics.successes}/{health_metrics.successes + health_metrics.errors}")
        logger.info(f"✅ Reset: {reset_metrics.successes}/{reset_metrics.successes + reset_metrics.errors}")
        logger.info(f"✅ Step: {step_metrics.successes}/{step_metrics.successes + step_metrics.errors}")
        logger.info(f"✅ Concurrent: {concurrent_metrics.successes}/{concurrent_metrics.successes + concurrent_metrics.errors}")
        logger.info(f"✅ Sustained: {sustained_metrics.successes}/{sustained_metrics.successes + sustained_metrics.errors}")


if __name__ == "__main__":
    asyncio.run(main())
