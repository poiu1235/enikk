"""Hermes agent runner for Enikk — main session + post-review."""
import agent.trajectory as _trajectory
import logging
import os
import run_agent as hermes_agent
import tools.memory_tool
from datetime import datetime
from pathlib import Path

from .hermes_tools import register_tools
from .prompts import AGENT_SYSTEM_PROMPT, REVIEW_SYSTEM_PROMPT


def run_agent(prompt: str, server_url: str, model: str, base_url: str, api_key: str):
    """Run a full Enikk agent session with trajectory export and post-review."""
    logging.getLogger().setLevel(logging.CRITICAL)

    os.environ["HERMES_HOME"] = "."

    register_tools(server_url)

    agent = hermes_agent.AIAgent(
        base_url=base_url,
        api_key=api_key,
        model=model,
        enabled_toolsets=["enikk", "memory", "todo"],
        quiet_mode=False,
        save_trajectories=False,
        max_iterations=200,
    )

    _init_memory(agent)

    result = agent.run_conversation(prompt, system_message=AGENT_SYSTEM_PROMPT)
    response = result.get("final_response", "")
    #print(response)

    _save_trajectory(agent, result, prompt)
    _review_session(agent, result, base_url, api_key, model, REVIEW_SYSTEM_PROMPT)


def _init_memory(agent):
    agent._memory_store = tools.memory_tool.MemoryStore(
        memory_char_limit=200000, user_char_limit=100000
    )
    agent._memory_store.load_from_disk()
    agent._memory_enabled = True
    agent._user_profile_enabled = False


def _save_trajectory(agent, result, prompt):
    try:
        traj_dir = Path("trajectories")
        traj_dir.mkdir(parents=True, exist_ok=True)
        traj_file = traj_dir / f"enikk_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jsonl"
        messages = result.get("messages", [])
        trajectory = agent._convert_to_trajectory_format(messages, prompt, True)
        _trajectory.save_trajectory(trajectory, agent.model, True, filename=str(traj_file))
        print(f"[trajectory] Saved to {traj_file}")
    except Exception as e:
        print(f"[warn] Failed to save trajectory: {e}")


def _review_session(agent, result, base_url, api_key, model, review_system_prompt):
    try:
        messages = result.get("messages", [])
        review_messages = [m for m in messages if m.get("role") in ("user", "assistant")]
        review_user_msg = "Review this session and save lessons to memory:\n" + "\n".join(
            f"[{m['role']}] {m['content'][:200]}" for m in review_messages[-20:]
        )
        print("\n--- Reviewing session ---")
        review_agent = hermes_agent.AIAgent(
            base_url=base_url,
            api_key=api_key,
            model=model,
            enabled_toolsets=["memory"],
            quiet_mode=True,
            save_trajectories=False,
            max_iterations=8,
        )
        review_agent._memory_store = agent._memory_store
        review_agent._memory_enabled = True
        review_agent._user_profile_enabled = False
        review_result = review_agent.run_conversation(review_user_msg, system_message=review_system_prompt)
        review_text = review_result.get("final_response", "")
        if review_text:
            print(review_text)
    except Exception as e:
        print(f"[warn] Session review failed (non-fatal): {e}")
