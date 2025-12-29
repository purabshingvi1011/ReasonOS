import json
from pathlib import Path
from typing import Any, Dict, Tuple

from ..kernel import run_paper_verification_task
from ..utils.time import now_iso

def replay_run(original_run_path: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Replay a past run deterministically.
    
    Args:
        original_run_path: Path to the original run JSON file.
        
    Returns:
        Tuple containing (original_run_dict, replayed_run_dict).
        
    Raises:
        FileNotFoundError: If original run file doesn't exist.
        ValueError: If run type is not supported.
    """
    run_path = Path(original_run_path)
    if not run_path.exists():
        raise FileNotFoundError(f"Run file not found: {original_run_path}")
        
    with open(run_path, "r") as f:
        original_run = json.load(f)
        
    task = original_run.get("task", {})
    domain = task.get("domain")
    inputs = task.get("inputs", {})
    
    if domain != "research_verification":
        raise ValueError(f"Replay not supported for domain: {domain}")
        
    # Extract parameters
    paragraph = inputs.get("paragraph")
    document_path = inputs.get("document_path")
    
    # We assume the policy used was the default or we'd need to store policy path in run artifact.
    # For this step, we'll assume default_policy.json as per constraints.
    policy_path = "policies/default_policy.json"
    
    # Re-execute
    # Note: We need to modify kernel to accept enable_memory_writes and parent_run_id
    replayed_run = run_paper_verification_task(
        paragraph=paragraph,
        document_path=document_path,
        policy_path=policy_path,
        memory_path=None, # Disable memory loading/writing for replay to ensure isolation
        enable_memory_writes=False, # Explicit flag we will add to kernel
        parent_run_id=original_run["run"]["run_id"] # Link to original
    )
    
    # Save replay run
    timestamp = now_iso().replace(":", "").replace("-", "").split(".")[0]
    replay_filename = run_path.stem + f"_replay_{timestamp}.json"
    replay_path = run_path.parent / replay_filename
    
    with open(replay_path, "w") as f:
        json.dump(replayed_run, f, indent=2)
        
    return original_run, replayed_run
