"""
APEX Code Solver - HuggingFace Spaces Gradio Interface

Run with: python app_gradio.py
"""

import asyncio
import json
import logging
from datetime import datetime

import gradio as gr
from envs.code_solver_env.server.code_solver_environment import CodeSolverEnvironment

logger = logging.getLogger(__name__)

# Global environment
env = CodeSolverEnvironment()

# Current session tracking
current_session = {"id": None, "problem": None, "history": []}


async def reset_environment(difficulty):
    """Reset environment to get new problem"""
    session_id, observation = await env.reset(
        difficulty=difficulty or None,
        mode="mixed"
    )
    current_session["id"] = session_id
    current_session["problem"] = observation
    current_session["history"] = []

    obs = observation
    return (
        f"# {obs.title}\n\n**Problem ID:** {obs.problem_id}\n\n"
        f"**Difficulty:** {obs.difficulty}\n\n"
        f"**Description:**\n{obs.description}\n\n"
        f"**Function Signature:**\n```python\n{obs.function_signature}\n```\n\n"
        f"**Examples:**\n{obs.examples}\n\n"
        f"**Constraints:**\n{obs.constraints}"
    )


async def submit_code(code_text):
    """Submit code and get results"""
    if not current_session["id"]:
        return "Error: No active session. Click 'Load New Problem' first.", ""

    try:
        observation, reward, terminated, truncated, info = await env.step(
            session_id=current_session["id"],
            code=code_text
        )

        # Update history
        current_session["history"].append({
            "reward": reward,
            "passed": observation.passed_cases,
            "total": observation.total_cases,
            "code": code_text
        })

        # Build results display
        results = []
        if observation.test_results:
            for i, result in enumerate(observation.test_results):
                status = "✅ PASS" if result.passed else "❌ FAIL"
                results.append(f"{status} Test {result.case_index + 1}")
                if result.error:
                    results.append(f"  Error: {result.error}")

        result_text = "\n".join(results) if results else "No tests run"

        # Build summary
        summary = (
            f"**Reward:** {reward:.3f}\n\n"
            f"**Tests Passed:** {observation.passed_cases}/{observation.total_cases}\n\n"
            f"**Step:** {observation.step_count}/{observation.max_steps}\n\n"
            f"**Status:** {('✅ SOLVED!' if terminated else ('🔄 CONTINUE' if not truncated else '⏹ TRUNCATED'))}\n\n"
            f"**Test Details:**\n{result_text}"
        )

        if observation.error_message:
            summary += f"\n\n**Error:** {observation.error_message}"

        return summary, result_text

    except Exception as e:
        return f"Error submitting code: {str(e)}", ""


def get_leaderboard():
    """Get leaderboard scores"""
    leaderboard_data = env.session_manager.get_leaderboard()

    if not leaderboard_data:
        return "No scores yet. Start solving problems to appear on the leaderboard!"

    scores_text = "| Rank | Score | Session |\n|------|-------|----------|\n"
    for i, entry in enumerate(leaderboard_data[:10], 1):
        scores_text += (
            f"| {i} | {entry['reward']:.3f} | "
            f"{entry['session_id'][:8]}... |\n"
        )

    return scores_text


async def get_problems_list():
    """Get list of available problems"""
    from envs.code_solver_env.server.problems import SOLVE_TASKS, REVIEW_TASKS, DEBUG_TASKS

    problems_text = ""
    
    for task_type, tasks, emoji in [
        ("SOLVE", SOLVE_TASKS, "💻"),
        ("REVIEW", REVIEW_TASKS, "🔍"),
        ("DEBUG", DEBUG_TASKS, "🐛"),
    ]:
        problems_text += f"\n#### {emoji} {task_type} Tasks ({len(tasks)} tasks)\n\n"
        problems_text += "| ID | Title | Difficulty | Cases |\n"
        problems_text += "|----:|-------|-----------|-------|\n"
        
        for p in tasks:
            problems_text += (
                f"| {p['task_id']} | {p['title']} | "
                f"{p['difficulty']} | {len(p['test_cases'])} |\n"
            )

    return problems_text


# Create Gradio interface
with gr.Blocks(title="APEX Data Pipeline Engineer") as demo:
    gr.Markdown("""
    # 🤖 APEX Data Pipeline Engineer
    
    An RL environment for training agents to **solve real-world data pipeline engineering tasks** using pandas, CSV, JSON, and ETL workflows.
    
    **Task Modes:**
    - 💻 **SOLVE**: Write pipeline code from scratch (9 tasks)
    - 🔍 **REVIEW**: Identify and fix bugs in data transformations (9 tasks)  
    - 🐛 **DEBUG**: Fix crashing pipelines step-by-step (9 tasks)
    """)

    with gr.Tabs():
        # ====== TAB 1: Try It ======
        with gr.Tab("Try It"):
            gr.Markdown("### Solve a Data Pipeline Task")

            with gr.Row():
                difficulty_select = gr.Dropdown(
                    choices=["easy", "medium", "hard", "any"],
                    value="easy",
                    label="Difficulty"
                )
                load_btn = gr.Button("Load New Problem", scale=1)

            problem_display = gr.Markdown("")

            with gr.Row():
                code_input = gr.Code(
                    language="python",
                    label="Your Solution",
                    lines=15
                )

            submit_btn = gr.Button("Submit Code")

            with gr.Row():
                results_display = gr.Markdown("")
                tests_display = gr.Markdown("")

            # Connect buttons
            load_btn.click(
                reset_environment,
                inputs=[difficulty_select],
                outputs=[problem_display]
            )

            submit_btn.click(
                submit_code,
                inputs=[code_input],
                outputs=[results_display, tests_display]
            )

        # ====== TAB 2: API Docs ======
        with gr.Tab("API Docs"):
            gr.Markdown("""
            ### REST & WebSocket APIs
            
            This environment provides REST and WebSocket endpoints for programmatic access:
            
            - **`POST /reset`** - Start a new episode
            - **`POST /step`** - Submit code and get reward  
            - **`GET /manifest`** - Discover environment capabilities
            - **`GET /health`** - Health check
            
            Full API documentation at the `/docs` endpoint when running locally.
            
            **Environment Details:**
            - 18 real-world data pipeline tasks
            - Deterministic rewards (0.0 to 1.0)
            - Sandboxed pandas code execution
            - Multi-session support with UUIDs
            """)

        # ====== TAB 3: Leaderboard ======
        with gr.Tab("Leaderboard"):
            leaderboard_display = gr.Markdown("")
            refresh_btn = gr.Button("Refresh")
            
            refresh_btn.click(
                get_leaderboard,
                outputs=[leaderboard_display]
            )
            
            # Load on start
            demo.load(get_leaderboard, outputs=[leaderboard_display])

        # ====== TAB 4: Tasks ======
        with gr.Tab("Tasks"):
            gr.Markdown("""
            ### Available Data Pipeline Tasks
            
            **18 Total Tasks** (6 per mode × 3 difficulties)
            """)
            problems_display = gr.Markdown("")
            refresh_btn2 = gr.Button("Refresh Tasks")
            
            refresh_btn2.click(
                get_problems_list,
                outputs=[problems_display]
            )
            
            # Load on start
            demo.load(get_problems_list, outputs=[problems_display])


if __name__ == "__main__":
    # Mount FastAPI app with Gradio UI running alongside it
    # This allows both REST endpoints (/reset, /step, /state) AND Gradio UI to work on same port
    from envs.code_solver_env.server.app import app as fastapi_app
    import uvicorn
    
    # Mount Gradio demo to FastAPI app at /ui
    app = gr.mount_gradio_app(fastapi_app, demo, path="/ui")
    
    # Run both FastAPI + Gradio on port 7860
    print("\n" + "=" * 80)
    print("APEX ENGINEERING BENCHMARK - FastAPI + Gradio Server")
    print("=" * 80)
    print("✅ FastAPI endpoints (for automated validator):")
    print("   - POST /reset    → Start new episode")
    print("   - POST /step     → Advance episode")
    print("   - GET  /state    → Get current observation")
    print()
    print("✅ Gradio UI: http://0.0.0.0:7860/ui")
    print("✅ API Docs: http://0.0.0.0:7860/docs")
    print("=" * 80 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=7860,
        log_level="info"
    )
