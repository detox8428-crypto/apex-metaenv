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
        ]
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
        ]
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
        ]
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
        ]
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
        ]
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
        ]
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
        ]
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
        ]
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
        ]
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
        ]
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
        ]
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
        ]
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
        ]
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
        ]
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
        ]
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
        ]
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


