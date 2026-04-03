"""Server-Sent Events and WebSocket streaming helpers"""

import json
import logging
from typing import AsyncGenerator, Dict, Any

logger = logging.getLogger(__name__)


async def stream_test_results_sse(
    test_results: list[Dict[str, Any]],
    total_cases: int
) -> AsyncGenerator[str, None]:
    """
    Generate Server-Sent Events for streaming test results.
    
    Args:
        test_results: List of test case results
        total_cases: Total number of test cases
        
    Yields:
        SSE-formatted strings
    """
    # Event 1: Start message
    start_event = {
        "type": "start",
        "total_cases": total_cases
    }
    yield f"data: {json.dumps(start_event)}\n\n"

    # Events 2..N+1: Individual test results
    for result in test_results:
        event = {
            "type": "test_result",
            "case_index": result.get("case_index"),
            "passed": result.get("passed"),
            "error": result.get("error"),
            "time_ms": result.get("time_ms")
        }
        yield f"data: {json.dumps(event)}\n\n"


async def format_sse_event(data: Dict[str, Any]) -> str:
    """
    Format a dictionary as a Server-Sent Event.
    
    Args:
        data: Dictionary to send
        
    Returns:
        SSE-formatted string
    """
    return f"data: {json.dumps(data)}\n\n"


async def stream_step_response_sse(
    test_results: list[Dict[str, Any]],
    observation: Dict[str, Any],
    reward: float,
    terminated: bool,
    truncated: bool,
    info: Dict[str, Any]
) -> AsyncGenerator[str, None]:
    """
    Stream everything incrementally: tests, then final response.
    
    Args:
        test_results: List of test case results
        observation: Problem observation
        reward: Computed reward
        terminated: Whether episode is terminated
        truncated: Whether episode is truncated
        info: Additional info dict
        
    Yields:
        SSE-formatted strings
    """
    total_cases = len(test_results) if test_results else 0

    # 1. Start event
    yield await format_sse_event({
        "type": "start",
        "total_cases": total_cases
    })

    # 2. Individual test results as they arrive
    for result in test_results:
        yield await format_sse_event({
            "type": "test_result",
            "case_index": result.get("case_index"),
            "passed": result.get("passed"),
            "error": result.get("error"),
            "time_ms": result.get("time_ms")
        })

    # 3. Final complete response
    complete_event = {
        "type": "complete",
        "observation": observation,
        "reward": reward,
        "terminated": terminated,
        "truncated": truncated,
        "info": info
    }
    yield await format_sse_event(complete_event)


class WebSocketMessageBuilder:
    """Helper to build WebSocket messages in a consistent format"""

    @staticmethod
    def test_result_event(case_index: int, passed: bool, error: str = None, time_ms: float = None) -> Dict[str, Any]:
        """Build a test result message"""
        return {
            "type": "test_result",
            "case_index": case_index,
            "passed": passed,
            "error": error,
            "time_ms": time_ms
        }

    @staticmethod
    def step_response_event(
        session_id: str,
        observation: Dict[str, Any],
        reward: float,
        terminated: bool,
        truncated: bool,
        info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build a complete step response message"""
        return {
            "type": "step_response",
            "session_id": session_id,
            "observation": observation,
            "reward": reward,
            "terminated": terminated,
            "truncated": truncated,
            "info": info
        }

    @staticmethod
    def error_event(error_type: str, error_message: str) -> Dict[str, Any]:
        """Build an error message"""
        return {
            "type": "error",
            "error_type": error_type,
            "error_message": error_message
        }

    @staticmethod
    def reset_response_event(
        session_id: str,
        observation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build a reset response message"""
        return {
            "type": "reset_response",
            "session_id": session_id,
            "observation": observation
        }
