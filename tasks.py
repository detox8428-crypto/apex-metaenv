"""
APEX Engineering Benchmark - 9 Real-World Tasks
3 domains × 3 difficulties = 9 total tasks
"""

# ============================================================================
# DOMAIN 1: DATA_PIPELINE (Pandas code tasks)
# ============================================================================

DATA_PIPELINE_TASKS = {
    "easy": {
        "task_id": "dp-easy-001",
        "title": "Customer Sales Aggregation",
        "description": (
            "Write a function aggregate_sales(df) that groups sales data by customer_id "
            "and returns the total amount per customer, sorted by amount descending."
        ),
        "function_name": "aggregate_sales",
        "data_sample": (
            "customer_id,product,amount,date\n"
            "C001,laptop,1200,2024-01-15\n"
            "C001,mouse,25,2024-01-16\n"
            "C002,keyboard,85,2024-01-15\n"
            "C001,monitor,350,2024-01-17"
        ),
        "test_cases": [
            {
                "input": {
                    "customer_id": ["C001", "C001", "C002"],
                    "amount": [1200, 25, 85]
                },
                "expected": {"C001": 1225, "C002": 85}
            }
        ],
        "expected_fix_keywords": ["groupby", "sum"],
        "max_steps": 3
    },
    
    "medium": {
        "task_id": "dp-medium-001",
        "title": "Deduplicate and Clean Transaction Records",
        "description": (
            "Write a function clean_transactions(df) that takes a single transaction dataframe, "
            "drops exact duplicate rows, and fills NaN amounts with 0. "
            "Return the cleaned DataFrame."
        ),
        "function_name": "clean_transactions",
        "data_sample": (
            "transaction_id,amount,status\n"
            "T001,100.00,completed\n"
            "T002,,pending\n"
            "T001,100.00,completed"
        ),
        "test_cases": [
            {
                "input": {
                    "transaction_id": ["T001", "T002", "T001"],
                    "amount": [100.0, None, 100.0],
                    "status": ["completed", "pending", "completed"]
                },
                "expected": 2  # 2 unique rows after dedup (T001 appears once, T002 once)
            }
        ],
        "expected_fix_keywords": ["merge", "drop_duplicates", "fillna"],
        "max_steps": 3
    },
    
    "hard": {
        "task_id": "dp-hard-001",
        "title": "Timezone-Aware DateTime Bug Fix",
        "description": (
            "Fix the function compare_dates(df) which crashes with TypeError "
            "when comparing mixed timezone-aware and timezone-naive timestamps. "
            "Handle both tz-aware and tz-naive data gracefully."
        ),
        "function_name": "compare_dates",
        "data_sample": (
            "event_id,timestamp,tz_info\n"
            "E001,2024-01-15 10:00:00,UTC\n"
            "E002,2024-01-15 10:30:00,None\n"
            "E003,2024-01-15 11:00:00+00:00,UTC"
        ),
        "test_cases": [
            {
                "input": {
                    "event_id": ["E001", "E002", "E003"],
                    "timestamp": ["2024-01-15 10:00:00 UTC", "2024-01-15 10:30:00", "2024-01-15 11:00:00 UTC"]
                },
                "expected": 3  # Should handle 3 rows without crashing
            }
        ],
        "expected_fix_keywords": ["tz_localize", "tz_convert", "dt.tz"],
        "max_steps": 3
    }
}


# ============================================================================
# DOMAIN 2: CODE_REVIEW (Find bugs + explain impact)
# ============================================================================

CODE_REVIEW_TASKS = {
    "easy": {
        "task_id": "cr-easy-001",
        "title": "N+1 Query Problem",
        "description": (
            "Review this Django code. Identify the N+1 query problem "
            "(loops causing excessive database queries). Explain the production impact "
            "on users and scale. Suggest the fix."
        ),
        "code_to_review": '''
def get_user_orders(user_ids):
    """Fetch orders for multiple users - SLOW!"""
    users = User.objects.filter(id__in=user_ids)
    result = []
    for user in users:
        # N+1 PROBLEM: queries database once per user!
        orders = Order.objects.filter(user=user)
        result.append({
            "user": user.name,
            "orders": orders.count(),
            "total": sum(o.amount for o in orders)
        })
    return result
        ''',
        "expected_production_keywords": ["N+1", "query", "users", "scale", "database", "timeout", "performance"],
        "expected_fix_keywords": ["select_related", "prefetch_related", "annotate", "Count", "Sum"],
        "max_steps": 1
    },
    
    "medium": {
        "task_id": "cr-medium-001",
        "title": "Race Condition in Cache Update",
        "description": (
            "Review this cache increment code. Identify the race condition "
            "(time-of-check to time-of-use bug). Explain why this fails under "
            "concurrent load and the production impact."
        ),
        "code_to_review": '''
def increment_counter(key, redis_client):
    """Increment counter - NOT ATOMIC!"""
    count = redis_client.get(key) or 0
    # RACE CONDITION: Between read and write, another request can increment
    time.sleep(0.01)  # Simulate processing
    redis_client.set(key, count + 1)
    return count + 1
        ''',
        "expected_production_keywords": ["race", "concurrent", "atomic", "users", "count", "lost update", "consistency"],
        "expected_fix_keywords": ["INCR", "atomic", "lock", "transaction"],
        "max_steps": 1
    },
    
    "hard": {
        "task_id": "cr-hard-001",
        "title": "Silent Data Corruption in Bulk Update",
        "description": (
            "Review this bulk update code. Identify the CRITICAL bug: missing WHERE clause "
            "silently updates ALL rows instead of target set. Explain the business impact "
            "and how this could cause outage."
        ),
        "code_to_review": '''
def deactivate_expired_accounts():
    """Deactivate old accounts - DISASTER!"""
    expired_date = timezone.now() - timedelta(days=365)
    # BUG: Missing WHERE clause - updates ALL accounts, not just expired!
    User.objects.update(is_active=False)  # WHOOPS
    
    # This silently deactivates 10 million users instead of 1000
        ''',
        "expected_production_keywords": ["WHERE", "all", "silent", "data loss", "outage", "users", "deactivated", "critical"],
        "expected_fix_keywords": ["filter", "WHERE", "UPDATE...WHERE", "conditional"],
        "max_steps": 1
    }
}


# ============================================================================
# DOMAIN 3: INCIDENT_DEBUG (Multi-step SRE diagnostics)
# ============================================================================

INCIDENT_DEBUG_TASKS = {
    "easy": {
        "task_id": "id-easy-001",
        "title": "Service Timeout Diagnosis",
        "description": (
            "Users report login failures. The auth service is timing out. "
            "You're given logs from each step. Diagnose the root cause incrementally."
        ),
        "steps": [
            {
                "step": 1,
                "log": (
                    "[14:32:15] ERROR auth-service: Connection timeout after 30s\n"
                    "[14:32:20] ERROR auth-service: Retry 1/3 started\n"
                    "[14:32:45] ERROR auth-service: Retry 1 failed - timeout"
                ),
                "expected_keywords": ["timeout", "connection", "auth", "retry", "30s"]
            }
        ]
    },
    
    "medium": {
        "task_id": "id-medium-001",
        "title": "Cascading Failure - Connection Pool",
        "description": (
            "Your application is serving 10x normal traffic. Diagnose why "
            "everything is timing out. Fix appears to create new problems."
        ),
        "steps": [
            {
                "step": 1,
                "log": (
                    "[15:00:00] ALERT: p99 latency 50ms → 8000ms\n"
                    "[15:00:05] ERROR db-pool: All 10 connections in use\n"
                    "[15:00:10] WARN db: Queue depth 2,847 requests waiting"
                ),
                "expected_keywords": ["connection pool", "exhausted", "queue", "database", "latency"]
            },
            {
                "step": 2,
                "log": (
                    "[15:00:30] INFO: Increased pool to 100 connections\n"
                    "[15:00:35] CRITICAL: Retry storm detected!\n"
                    "[15:00:40] ERROR: 50,000 retry requests/sec flooding database"
                ),
                "expected_keywords": ["retry", "storm", "cascading", "flooding", "backoff"]
            }
        ]
    },
    
    "hard": {
        "task_id": "id-hard-001",
        "title": "Distributed System Meltdown",
        "description": (
            "Complete infrastructure failure. Multiple cascading failures. "
            "You must diagnose and fix each layer to restore service."
        ),
        "steps": [
            {
                "step": 1,
                "log": (
                    "[16:00:00] CRITICAL US-East-3: Database connection pool FULL\n"
                    "[16:00:02] ERROR: New connection requests BLOCKED\n"
                    "[16:00:05] WARN: Cache miss rate jumped to 87%"
                ),
                "expected_keywords": ["pool", "connection", "database", "blocking", "cache"]
            },
            {
                "step": 2,
                "log": (
                    "[16:00:15] ERROR: Client retry logic hammering database\n"
                    "[16:00:20] CRITICAL: 1,000,000 retries/sec\n"
                    "[16:00:25] FATAL: Circuit breaker should have opened!"
                ),
                "expected_keywords": ["retry", "hammer", "circuit breaker", "exponential backoff", "timeout"]
            },
            {
                "step": 3,
                "log": (
                    "[16:00:35] ERROR: Circuit breaker is STUCK OPEN\n"
                    "[16:00:40] User-facing: All requests FAILING even though database recovering\n"
                    "[16:00:45] CRITICAL: Need manual intervention to reset circuit"
                ),
                "expected_keywords": ["circuit breaker", "stuck", "reset", "manual", "graceful degradation"]
            }
        ]
    }
}


# ============================================================================
# COMBINED TASK REGISTRY
# ============================================================================

TASKS = {
    "data_pipeline": DATA_PIPELINE_TASKS,
    "code_review": CODE_REVIEW_TASKS,
    "incident_debug": INCIDENT_DEBUG_TASKS,
}


def get_task(domain: str, difficulty: str) -> dict:
    """Get a specific task"""
    return TASKS.get(domain, {}).get(difficulty, {})


def get_task_by_id(task_id: str) -> tuple:
    """
    Get task by task_id string (e.g., 'easy-solve-001')
    Returns (domain, difficulty, task) tuple, or (None, None, None) if not found
    """
    for domain, difficulties in TASKS.items():
        for difficulty, task in difficulties.items():
            if task.get("task_id") == task_id:
                return domain, difficulty, task
    return None, None, None


def get_all_tasks(domain: str) -> dict:
    """Get all tasks for a domain"""
    return TASKS.get(domain, {})
