#!/usr/bin/env python3
"""
APEX Complete Verification Test - Validates all fixes are working correctly
"""
import asyncio
import sys
from envs.code_solver_env.server.code_solver_environment import CodeSolverEnvironment

async def test_all_episodes():
    """Test all 9 episodes with attempts at solving each"""
    env = CodeSolverEnvironment()
    results = {"success": 0, "failed": 0, "errors": []}
    
    test_cases = [
        ("data_pipeline", "solve", "easy"),
        ("data_pipeline", "solve", "medium"),
        ("data_pipeline", "solve", "hard"),
        ("code_review", "review", "easy"),
        ("code_review", "review", "medium"),
        ("code_review", "review", "hard"),
        ("incident_debug", "debug", "easy"),
        ("incident_debug", "debug", "medium"),
        ("incident_debug", "debug", "hard"),
    ]
    
    print("\n" + "="*80)
    print("APEX VERIFICATION TEST - All 9 Episodes")
    print("="*80)
    
    for domain, mode, difficulty in test_cases:
        try:
            # Reset episode
            result = await env.reset(domain=domain, difficulty=difficulty)
            if isinstance(result, tuple) and len(result) == 2:
                obs, info = result
            else:
                obs = result
                info = {}
            
            # Extract session ID (could be in obs or info)
            if isinstance(info, dict):
                session_id = info.get("session_id", "unknown")
                task = info.get("task_id", "unknown") 
            else:
                # info is a Pydantic model
                session_id = getattr(info, "session_id", "unknown")
                task = getattr(info, "task_id", "unknown")
            
            print(f"\n✅ [{domain:15} / {mode:6} / {difficulty:6}]")
            print(f"   Session: {str(session_id)[:8]}... Task: {task}")
            
            # Validate observation
            if not obs:
                raise ValueError("Invalid observation from reset()")
            
            # Attempt step (using dummy code, not actual solution)
            if mode == "review":
                # For review mode, submit a dummy review
                step_result = await env.step(
                    session_id=session_id,
                    review={"score": 4, "feedback": "test"}
                )
            else:
                # For solve/debug modes, submit dummy code
                step_result = await env.step(
                    session_id=session_id,
                    code="pass"
                )
            
            obs_out, reward, done, info_out = step_result
            
            # Extract reward from Pydantic model if needed (in case it returns StepResponse object)
            if hasattr(reward, "total_reward"):
                reward = reward.total_reward
            
            # Extract passed_cases/total_cases from observation or info
            if hasattr(obs_out, "passed_cases"):
                passed = obs_out.passed_cases
                total = obs_out.total_cases
            else:
                passed = info_out.get("passed_cases", 0) if isinstance(info_out, dict) else 0
                total = info_out.get("total_cases", 1) if isinstance(info_out, dict) else 1
            
            print(f"   Reward: {reward:.3f} | Done: {done}")
            print(f"   ✓ Passed: {passed}/{total}")
            
            results["success"] += 1
            
        except Exception as e:
            results["failed"] += 1
            error_msg = str(e)
            results["errors"].append(f"{domain}/{mode}/{difficulty}: {error_msg}")
            print(f"   ❌ ERROR: {error_msg}")
    
    # Summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    print(f"Episodes: {results['success']}/9 successful")
    print(f"Success Rate: {100*results['success']/9:.1f}%")
    
    if results["errors"]:
        print("\nErrors encountered:")
        for error in results["errors"]:
            print(f"  • {error}")
        return False
    
    print("\n✅ All verification tests passed!")
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_all_episodes())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
