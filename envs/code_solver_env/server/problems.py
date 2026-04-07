"""Real-world data pipeline tasks for APEX Data Pipeline Engineer Environment"""

import json
import random
import pandas as pd
from typing import Dict, Any, List, Tuple

# ============================================================================
# TASK TYPE 1: PIPELINE WRITER (solve mode) - Agent writes code from scratch
# ============================================================================

SOLVE_TASKS = [
    # ==================== EASY SOLVE ====================
    {
        "task_id": "easy-solve-001",
        "title": "Sales CSV Aggregator",
        "difficulty": "easy",
        "task_type": "solve",
        "description": "Write a function that returns total spend per customer from sales CSV, sorted descending by amount. You have columns: customer_id, product, amount, date",
        "function_signature": "def aggregate_sales(df: pd.DataFrame) -> pd.DataFrame:\n    # Returns DataFrame with columns: customer_id, total_amount\n    # Sorted by total_amount descending",
        "data_sample": {
            "format": "csv",
            "content": "customer_id,product,amount,date\nC001,laptop,1200.00,2024-01-15\nC001,mouse,25.00,2024-01-16\nC002,keyboard,75.00,2024-01-15\nC003,laptop,1200.00,2024-01-17\nC002,laptop,1200.00,2024-01-18",
            "description": "Sales transactions from January 2024"
        },
        "test_cases": [
            {"csv": "customer_id,product,amount\nC001,laptop,1200\nC001,mouse,25\nC002,keyboard,75\nC003,laptop,1200\nC002,laptop,1200", "assertions": [
                "len(result) == 3",
                "list(result.columns) == ['customer_id', 'total_amount']",
                "result.iloc[0]['customer_id'] == 'C002'",
                "result.iloc[0]['total_amount'] == 2475.0",
                "result.iloc[1]['total_amount'] == 1225.0"
            ]}
        ],
        "visible_test_count": 2,
        "hidden_test_count": 3
    },
    {
        "task_id": "easy-solve-002",
        "title": "JSON Customer Flattener",
        "difficulty": "easy",
        "task_type": "solve",
        "description": "Flatten nested JSON customer records into DataFrame. Input has customers array with nested address objects. Output should have columns: id, name, city, zip",
        "function_signature": "def flatten_customers(data: dict) -> pd.DataFrame:\n    # Flatten nested JSON into DataFrame",
        "data_sample": {
            "format": "json",
            "content": '{\"customers\": [{\"id\": \"C001\", \"name\": \"Alice\", \"address\": {\"city\": \"NYC\", \"zip\": \"10001\"}}, {\"id\": \"C002\", \"name\": \"Bob\", \"address\": {\"city\": \"LA\", \"zip\": \"90001\"}}]}',
            "description": "Customer records with nested address"
        },
        "test_cases": [
            {"json": '{\"customers\": [{\"id\": \"C001\", \"name\": \"Alice\", \"address\": {\"city\": \"NYC\", \"zip\": \"10001\"}}]}', "assertions": [
                "len(result) == 1",
                "list(result.columns) == ['id', 'name', 'city', 'zip']",
                "result.iloc[0]['city'] == 'NYC'"
            ]}
        ],
        "visible_test_count": 2,
        "hidden_test_count": 3
    },
    {
        "task_id": "easy-solve-003",
        "title": "Date Format Standardizer",
        "difficulty": "easy",
        "task_type": "solve",
        "description": "Convert mixed date formats in a CSV to YYYY-MM-DD format. Handle both MM/DD/YYYY and DD-MM-YYYY formats.",
        "function_signature": "def standardize_dates(df: pd.DataFrame) -> pd.DataFrame:\n    # Convert all dates to YYYY-MM-DD format",
        "data_sample": {
            "format": "csv",
            "content": "order_id,date\nO001,01/15/2024\nO002,15-01-2024\nO003,02/20/2024",
            "description": "Orders with mixed date formats"
        },
        "test_cases": [
            {"csv": "order_id,date\nO001,01/15/2024\nO002,15-01-2024", "assertions": [
                "result.iloc[0]['date'] == '2024-01-15'",
                "result.iloc[1]['date'] == '2024-01-15'"
            ]}
        ],
        "visible_test_count": 2,
        "hidden_test_count": 3
    },
    # ==================== MEDIUM SOLVE ====================
    {
        "task_id": "medium-solve-001",
        "title": "Duplicate Transaction Detector",
        "difficulty": "medium",
        "task_type": "solve",
        "description": "Detect duplicate transactions: same account + amount + merchant within 60 seconds. Add is_duplicate boolean column.",
        "function_signature": "def detect_duplicates(df: pd.DataFrame) -> pd.DataFrame:\n    # Add is_duplicate column (bool) - flags duplicates within 60s window",
        "data_sample": {
            "format": "csv",
            "content": "tx_id,account,amount,timestamp,merchant\nT001,ACC123,50.00,2024-01-15 10:30:00,Amazon\nT002,ACC123,50.00,2024-01-15 10:30:05,Amazon\nT003,ACC456,200.00,2024-01-15 11:00:00,Walmart\nT004,ACC123,75.00,2024-01-15 12:00:00,Amazon",
            "description": "Bank transactions with potential duplicates"
        },
        "test_cases": [
            {"csv": "tx_id,account,amount,timestamp,merchant\nT001,ACC123,50,2024-01-15 10:30:00,Amazon\nT002,ACC123,50,2024-01-15 10:30:05,Amazon", "assertions": [
                "result.iloc[1]['is_duplicate'] == True",
                "result.iloc[0]['is_duplicate'] == False"
            ]}
        ],
        "visible_test_count": 1,
        "hidden_test_count": 4
    },
    {
        "task_id": "medium-solve-002",
        "title": "Time Series Resampler",
        "difficulty": "medium",
        "task_type": "solve",
        "description": "Resample sensor readings to 1-hour intervals, forward-fill missing values, compute rolling 3-hour average.",
        "function_signature": "def resample_timeseries(df: pd.DataFrame) -> pd.DataFrame:\n    # Resample to 1-hour intervals, forward-fill, compute 3-hour rolling mean",
        "data_sample": {
            "format": "csv",
            "content": "timestamp,sensor_value\n2024-01-15 10:00:00,20.5\n2024-01-15 10:15:00,21.3\n2024-01-15 10:45:00,19.8",
            "description": "Irregular sensor readings"
        },
        "test_cases": [
            {"csv": "timestamp,sensor_value\n2024-01-15 10:00:00,20.5\n2024-01-15 10:30:00,21.0", "assertions": [
                "len(result) >= 2",
                "'rolling_mean' in result.columns"
            ]}
        ],
        "visible_test_count": 1,
        "hidden_test_count": 4
    },
    {
        "task_id": "medium-solve-003",
        "title": "Data Quality Validator",
        "difficulty": "medium",
        "task_type": "solve",
        "description": "Check data quality: detect missing values, outliers (>3 std), and invalid email formats. Return quality report.",
        "function_signature": "def validate_data_quality(df: pd.DataFrame) -> dict:\n    # Returns dict with missing_count, outlier_count, invalid_emails, quality_score",
        "data_sample": {
            "format": "csv",
            "content": "user_id,email,age\nU001,alice@example.com,25\nU002,bob@invalid,28\nU003,,30\nU004,charlie@example.com,150",
            "description": "Customer data with quality issues"
        },
        "test_cases": [
            {"csv": "user_id,email,age\nU001,alice@example.com,25\nU002,bob@invalid,28\nU003,,30", "assertions": [
                "result['missing_count'] == 1",
                "result['invalid_emails'] == 1"
            ]}
        ],
        "visible_test_count": 1,
        "hidden_test_count": 4
    },
    # ==================== HARD SOLVE ====================
    {
        "task_id": "hard-solve-001",
        "title": "Multi-source Data Merger",
        "difficulty": "hard",
        "task_type": "solve",
        "description": "Merge 3 CSV files (sales, returns, inventory) with inconsistent column names and date formats. Standardize names and compute net_revenue per product.",
        "function_signature": "def merge_pipeline(sales_df: pd.DataFrame, returns_df: pd.DataFrame, inventory_df: pd.DataFrame) -> pd.DataFrame:\n    # Merge all 3 sources, standardize columns, compute net_revenue",
        "data_sample": {
            "format": "csv",
            "content": "SALES: product_id,amount\\nP001,1000\\nP002,500\\nRETURNS: prod_id,return_amount\\nP001,100\\nINVENTORY: item_id,stock_qty\\nP001,50\\nP002,30",
            "description": "Three sources with different column naming"
        },
        "test_cases": [
            {"files": {"sales": "product_id,amount\nP001,1000", "returns": "prod_id,return_amount\nP001,100", "inventory": "item_id,stock_qty\nP001,50"}, "assertions": [
                "len(result) == 1",
                "result.iloc[0]['net_revenue'] == 900"
            ]}
        ],
        "visible_test_count": 0,
        "hidden_test_count": 5
    },
    {
        "task_id": "hard-solve-002",
        "title": "Log Parser and Anomaly Detector",
        "difficulty": "hard",
        "task_type": "solve",
        "description": "Parse Apache-format server logs into DataFrame. Detect IPs with >5 failed (4xx/5xx) requests in any 10-minute window.",
        "function_signature": "def parse_and_detect_anomalies(logs: str) -> Dict[str, Any]:\n    # Parse logs, return anomalous_ips list and detailed DataFrame",
        "data_sample": {
            "format": "log",
            "content": '192.168.1.1 - - [15/Jan/2024:10:30:00] \"GET /api/users HTTP/1.1\" 200 1234\n192.168.1.2 - - [15/Jan/2024:10:30:01] \"POST /api/login HTTP/1.1\" 401 89\n192.168.1.1 - - [15/Jan/2024:10:30:02] \"GET /api/admin HTTP/1.1\" 403 45',
            "description": "Apache-format server access logs"
        },
        "test_cases": [
            {"logs": '192.168.1.1 - - [15/Jan/2024:10:30:00] \"GET / HTTP/1.1\" 404 100\n192.168.1.1 - - [15/Jan/2024:10:30:05] \"GET / HTTP/1.1\" 404 100\n192.168.1.1 - - [15/Jan/2024:10:30:10] \"GET / HTTP/1.1\" 404 100\n192.168.1.1 - - [15/Jan/2024:10:30:15] \"GET / HTTP/1.1\" 404 100\n192.168.1.1 - - [15/Jan/2024:10:30:20] \"GET / HTTP/1.1\" 404 100\n192.168.1.1 - - [15/Jan/2024:10:30:25] \"GET / HTTP/1.1\" 404 100', "assertions": [
                "'192.168.1.1' in result.get('anomalous_ips', [])"
            ]}
        ],
        "visible_test_count": 0,
        "hidden_test_count": 5
    },
    {
        "task_id": "hard-solve-003",
        "title": "ETL Pipeline with Schema Validation",
        "difficulty": "hard",
        "task_type": "solve",
        "description": "Build ETL: extract CSV, transform (clean nulls, dedupe, validate types), load to parquet. Handle schema evolution gracefully.",
        "function_signature": "def etl_pipeline(input_csv: str, schema: dict) -> Tuple[pd.DataFrame, dict]:\n    # Returns (cleaned_df, quality_report)",
        "data_sample": {
            "format": "csv",
            "content": "order_id,customer_id,amount,date\nO001,C001,100.50,2024-01-15\nO001,C001,100.50,2024-01-15\nO002,C002,,2024-01-16\nO003,invalid,150.00,2024-13-40",
            "description": "Raw order data with quality issues"
        },
        "test_cases": [
            {"csv": "order_id,customer_id,amount\nO001,C001,100.50\nO001,C001,100.50", "assertions": [
                "len(result[0]) == 1"
            ]}
        ],
        "visible_test_count": 0,
        "hidden_test_count": 5
    },
    {
        "task_id": "hard-solve-004",
        "title": "CDC Pipeline Debugger",
        "difficulty": "hard",
        "task_type": "solve",
        "description": "Fix a Change Data Capture pipeline that produces duplicate records when events arrive out of order. Classic Kafka/streaming problem: you need deduplication logic using event timestamps to identify and remove duplicates.",
        "function_signature": "def deduplicate_events(df: pd.DataFrame) -> pd.DataFrame:\n    # Remove duplicate events using timestamp-based deduplication\n    # Return DataFrame with duplicates removed",
        "data_sample": {
            "format": "csv",
            "content": "event_id,user_id,action,timestamp,sequence_num\n1,U001,login,2024-01-15 10:00:00,1\n2,U001,login,2024-01-15 10:00:00,1\n3,U001,view,2024-01-15 10:00:05,2\n4,U001,login,2024-01-15 10:00:00,1\n5,U002,purchase,2024-01-15 10:00:03,5",
            "description": "Event stream with out-of-order duplicates (events 1,2,4 are duplicates)"
        },
        "test_cases": [
            {"csv": "event_id,user_id,action,timestamp,sequence_num\n1,U001,login,2024-01-15 10:00:00,1\n2,U001,login,2024-01-15 10:00:00,1\n3,U001,view,2024-01-15 10:00:05,2", "assertions": [
                "len(result) == 2",
                "result['event_id'].tolist() in [[1, 3], [2, 3]]",
                "result.iloc[0]['action'] == 'login'",
                "result.iloc[1]['action'] == 'view'"
            ]}
        ],
        "visible_test_count": 1,
        "hidden_test_count": 4
    },
    {
        "task_id": "hard-solve-005",
        "title": "Schema Drift Detector",
        "difficulty": "hard",
        "task_type": "solve",
        "description": "Upstream data source silently changed column types. Write a schema validation function that detects drift (data type changes, new columns, dropped columns) and returns a structured report of what changed. Real scenario: Meta's data pipelines ingest from hundreds of sources.",
        "function_signature": "def detect_schema_drift(current_df: pd.DataFrame, expected_schema: dict) -> dict:\n    # Return dict with 'status' (ok/warning/error), 'changes' list, 'details' dict",
        "data_sample": {
            "format": "csv",
            "content": "user_id,name,age,account_balance,signup_date,country\nU001,Alice,25,1000.50,2024-01-15,US\nU002,Bob,32,2500.75,2024-01-14,CA\nU003,Charlie,28,,2024-01-10,US",
            "description": "User data that changed type (age was int now string in upstream, balance might be NULL)"
        },
        "test_cases": [
            {"csv": "user_id,name,age,account_balance\nU001,Alice,25,1000.50\nU002,Bob,thirty,2500.75", "schema": {"user_id": "int", "name": "str", "age": "int", "account_balance": "float"}, "assertions": [
                "result['status'] in ['warning', 'error']",
                "len(result['changes']) > 0",
                "any('age' in str(c).lower() for c in result['changes'])"
            ]}
        ],
        "visible_test_count": 0,
        "hidden_test_count": 5
    }
]

# ============================================================================
# TASK TYPE 2: PIPELINE REVIEWER (review mode) - Agent identifies bugs
# ============================================================================

REVIEW_TASKS = [
    # ==================== EASY REVIEW ====================
    {
        "task_id": "easy-review-001",
        "title": "Wrong GroupBy Column",
        "difficulty": "easy",
        "task_type": "review",
        "description": "Review a buggy aggregation function. The bug is in the groupby column selection.",
        "function_signature": "def get_top_customers(df):",
        "data_sample": {
            "format": "csv",
            "content": "customer_id,product,amount\nC001,laptop,1200\nC001,mouse,25\nC002,keyboard,75",
            "description": "Sales data"
        },
        "current_code": "def get_top_customers(df):\n    return df.groupby('product')['amount'].sum().sort_values(ascending=False).head(5)",
        "bug_type": "wrong_aggregation",
        "bug_location": "line 2",
        "explanation": "The code groups by 'product' instead of 'customer_id', causing incorrect aggregation. It should group by customer_id to get total spend per customer.",
        "test_cases": [
            {"csv": "customer_id,product,amount\nC001,laptop,1200\nC001,mouse,25", "assertions": [
                "len(result) == 2",
                "list(result.index)[0] == 'C001'"
            ]}
        ],
        "visible_test_count": 2,
        "hidden_test_count": 3
    },
    {
        "task_id": "easy-review-002",
        "title": "Missing fillna Before Calculation",
        "difficulty": "easy",
        "task_type": "review",
        "description": "Review code that calculates average without handling NaN values properly.",
        "function_signature": "def calculate_avg_order(df):",
        "data_sample": {
            "format": "csv",
            "content": "order_id,amount\nO001,100\nO002,\nO003,150",
            "description": "Orders with some missing amounts"
        },
        "current_code": "def calculate_avg_order(df):\n    return df['amount'].mean()",
        "bug_type": "missing_null_handling",
        "bug_location": "line 2",
        "explanation": "The code uses mean() which skips NaN, but the result is misleading. Should explicitly fill NaN with 0 or handle them explicitly based on business logic.",
        "test_cases": [
            {"csv": "order_id,amount\nO001,100\nO002,\nO003,150", "assertions": [
                "isinstance(result, float)"
            ]}
        ],
        "visible_test_count": 2,
        "hidden_test_count": 3
    },
    {
        "task_id": "easy-review-003",
        "title": "Wrong Filter Condition",
        "difficulty": "easy",
        "task_type": "review",
        "description": "Review filtering logic that uses wrong comparison.",
        "function_signature": "def get_high_value_orders(df):",
        "data_sample": {
            "format": "csv",
            "content": "order_id,amount\nO001,100\nO002,1000\nO003,500",
            "description": "Orders with different amounts"
        },
        "current_code": "def get_high_value_orders(df):\n    return df[df['amount'] < 500]",
        "bug_type": "wrong_filter",
        "bug_location": "line 2",
        "explanation": "Filter uses < instead of >=. Should return orders with amount >= 500 (high-value), not less than 500.",
        "test_cases": [
            {"csv": "order_id,amount\nO001,100\nO002,1000", "assertions": [
                "len(result) == 1",
                "result.iloc[0]['amount'] == 1000"
            ]}
        ],
        "visible_test_count": 2,
        "hidden_test_count": 3
    },
    # ==================== MEDIUM REVIEW ====================
    {
        "task_id": "medium-review-001",
        "title": "Wrong Merge Type (inner vs left)",
        "difficulty": "medium",
        "task_type": "review",
        "description": "Review a merge that loses data by using wrong join type.",
        "function_signature": "def merge_sales_returns(sales_df, returns_df):",
        "data_sample": {
            "format": "csv",
            "content": "SALES: order_id,amount\\nO001,100\\nO002,200\\nRETURNS: order_id,return_amount\\nO001,10",
            "description": "Sales and returns with different row counts"
        },
        "current_code": "def merge_sales_returns(sales_df, returns_df):\n    merged = sales_df.merge(returns_df, on='order_id', how='inner')\n    merged['net'] = merged['amount'] - merged['return_amount'].fillna(0)\n    return merged",
        "bug_type": "wrong_merge",
        "bug_location": "line 2",
        "explanation": "Using inner join drops sales with no returns (O002). Should use left join to keep all sales records. Returns without matches should have NaN in return_amount.",
        "test_cases": [
            {"files": {"sales": "order_id,amount\nO001,100\nO002,200", "returns": "order_id,return_amount\nO001,10"}, "assertions": [
                "len(result) == 2",
                "result.iloc[1]['net'] == 200"
            ]}
        ],
        "visible_test_count": 1,
        "hidden_test_count": 2
    },
    {
        "task_id": "medium-review-002",
        "title": "Off-by-One in Filtering",
        "difficulty": "medium",
        "task_type": "review",
        "description": "Review filtering that excludes the boundary case.",
        "function_signature": "def get_recent_records(df, days):",
        "data_sample": {
            "format": "csv",
            "content": "record_id,date,value\nR001,2024-01-15,100\nR002,2024-01-14,200",
            "description": "Records with dates"
        },
        "current_code": "def get_recent_records(df, days):\n    cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)\n    return df[df['date'] > cutoff]",
        "bug_type": "off_by_one",
        "bug_location": "line 3",
        "explanation": "Uses > instead of >=. This excludes records exactly 'days' old. Should use >= to include the boundary.",
        "test_cases": [
            {"csv": "record_id,date\nR001,2024-01-15\nR002,2024-01-14", "assertions": [
                "len(result) >= 2"
            ]}
        ],
        "visible_test_count": 2,
        "hidden_test_count": 3
    },
    {
        "task_id": "medium-review-003",
        "title": "Type Mismatch in Comparison",
        "difficulty": "medium",
        "task_type": "review",
        "description": "Review code comparing string and numeric types.",
        "function_signature": "def filter_by_amount(df):",
        "data_sample": {
            "format": "csv",
            "content": "order_id,amount\nO001,100\nO002,200.5",
            "description": "Orders with amounts"
        },
        "current_code": "def filter_by_amount(df):\n    return df[df['amount'] > '150']",
        "bug_type": "data_type_error",
        "bug_location": "line 2",
        "explanation": "Comparing numeric column to string '150'. Should be numeric 150. This causes wrong comparison behavior (string comparison vs numeric).",
        "test_cases": [
            {"csv": "order_id,amount\nO001,100\nO002,200", "assertions": [
                "len(result) == 1"
            ]}
        ],
        "visible_test_count": 2,
        "hidden_test_count": 3
    },
    # ==================== HARD REVIEW ====================
    {
        "task_id": "hard-review-001",
        "title": "Silent Data Loss in Chained Operations",
        "difficulty": "hard",
        "task_type": "review",
        "description": "Review code that silently loses rows due to inplace parameter misunderstanding.",
        "function_signature": "def clean_pipeline(df):",
        "data_sample": {
            "format": "csv",
            "content": "id,value,status\n1,100,active\n2,,inactive\n3,300,active",
            "description": "Data with nulls and status"
        },
        "current_code": "def clean_pipeline(df):\n    df.dropna(inplace=True)\n    df[df['value'] > 100].reset_index(inplace=True)\n    return df",
        "bug_type": "wrong_aggregation",
        "bug_location": "line 3",
        "explanation": "The reset_index with inplace=True modifies df, but the filter on line 2 is not assigned back to df. Should assign: df = df[df['value'] > 100].reset_index(drop=True)",
        "test_cases": [
            {"csv": "id,value\n1,100\n2,200\n3,300", "assertions": [
                "len(result) == 2"
            ]}
        ],
        "visible_test_count": 1,
        "hidden_test_count": 2
    },
    {
        "task_id": "hard-review-002",
        "title": "Timezone-Naive vs Timezone-Aware Comparison",
        "difficulty": "hard",
        "task_type": "review",
        "description": "Review code comparing timezone-aware and timezone-naive timestamps.",
        "function_signature": "def filter_by_timestamp(df):",
        "data_sample": {
            "format": "csv",
            "content": "id,timestamp\n1,2024-01-15 10:00:00+00:00\n2,2024-01-15 11:00:00",
            "description": "Mixed timezone data"
        },
        "current_code": "def filter_by_timestamp(df):\n    cutoff = pd.Timestamp('2024-01-15 10:30:00')\n    return df[df['timestamp'] > cutoff]",
        "bug_type": "data_type_error",
        "bug_location": "line 2-3",
        "explanation": "Mixing timezone-aware (with +00:00) and timezone-naive timestamps causes comparison errors. Should make both same: either both aware or both naive.",
        "test_cases": [
            {"csv": "id,timestamp\n1,2024-01-15 10:00:00", "assertions": [
                "isinstance(result, pd.DataFrame)"
            ]}
        ],
        "visible_test_count": 1,
        "hidden_test_count": 2
    },
    {
        "task_id": "hard-review-003",
        "title": "Cascading Groupby-Reset Bug",
        "difficulty": "hard",
        "task_type": "review",
        "description": "Review complex aggregation with forgotten reset_index.",
        "function_signature": "def aggregate_with_ranking(df):",
        "data_sample": {
            "format": "csv",
            "content": "category,item_id,value\nA,I1,100\nA,I2,200\nB,I3,150",
            "description": "Hierarchical data"
        },
        "current_code": "def aggregate_with_ranking(df):\n    grouped = df.groupby('category')['value'].sum().sort_values(ascending=False)\n    grouped['rank'] = range(1, len(grouped) + 1)\n    return grouped",
        "bug_type": "wrong_aggregation",
        "bug_location": "line 3",
        "explanation": "After groupby().sum(), 'grouped' is a Series, not a DataFrame. Cannot add 'rank' column directly. Need .reset_index() first to convert to DataFrame.",
        "test_cases": [
            {"csv": "category,value\nA,100\nA,200\nB,150", "assertions": [
                "isinstance(result, pd.DataFrame)",
                "result.iloc[0]['value'] == 300"
            ]}
        ],
        "visible_test_count": 1,
        "hidden_test_count": 2
    }
]

# ============================================================================
# TASK TYPE 3: PIPELINE DEBUGGER (debug mode) - Agent fixes crashing code
# ============================================================================

DEBUG_TASKS = [
    # ==================== EASY DEBUG ====================
    {
        "task_id": "easy-debug-001",
        "title": "KeyError in Column Access",
        "difficulty": "easy",
        "task_type": "debug",
        "description": "Fix code that crashes on invalid column name.",
        "function_signature": "def process_orders(df):",
        "data_sample": {
            "format": "csv",
            "content": "order_id,qty,price\nO001,2,50.00\nO002,3,75.00",
            "description": "Order data"
        },
        "current_code": "def process_orders(df):\n    df['revenue'] = df['qty'] * df['unit_price']\n    return df",
        "error_message": "KeyError: 'unit_price'",
        "feedback": "The column is named 'price', not 'unit_price'. Fix the column reference.",
        "test_cases": [
            {"csv": "order_id,qty,price\nO001,2,50", "assertions": [
                "'revenue' in result.columns",
                "result.iloc[0]['revenue'] == 100"
            ]}
        ],
        "visible_test_count": 2,
        "hidden_test_count": 3
    },
    {
        "task_id": "easy-debug-002",
        "title": "TypeError in Date Parsing",
        "difficulty": "easy",
        "task_type": "debug",
        "description": "Fix code trying to do arithmetic on string dates.",
        "function_signature": "def calculate_days_old(df):",
        "data_sample": {
            "format": "csv",
            "content": "record_id,date\nR001,2024-01-15\nR002,2024-01-10",
            "description": "Records with date strings"
        },
        "current_code": "def calculate_days_old(df):\n    df['days_old'] = pd.Timestamp.now() - df['date']\n    return df",
        "error_message": "TypeError: unsupported operand type(s) for -: 'Timestamp' and 'str'",
        "feedback": "Need to convert date column to datetime first using pd.to_datetime().",
        "test_cases": [
            {"csv": "record_id,date\nR001,2024-01-15", "assertions": [
                "'days_old' in result.columns"
            ]}
        ],
        "visible_test_count": 2,
        "hidden_test_count": 3
    },
    {
        "task_id": "easy-debug-003",
        "title": "Index Out of Bounds",
        "difficulty": "easy",
        "task_type": "debug",
        "description": "Fix code accessing non-existent DataFrame rows.",
        "function_signature": "def get_first_three(df):",
        "data_sample": {
            "format": "csv",
            "content": "id,value\n1,100\n2,200",
            "description": "Small dataset"
        },
        "current_code": "def get_first_three(df):\n    return df.iloc[0:3]",
        "error_message": "No error technically, but ensure correct behavior with <3 rows",
        "feedback": "Function should handle DataFrames with fewer than 3 rows gracefully.",
        "test_cases": [
            {"csv": "id,value\n1,100\n2,200", "assertions": [
                "len(result) == 2"
            ]}
        ],
        "visible_test_count": 2,
        "hidden_test_count": 3
    },
    # ==================== MEDIUM DEBUG ====================
    {
        "task_id": "medium-debug-001",
        "title": "SettingWithCopyWarning Becomes Bug",
        "difficulty": "medium",
        "task_type": "debug",
        "description": "Fix SettingWithCopyWarning that causes silent data loss.",
        "function_signature": "def transform_data(df):",
        "data_sample": {
            "format": "csv",
            "content": "id,amount,status\n1,100,active\n2,200,inactive\n3,150,active",
            "description": "Data to transform"
        },
        "current_code": "def transform_data(df):\n    active_rows = df[df['status'] == 'active']\n    active_rows['amount'] = active_rows['amount'] * 1.1\n    return df",
        "error_message": "SettingWithCopyWarning and data not actually updated",
        "feedback": "Chained indexing creates a view, not a copy. Use .copy() or use .loc for modification.",
        "test_cases": [
            {"csv": "id,amount,status\n1,100,active\n2,200,inactive", "assertions": [
                "result.iloc[0]['amount'] == 110"
            ]}
        ],
        "visible_test_count": 1,
        "hidden_test_count": 2
    },
    {
        "task_id": "medium-debug-002",
        "title": "Groupby Without Reset Index",
        "difficulty": "medium",
        "task_type": "debug",
        "description": "Fix code that doesn't properly convert grouped Series back to DataFrame.",
        "function_signature": "def aggregate_by_category(df):",
        "data_sample": {
            "format": "csv",
            "content": "category,value\nA,100\nA,200\nB,150",
            "description": "Categorical data"
        },
        "current_code": "def aggregate_by_category(df):\n    result = df.groupby('category')['value'].sum()\n    result['count'] = result.groupby(level=0).size()\n    return result",
        "error_message": "AttributeError or unexpected Series behavior",
        "feedback": "After groupby, result is a Series. Need reset_index() to get DataFrame, then can add more columns.",
        "test_cases": [
            {"csv": "category,value\nA,100\nA,200\nB,150", "assertions": [
                "isinstance(result, pd.DataFrame)",
                "result.iloc[0]['value'] == 300"
            ]}
        ],
        "visible_test_count": 1,
        "hidden_test_count": 2
    },
    {
        "task_id": "medium-debug-003",
        "title": "Memory Error on Large File",
        "difficulty": "medium",
        "task_type": "debug",
        "description": "Fix code that loads entire large CSV, causing memory error.",
        "function_signature": "def process_large_csv(filepath):",
        "data_sample": {
            "format": "csv",
            "content": "Simulated large file scenario",
            "description": "Large dataset warning"
        },
        "current_code": "def process_large_csv(filepath):\n    df = pd.read_csv(filepath)\n    return df[df['value'] > 100].describe()",
        "error_message": "MemoryError: Unable to allocate memory",
        "feedback": "Use chunked reading with chunksize parameter instead of loading entire file.",
        "test_cases": [
            {"csv": "value\n50\n150", "assertions": [
                "isinstance(result, pd.Series)"
            ]}
        ]
    },
    # ==================== HARD DEBUG ====================
    {
        "task_id": "hard-debug-001",
        "title": "Cascading Errors (3-Step Fix)",
        "difficulty": "hard",
        "task_type": "debug",
        "description": "Multi-step debugging: KeyError → TypeError → LogicError. Fix reveals next error.",
        "function_signature": "def complex_pipeline(df):",
        "data_sample": {
            "format": "csv",
            "content": "date,category,amount\n2024-01-15,A,100\n2024-01-16,B,200",
            "description": "Complex data"
        },
        "current_code": "def complex_pipeline(df):\n    df['revenue'] = df['qty'] * df['price']\n    df['date'] = pd.to_datetime(df['date'])\n    df['month'] = df['date'].dt.month\n    return df.groupby('month')['revenue'].sum()",
        "error_message": "Step 1: KeyError: 'qty'",
        "feedback": "Use 'amount' instead of 'qty'. After this fix, additional errors will appear.",
        "test_cases": [
            {"csv": "date,category,amount\n2024-01-15,A,100", "assertions": [
                "isinstance(result, pd.Series)",
                "result.iloc[0] == 100"
            ]}
        ],
        "visible_test_count": 1,
        "hidden_test_count": 2
    },
    {
        "task_id": "hard-debug-002",
        "title": "Silent Wrong Output (No Error)",
        "difficulty": "hard",
        "task_type": "debug",
        "description": "Code runs without error but produces wrong aggregation due to missing reset_index.",
        "function_signature": "def rank_by_category(df):",
        "data_sample": {
            "format": "csv",
            "content": "category,value,rank\nA,100,\nA,200,\nB,150,",
            "description": "Data to rank"
        },
        "current_code": "def rank_by_category(df):\n    df['rank'] = df.groupby('category')['value'].rank(method='dense')\n    return df",
        "error_message": "No error, but rank column is 0.0 or NaN everywhere",
        "feedback": "The groupby.rank() returns a Series with same index as df. Assignment might fail silently.",
        "test_cases": [
            {"csv": "category,value\nA,100\nA,200\nB,150", "assertions": [
                "result['rank'].notna().all()",
                "result.iloc[1]['rank'] > result.iloc[0]['rank']"
            ]}
        ],
        "visible_test_count": 1,
        "hidden_test_count": 2
    },
    {
        "task_id": "hard-debug-003",
        "title": "Locale-Specific Float Parsing",
        "difficulty": "hard",
        "task_type": "debug",
        "description": "Fix code that mishandles locale-specific number formats (comma as decimal).",
        "function_signature": "def parse_european_csv(df):",
        "data_sample": {
            "format": "csv",
            "content": 'id,amount\n1,100.50\n2,200.75',
            "description": "European format with comma decimals",
        },
        "current_code": "def parse_european_csv(df):\n    df['amount'] = pd.to_numeric(df['amount'])\n    return df['amount'].sum()",
        "error_message": "ValueError: Unable to parse string",
        "feedback": "Need to replace comma with period before parsing, or use decimal parameter.",
        "test_cases": [
            {"csv": "id,amount\n1,100.50\n2,200.75", "assertions": [
                "isinstance(result, float)",
                "result == 301.25"
            ]}
        ],
        "visible_test_count": 1,
        "hidden_test_count": 2
    }
]

# ============================================================================
# DOMAIN 2: CODE REVIEW (code_review domain) - Production code review
# ============================================================================

CODE_REVIEW_TASKS = [
    # ==================== EASY CODE REVIEW ====================
    {
        "task_id": "code-review-easy-001",
        "title": "N+1 Query Problem",
        "difficulty": "easy",
        "task_type": "review",
        "domain": "code_review",
        "description": "Review production code with classic N+1 query pattern. Agent must identify the problem, explain production impact (scale, timeouts), and submit a fix.",
        "function_signature": "def get_user_orders(user_ids: list) -> list:",
        "data_sample": {
            "format": "text",
            "content": "# Simulated database queries for 10,000 users\n# Current approach: 10,001 queries (1 per user + 1 per order)\n# Fixed approach: 2 queries total (1 for users, 1 batch for orders)",
            "description": "Database query scaling scenario"
        },
        "code_context": "def get_user_orders(user_ids):\n    result = []\n    for user_id in user_ids:  # N+1: queries DB once per user\n        orders = db.query(f'SELECT * FROM orders WHERE user_id={user_id}')\n        result.extend(orders)\n    return result",
        "expected_issues": [
            "N+1 query pattern",
            "Scale: 10,000 users = 10,000 queries instead of 1",
            "Production impact: Timeout at scale"
        ],
        "test_cases": [
            {"input": "user_ids=[1,2,3]", "assertions": [
                "'IN' in fixed_code or 'batch' in fixed_code.lower() or 'join' in fixed_code.lower()",
                "fixed_code.count('query') <= 2"
            ]}
        ]
    },
    {
        "task_id": "code-review-easy-002",
        "title": "Silent Float Precision Error",
        "difficulty": "easy",
        "task_type": "review",
        "domain": "code_review",
        "description": "Review code doing monetary calculations with float. Must explain why this causes data corruption in production.",
        "function_signature": "def calculate_total_payment(transactions: list) -> float:",
        "data_sample": {
            "format": "text",
            "content": "# Financial calculations must use Decimal, not float\n# Bug: float has ~15 digits precision, loses cents on large sums",
            "description": "Payment processing scenario"
        },
        "code_context": "def calculate_total_payment(transactions):\n    total = 0.0\n    for tx in transactions:\n        total += tx['amount']  # float addition = rounding errors\n    return total",
        "expected_issues": [
            "Float precision loss in monetary calculations",
            "Silent data corruption (no crash, wrong values)",
            "Production impact: Financial calculations off by fractions of cents"
        ],
        "test_cases": [
            {"input": "transactions=[{'amount': 0.1}, {'amount': 0.2}, ...]", "assertions": [
                "'Decimal' in fixed_code",
                "'decimal' in fixed_code or 'Decimal' in fixed_code"
            ]}
        ]
    },
    {
        "task_id": "code-review-easy-003",
        "title": "Missing Error Handling",
        "difficulty": "easy",
        "task_type": "review",
        "domain": "code_review",
        "description": "Identify missing error handling that causes unhelpful errors in production.",
        "function_signature": "def parse_user_input(user_data: dict) -> dict:",
        "data_sample": {
            "format": "text",
            "content": "# Production errors should be informative, not cryptic",
            "description": "User input parsing"
        },
        "code_context": "def parse_user_input(user_data):\n    return {\n        'age': int(user_data['age']),\n        'email': user_data['email'],\n        'country': user_data['location']['country']\n    }",
        "expected_issues": [
            "Missing try-catch or validation",
            "KeyError if 'location' missing",
            "ValueError if 'age' is not numeric",
            "Production impact: Users see cryptic errors instead of validation messages"
        ],
        "test_cases": [
            {"input": "malformed_data", "assertions": [
                "'try' in fixed_code and 'except' in fixed_code",
                "'except' in fixed_code or 'get(' in fixed_code"
            ]}
        ]
    },
    # ==================== MEDIUM CODE REVIEW ====================
    {
        "task_id": "code-review-medium-001",
        "title": "Race Condition in Async Code",
        "difficulty": "medium",
        "task_type": "review",
        "domain": "code_review",
        "description": "Review async code with race condition (read-modify-write not atomic). Explain why this breaks under concurrency.",
        "function_signature": "async def increment_counter(key: str):",
        "data_sample": {
            "format": "text",
            "content": "# Concurrency issue: between read and write, another request can modify value\n# With 1000 concurrent requests, counter should be 1000 but might be much lower",
            "description": "Concurrent counter increment"
        },
        "code_context": "async def increment_counter(key):\n    count = await cache.get(key) or 0  # RACE: read-modify-write\n    await cache.set(key, count + 1)    # not atomic under concurrency",
        "expected_issues": [
            "Race condition in read-modify-write",
            "Production impact: Lost updates under high concurrency",
            "Fix: Use atomic INCR (Redis) or distributed lock"
        ],
        "test_cases": [
            {"input": "1000 concurrent increments", "assertions": [
                "'INCR' in fixed_code or 'atomic' in fixed_code.lower() or 'lock' in fixed_code.lower()",
                "fixed_code.count('await cache.get') == 0 or 'INCR' in fixed_code"
            ]}
        ]
    },
    {
        "task_id": "code-review-medium-002",
        "title": "Memory Leak in Long-Running Service",
        "difficulty": "medium",
        "task_type": "review",
        "domain": "code_review",
        "description": "Identify memory leak pattern. Must explain why this causes OOM after ~24 hours.",
        "function_signature": "def handle_request(request):",
        "data_sample": {
            "format": "text",
            "content": "# Module-level list grows without cleanup\n# With 1000 requests/sec, each storing 1KB, uses 86GB per day",
            "description": "Memory accumulation scenario"
        },
        "code_context": "# Global cache that grows indefinitely\ncached_results = []\n\ndef handle_request(request):\n    result = process_request(request)\n    cached_results.append(result)  # Never cleared - memory leak\n    return result",
        "expected_issues": [
            "Unbounded list growth in module-level global",
            "Production impact: Service OOMs after ~24 hours, requires restart",
            "Fix: Use bounded cache (LRU, TTL, max size) or cleanup logic"
        ],
        "test_cases": [
            {"input": "10000 requests", "assertions": [
                "'maxsize' in fixed_code or 'TTL' in fixed_code or 'lru' in fixed_code.lower() or 'limit' in fixed_code.lower()",
                "cached_results_not_unbounded_in_fixed_code"
            ]}
        ]
    },
    {
        "task_id": "code-review-medium-003",
        "title": "Incomplete Null Coalescing",
        "difficulty": "medium",
        "task_type": "review",
        "domain": "code_review",
        "description": "Review null handling that misses edge cases.",
        "function_signature": "def get_user_preference(user_id: int, key: str) -> str:",
        "data_sample": {
            "format": "text",
            "content": "# Returns None when preference doesn't exist\n# Caller assumes always string, crashes on NoneType",
            "description": "Preference lookup scenario"
        },
        "code_context": "def get_user_preference(user_id, key):\n    pref = db.query(f'SELECT value FROM preferences WHERE user_id={user_id} AND key={key}')\n    return pref.get('value') if pref else None  # Can return None",
        "expected_issues": [
            "Function can return None but caller expects string",
            "No type annotation warning (Python 3.10+ would catch)",
            "Production impact: Downstream NoneType errors"
        ],
        "test_cases": [
            {"input": "missing_preference", "assertions": [
                "'default' in fixed_code.lower() or \"''\" in fixed_code or '\"\"' in fixed_code",
                "returns_non_null_in_fixed_code"
            ]}
        ]
    },
    # ==================== HARD CODE REVIEW ====================
    {
        "task_id": "code-review-hard-001",
        "title": "Distributed Transaction Bug (Saga Pattern Violation)",
        "difficulty": "hard",
        "task_type": "review",
        "domain": "code_review",
        "description": "Review payment + email confirmation code. Identify: payment succeeds but email fails, leaving partial transaction. Must explain saga pattern fix.",
        "function_signature": "def process_payment_and_confirm(user_id: int, amount: float):",
        "data_sample": {
            "format": "text",
            "content": "# Distributed transaction nightmare:\n# Money debited BUT NO confirmation email sent\n# Customer doesn't know payment succeeded, tries again",
            "description": "Payment workflow scenario"
        },
        "code_context": "def process_payment_and_confirm(user_id, amount):\n    # Step 1: Charge payment\n    payment = charge_card(user_id, amount)  # SUCCESS\n    \n    # Step 2: Send confirmation\n    send_email(user_id, f'Payment of ${amount} confirmed')  # FAILS - email service down\n    \n    # Now: Money taken, no confirmation = angry customer",
        "expected_issues": [
            "No compensation logic if email fails",
            "Partial transaction: payment succeeds, email fails",
            "Production impact: Data loss (customer doesn't know money was taken)",
            "Fix: Implement outbox pattern or compensating transaction (refund)"
        ],
        "test_cases": [
            {"input": "email_service_down", "assertions": [
                "'outbox' in fixed_code.lower() or 'compensat' in fixed_code.lower() or 'refund' in fixed_code.lower()",
                "'except' in fixed_code and ('refund' in fixed_code or 'rollback' in fixed_code)"
            ]}
        ]
    },
    {
        "task_id": "code-review-hard-002",
        "title": "Cache Stampede Under Load",
        "difficulty": "hard",
        "task_type": "review",
        "domain": "code_review",
        "description": "Review cache invalidation code. When cache expires: all requests hit DB simultaneously (thundering herd). Must explain probabilistic early expiry or mutex fix.",
        "function_signature": "def get_cached_resource(key: str, fetch_fn):",
        "data_sample": {
            "format": "text",
            "content": "# Cache expires at T=3600s\n# At T=3601s: 10,000 requests all see expired cache\n# All 10,000 hit database simultaneously = DB collapse (cache stampede)",
            "description": "High-concurrency cache scenario"
        },
        "code_context": "def get_cached_resource(key, fetch_fn):\n    value = cache.get(key)\n    if value is None:  # ALL REQUESTS hit this at same time\n        value = fetch_fn()  # 10,000 concurrent DB queries\n        cache.set(key, value, ttl=3600)\n    return value",
        "expected_issues": [
            "Cache stampede: all concurrent reqs recalculate on expiry",
            "Production impact: Spike in DB load, latency spike, possible cascade failure",
            "Fix: Probabilistic early expiry OR mutex lock on recalculation"
        ],
        "test_cases": [
            {"input": "10000_concurrent_requests_at_expiry", "assertions": [
                "'random' in fixed_code and 'ttl' in fixed_code.lower()",
                "'lock' in fixed_code.lower() or 'mutex' in fixed_code.lower() or ('random' in fixed_code and 'jitter' in fixed_code.lower())"
            ]}
        ]
    },
    {
        "task_id": "code-review-hard-003",
        "title": "Silent Data Corruption via Bulk Update",
        "difficulty": "hard",
        "task_type": "review",
        "domain": "code_review",
        "description": "Review bulk update missing WHERE clause. Accidentally updates ALL rows instead of target set.",
        "function_signature": "def deactivate_expired_accounts():",
        "data_sample": {
            "format": "text",
            "content": "# Bug: Missing WHERE clause updates ALL rows\n# 10M active users deactivated instead of 1000 expired ones",
            "description": "Bulk account update scenario"
        },
        "code_context": "def deactivate_expired_accounts():\n    expired_date = datetime.now() - timedelta(days=365)\n    # MISSING WHERE: updates ALL accounts, not just expired ones\n    db.execute(f'UPDATE users SET status = \"inactive\"')",
        "expected_issues": [
            "Missing WHERE clause in UPDATE",
            "Silent data corruption: all users deactivated, no error logs",
            "Production impact: Massive outage - entire user base locked out",
            "Fix: Add WHERE clause and verify affected row count"
        ],
        "test_cases": [
            {"input": "bulk_update", "assertions": [
                "'WHERE' in fixed_code or 'filter' in fixed_code.lower()",
                "'expired_date' in fixed_code"
            ]}
        ]
    }
]

# ============================================================================
# DOMAIN 3: INCIDENT DEBUGGING (incident_debug domain) - Multi-step SRE scenarios
# ============================================================================

INCIDENT_DEBUG_TASKS = [
    # ==================== EASY INCIDENT DEBUG ====================
    {
        "task_id": "incident-debug-easy-001",
        "title": "500 Error After Deploy",
        "difficulty": "easy",
        "task_type": "debug",
        "domain": "incident_debug",
        "description": "Incident: Service returns HTTP 500 since deploy. Error log shows AttributeError on null object. Multi-step: fix null check, reveals validation error.",
        "code_context": "# deployment at 14:30 UTC changed User.get() method\ndef get_user(user_id):\n    user = db.query(User).filter(User.id == user_id).first()  # Returns None if not found\n    return user  # Was raising UserNotFound before\n\ndef get_user_profile(user_id):\n    user = get_user(user_id)\n    return user.email  # Crash here if user is None",
        "incident": {
            "incident_report": "Service returning HTTP 500 starting 14:32 UTC (2 minutes after deploy)",
            "error_logs": "AttributeError: 'NoneType' has no attribute 'email'\n  File 'users.py', line 42, in get_user_profile\n    return user.email",
            "deploy_info": "Deployment at 14:30 UTC changed User.get() method signature",
            "metrics": {"error_rate": 0.8, "affected_endpoints": ["/api/profile", "/api/settings"]}
        },
        "step_1_hint": "Add null check after get_user() call",
        "step_1_error_after_fix": "KeyError: User missing required field 'email'",
        "step_2_hint": "Add validation that email field exists in user record",
        "expected_steps": 2,
        "test_cases": [
            {"step": 1, "input": "non_existent_user", "assertions": ["raises or returns error"]},
            {"step": 2, "input": "user_without_email", "assertions": ["validates or handles missing field"]}
        ]
    },
    {
        "task_id": "incident-debug-easy-002",
        "title": "Slow API After Traffic Spike",
        "difficulty": "easy",
        "task_type": "debug",
        "domain": "incident_debug",
        "description": "Incident: p99 latency jumped from 50ms to 8000ms during peak traffic. Investigate slow query.",
        "code_context": "# Slow query: missing database index\ndef get_user_orders(user_id):\n    # Query runs full table scan without index\n    return db.query(Orders).filter(Orders.user_id == user_id).all()\n\n# Database schema\nCREATE TABLE orders (\n    id INT PRIMARY KEY,\n    user_id INT,  # NO INDEX HERE\n    created_at TIMESTAMP\n)",
        "incident": {
            "incident_report": "API p99 latency: 50ms → 8000ms during peak traffic (10k req/sec)",
            "error_logs": "Slow query detected: SELECT * FROM orders WHERE user_id=? (2500ms)",
            "metrics": {"p99_latency": 8000, "p50_latency": 2500, "query_time_95th": 3000}
        },
        "step_1_hint": "Identify the missing database index",
        "expected_steps": 1,
        "test_cases": [
            {"input": "identify_index", "assertions": ["'CREATE INDEX' in response or 'user_id' in response"]}
        ]
    },
    {
        "task_id": "incident-debug-easy-003",
        "title": "Authorization Bug Silent Failure",
        "difficulty": "easy",
        "task_type": "debug",
        "domain": "incident_debug",
        "description": "Users report: can't access own data. Error logs silent. Bug: authorization check has wrong logic.",
        "code_context": "def check_user_access(requester_id, resource_owner_id):\n    # BUG: logic inverted - denies access to own data\n    if requester_id == resource_owner_id:  # This is True for valid access\n        return False  # But returns False (denied)\n    return True",
        "incident": {
            "incident_report": "Users report 'access denied' to own data starting 09:45 UTC",
            "error_logs": "Authorization failed for user U001 accessing resource owned by U001",
            "metrics": {"denied_requests": 15000, "normal_rate": 50}
        },
        "step_1_hint": "Fix authorization logic - should allow access when requester_id == owner_id",
        "expected_steps": 1,
        "test_cases": [
            {"input": "own_resource_access", "assertions": ["should return True or allow"]}
        ]
    },
    # ==================== MEDIUM INCIDENT DEBUG ====================
    {
        "task_id": "incident-debug-medium-001",
        "title": "Data Inconsistency: Different Values on Mobile vs Web",
        "difficulty": "medium",
        "task_type": "debug",
        "domain": "incident_debug",
        "description": "Users report: balance shows different amounts on mobile vs web. Root cause: reading from different DB replicas with different replication lag.",
        "code_context": "# Web reads from primary (up-to-date)\nweb_balance = db_primary.query(f'SELECT balance FROM users WHERE id = {user_id}')\n\n# Mobile reads from replica (lagged)\nmobile_balance = db_replica.query(f'SELECT balance FROM users WHERE id = {user_id}')\n\n# Replication lag: 5-10 seconds between primary and replica",
        "incident": {
            "incident_report": "User reports: balance = $1000 on web, $950 on mobile (different values)",
            "error_logs": "No errors - queries succeed but return different results",
            "metrics": {"inconsistency_reports": 342, "db_replica_lag": 8.5}
        },
        "step_1_hint": "Route all balance reads to primary (not replica) to ensure consistency",
        "expected_steps": 1,
        "test_cases": [
            {"input": "balance_query", "assertions": ["uses db_primary or explicit primary specification"]}
        ]
    },
    {
        "task_id": "incident-debug-medium-002",
        "title": "Memory Spike at 3am (Nightly Batch Job)",
        "difficulty": "medium",
        "task_type": "debug",
        "domain": "incident_debug",
        "description": "Incident: Pod OOMKilled at 03:15 UTC every night. Root cause: nightly batch job loads entire dataset into memory instead of streaming.",
        "code_context": "def nightly_export_job():\n    # WRONG: Loads 100M records into memory at once\n    all_records = db.query('SELECT * FROM events WHERE date = today')\n    results = [process(r) for r in all_records]  # All in memory\n    write_to_file(results)",
        "incident": {
            "incident_report": "Pod OOMKilled at 03:15 UTC (every night at job start)",
            "error_logs": "Killed: running nightly_export_job process - memory exhausted",
            "metrics": {"memory_growth": "linear from 12GB at 03:00 to 64GB limit at 03:15"}
        },
        "step_1_hint": "Switch to chunked/streaming processing instead of loading all records",
        "expected_steps": 1,
        "test_cases": [
            {"input": "batch_job_memory", "assertions": ["'batch' in response or 'chunk' in response or 'iterator' in response or 'stream' in response or 'for' in response"]}
        ]
    },
    {
        "task_id": "incident-debug-medium-003",
        "title": "Silent Timezone Bug in Scheduled Tasks",
        "difficulty": "medium",
        "task_type": "debug",
        "domain": "incident_debug",
        "description": "Scheduled jobs running at wrong time. Bug: mixing UTC and local timezone in scheduling logic.",
        "code_context": "# Bug: compares UTC time to local timezone cutoff\nnow_utc = datetime.now(tz=utc)\nif now_utc >= local_cutoff:  # Mixing UTC vs local\n    run_job()\n\n# local_cutoff is 9am but expressed as local time 'America/NY'\n# So job runs at 9am NY time = 2pm UTC in summer (EDT)",
        "incident": {
            "incident_report": "Scheduled jobs running at inconsistent times (off by 4-8 hours)",
            "error_logs": "Job scheduled for 09:00 but ran at 13:00; sometimes doesn't run",
            "metrics": {"inconsistent_execution_times": "true", "timezone_mismatch_detected": "true"}
        },
        "step_1_hint": "Normalize all times to UTC for comparisons, use pytz or aware datetimes",
        "expected_steps": 1,
        "test_cases": [
            {"input": "timezone_comparison", "assertions": ["'UTC' in response or 'pytz' in response or 'aware' in response"]}
        ]
    },
    # ==================== HARD INCIDENT DEBUG ====================
    {
        "task_id": "incident-debug-hard-001",
        "title": "Cascading Failure (3-Step Fix)",
        "difficulty": "hard",
        "task_type": "debug",
        "domain": "incident_debug",
        "description": "3-step cascading incident: (1) DB connection pool exhausted → (2) fix causes retry storm → (3) circuit breaker not resetting. Each fix reveals next symptom.",
        "code_context": "# Step 1: Connection pool exhausted\n# queries = await db.query(...)  # All connections consumed\n\n# Step 2 (after fix 1): Retry storm\n# Agent adds retry loop without backoff - hammers DB harder\n\n# Step 3 (after fix 2): Circuit breaker stuck open\n# Circuit breaker catches errors but never resets",
        "incident": {
            "incident_report": "Service completely down at 15:30 UTC",
            "error_logs": "STEP 1: [ERROR] Database connection timeout: pool exhausted (50/50 connections used)\nDatabases connections timing out, unable to execute queries",
            "metrics": {"error_rate": 1.0, "response_time": "timeout", "db_connections": "50/50"}
        },
        "step_1_fix": "Increase pool size or implement connection pooling",
        "step_1_error_after_fix": "[ERROR] Service hitting rate limit on database - retry storm detected",
        "step_2_fix": "Add exponential backoff to retry logic",
        "step_2_error_after_fix": "[ERROR] Circuit breaker OPEN - service returning 503 even though DB is recovering",
        "step_3_fix": "Reset circuit breaker after recovery period or on successful request",
        "expected_steps": 3,
        "test_cases": [
            {"step": 1, "expected": "pool size increased"},
            {"step": 2, "expected": "backoff implemented"},
            {"step": 3, "expected": "circuit breaker reset logic"}
        ]
    },
    {
        "task_id": "incident-debug-hard-002",
        "title": "Silent Integer Overflow Bug (3-Day Old)",
        "difficulty": "hard",
        "task_type": "debug",
        "domain": "incident_debug",
        "description": "Discovered 3 days after deploy: 0.1% of records have wrong calculations. No errors in logs. Root cause: integer overflow on large user IDs + 32-bit assumption.",
        "code_context": "# BUG: Uses 32-bit int, overflows on large IDs\n# Python 2 behavior or legacy type assumption\n\ndef calculate_user_hash(user_id):\n    # user_id > 2^31 causes overflow in 32-bit int\n    hash_result = (user_id * 31 + 17) % (2**31)  # Keeps only 32 bits\n    return hash_result\n\n# For user_id = 2.5 billion: overflows, returns wrong value\n# Silent corruption: no exception, just wrong results",
        "incident": {
            "incident_report": "Discovered: 0.1% of records have wrong calculated values (detected in audit 3 days later)",
            "error_logs": "No errors logged - silent data corruption",
            "metrics": {"affected_records": 1000, "total_records": 1000000, "discovery_lag": "72 hours"}
        },
        "step_1_hint": "Fix integer overflow: use 64-bit ints or Python's arbitrary precision",
        "step_2_hint": "Write migration to recalculate affected records",
        "expected_steps": 2,
        "test_cases": [
            {"step": 1, "input": "large_user_id", "assertions": ["no overflow", "correct calculation"]},
            {"step": 2, "input": "migration", "assertions": ["recalculate", "fix corrupted"]}
        ]
    },
    {
        "task_id": "incident-debug-hard-003",
        "title": "Leaking Secrets in Error Messages",
        "difficulty": "hard",
        "task_type": "debug",
        "domain": "incident_debug",
        "description": "Security incident: database credentials leaked in error messages logged to stdout. Multi-step: sanitize errors, rotate credentials, audit logs.",
        "code_context": "# BUG: Error messages include connection string with password\ntry:\n    conn = db.connect(f'postgres://user:password123@db.internal:5432/prod')\nexcept Exception as e:\n    logger.error(f'Connection failed: {e}')  # Logs full connection string with password\n    raise",
        "incident": {
            "incident_report": "Security audit found: database credentials leaked in container logs",
            "error_logs": "Connection failed: postgres://user:SecretPassword123@internal-db.vpc:5432/prod\n(visible in ECR logs, CloudWatch, any log aggregation)",
            "metrics": {"secrets_exposed": 5, "exposure_duration": "3 months", "affected_systems": "prod database"}
        },
        "step_1_hint": "Sanitize error messages - don't log sensitive connection strings",
        "step_2_hint": "Rotate exposed credentials immediately",
        "step_3_hint": "Audit all log systems for past exposures",
        "expected_steps": 3,
        "test_cases": [
            {"step": 1, "expected": "password removed from logs or masked"},
            {"step": 2, "expected": "credentials rotated"},
            {"step": 3, "expected": "audit logs checked"}
        ]
    }
]

# ============================================================================
# TASK SELECTION AND UTILITIES
# ============================================================================

def get_all_tasks():
    """Get all 18 tasks (6 solve, 6 review, 6 debug)"""
    return SOLVE_TASKS + REVIEW_TASKS + DEBUG_TASKS

def get_task_by_id(task_id: str) -> Dict[str, Any]:
    """Get a specific task by ID"""
    all_tasks = get_all_tasks()
    for task in all_tasks:
        if task['task_id'] == task_id:
            return task.copy()
    raise ValueError(f"Task not found: {task_id}")

def get_tasks_by_type_and_difficulty(task_type: str, difficulty: str) -> List[Dict[str, Any]]:
    """Get tasks filtered by type and difficulty"""
    if task_type == "solve":
        tasks = SOLVE_TASKS
    elif task_type == "review":
        tasks = REVIEW_TASKS
    elif task_type == "debug":
        tasks = DEBUG_TASKS
    else:
        raise ValueError(f"Invalid task_type: {task_type}")
    
    filtered = [t for t in tasks if t['difficulty'] == difficulty]
    return [t.copy() for t in filtered]

def select_random_task(task_type: str = None, difficulty: str = None) -> Dict[str, Any]:
    """Select a random task, optionally filtered"""
    all_tasks = get_all_tasks()
    
    if task_type:
        all_tasks = [t for t in all_tasks if t['task_type'] == task_type]
    if difficulty:
        all_tasks = [t for t in all_tasks if t['difficulty'] == difficulty]
    
    if not all_tasks:
        raise ValueError("No tasks match filters")
    
    return random.choice(all_tasks).copy()


# ============================================================================
# COMPATIBILITY ALIASES FOR LEGACY CODE
# ============================================================================

# Legacy names (map v3.0 tasks to old naming conventions)
CANONICAL_PROBLEMS = SOLVE_TASKS
BUGGY_PROBLEMS = REVIEW_TASKS

def get_random_canonical_problem(difficulty: str = None) -> Dict[str, Any]:
    """Get a random problem from SOLVE_TASKS (legacy name)"""
    try:
        tasks = [t for t in SOLVE_TASKS if not difficulty or t['difficulty'] == difficulty]
        if not tasks:
            tasks = SOLVE_TASKS
        return random.choice(tasks).copy()
    except:
        return None

def get_canonical_problem(problem_id: str) -> Dict[str, Any]:
    """Get a specific canonical problem by ID"""
    try:
        return get_task_by_id(problem_id)
    except:
        return None

def get_problem_by_id(problem_id: str) -> Dict[str, Any]:
    """Get a problem by ID (legacy name, alias for get_task_by_id)"""
    return get_task_by_id(problem_id)

def get_random_buggy_problem(difficulty: str = None) -> Dict[str, Any]:
    """Get a random problem from REVIEW_TASKS (legacy name)"""
    try:
        tasks = [t for t in REVIEW_TASKS if not difficulty or t['difficulty'] == difficulty]
        if not tasks:
            tasks = REVIEW_TASKS
        return random.choice(tasks).copy()
    except:
        return None

def get_problems_by_difficulty(difficulty: str) -> List[Dict[str, Any]]:
    """Get all problems of a specific difficulty (legacy compatibility)"""
    return [t for t in get_all_tasks() if t['difficulty'] == difficulty]

def get_buggy_problems_by_difficulty(difficulty: str) -> List[Dict[str, Any]]:
    """Get buggy problems (review tasks) by difficulty (legacy compatibility)"""
    return [t for t in REVIEW_TASKS if t['difficulty'] == difficulty]


# ============================================================================
# DOMAIN-AWARE PROBLEM SELECTION (v3.0)
# ============================================================================

def get_random_problem_by_domain(domain: str, difficulty: str = None, mode: str = "solve") -> Dict[str, Any]:
    """Get a random problem from the specified domain
    
    Args:
        domain: "data_pipeline", "code_review", or "incident_debug"
        difficulty: Filter by difficulty (easy/medium/hard)
        mode: "solve" or "review" (only applies to data_pipeline)
    
    Returns:
        A random task from the domain, or None if not found
    """
    try:
        if domain == "data_pipeline":
            # For data_pipeline, use solve/review modes
            if mode == "review":
                tasks = [t for t in REVIEW_TASKS if not difficulty or t['difficulty'] == difficulty]
            else:  # solve
                tasks = [t for t in SOLVE_TASKS if not difficulty or t['difficulty'] == difficulty]
        elif domain == "code_review":
            tasks = [t for t in CODE_REVIEW_TASKS if not difficulty or t['difficulty'] == difficulty]
        elif domain == "incident_debug":
            tasks = [t for t in INCIDENT_DEBUG_TASKS if not difficulty or t['difficulty'] == difficulty]
        else:
            return None
        
        if not tasks:
            # Fallback: try without difficulty filter
            if domain == "data_pipeline":
                tasks = REVIEW_TASKS if mode == "review" else SOLVE_TASKS
            elif domain == "code_review":
                tasks = CODE_REVIEW_TASKS
            elif domain == "incident_debug":
                tasks = INCIDENT_DEBUG_TASKS
        
        if tasks:
            problem = random.choice(tasks).copy()
            # Normalize: ensure both task_id and problem_id exist
            if "task_id" in problem and "problem_id" not in problem:
                problem["problem_id"] = problem["task_id"]
            if "problem_id" in problem and "task_id" not in problem:
                problem["task_id"] = problem["problem_id"]
            # Ensure task_type exists
            if "task_type" not in problem:
                problem["task_type"] = "solve"
            return problem
        return None
    except Exception as e:
        return None


# ============================================================================
# PROCEDURAL PROBLEM GENERATOR (Placeholder)
# ============================================================================

class ProceduralProblemGenerator:
    """Generate synthetic problems procedurally (legacy placeholder)
    
    This is a compatibility class for legacy code. Returns fixed canonical
    problems instead of truly procedural generation.
    """
    
    def __init__(self, seed: int = None):
        """Initialize generator with optional seed"""
        self.seed = seed
        if seed is not None:
            random.seed(seed)
    
    def generate(self, problem_type: str, difficulty: str) -> Dict[str, Any]:
        """Generate a problem of given type and difficulty
        
        Maps to canonical tasks since v3.0 uses fixed task definitions.
        """
        # Map legacy types to v3.0 task types
        task_type_map = {
            "two_sum": "solve",
            "palindrome": "solve",
            "sorting": "solve",
        }
        
        task_type = task_type_map.get(problem_type, "solve")
        
        # Get appropriate task
        if task_type == "solve":
            tasks = [t for t in SOLVE_TASKS if t['difficulty'] == difficulty]
        else:
            tasks = [t for t in SOLVE_TASKS if t['difficulty'] == difficulty]
        
        if not tasks:
            # Fallback to any difficulty if none match
            tasks = [t for t in SOLVE_TASKS if t.get('title', '').lower().find(problem_type) >= 0]
        
        if not tasks:
            tasks = SOLVE_TASKS
        
        return random.choice(tasks).copy()


