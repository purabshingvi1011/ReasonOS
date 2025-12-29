from typing import Any, Dict, Optional
import json
from pathlib import Path

from ..kernel import run_paper_verification_task, run_demo_task
from ..replay.replay_engine import replay_run

class ReasonOSClient:
    """
    Public Developer API for ReasonOS.
    
    Provides a stable interface for running reasoning tasks, replaying runs,
    and accessing ReasonOS capabilities without exposing internal kernel logic.
    """
    
    def __init__(
        self,
        policy_path: str = "policies/default_policy.json",
        memory_path: str | None = None,
        enable_replay: bool = False
    ):
        """
        Initialize the ReasonOS client.
        
        Args:
            policy_path: Path to the policy JSON file.
            memory_path: Optional path to persistent memory file.
            enable_replay: Whether to enable replay capabilities (currently unused in init, reserved for future config).
        """
        self.policy_path = policy_path
        self.memory_path = memory_path
        self.enable_replay = enable_replay

    def verify_research_claim(
        self,
        claim: str,
        document_path: str,
        domain: str = "research_verification"
    ) -> Dict[str, Any]:
        """
        Verify a research claim against a document.
        
        Args:
            claim: The claim text to verify.
            document_path: Path to the source document.
            domain: The domain of the task (default: "research_verification").
            
        Returns:
            A dictionary containing the full RSL (Reasoning System Log) run artifact.
        """
        if domain != "research_verification":
            raise ValueError(f"Unsupported domain for this method: {domain}")
            
        return run_paper_verification_task(
            paragraph=claim,
            document_path=document_path,
            memory_path=self.memory_path,
            policy_path=self.policy_path,
            enable_memory_writes=bool(self.memory_path)
        )

    def run_tool_reasoning(
        self,
        task_name: str,
        inputs: Dict[str, Any],
        domain: str = "tool_reasoning"
    ) -> Dict[str, Any]:
        """
        Run a tool-based reasoning task.
        
        Args:
            task_name: Name of the task (currently unused, maps to fixed demo task).
            inputs: Input parameters for the task.
            domain: The domain of the task (default: "tool_reasoning").
            
        Returns:
            A dictionary containing the full RSL run artifact.
        """
        if domain != "tool_reasoning":
            raise ValueError(f"Unsupported domain for this method: {domain}")
            
        # Note: run_demo_task currently hardcodes inputs in the kernel function signature or body.
        # Ideally, kernel.run_demo_task should accept inputs.
        # Looking at kernel.py, run_demo_task takes policy_path but hardcodes inputs inside.
        # To strictly follow "Refactor minimally", we will call it as is, 
        # but we should probably update kernel.py if we want to pass inputs.
        # However, the prompt says "run_tool_reasoning... Calls existing tool reasoning demo logic".
        # The existing logic is in run_demo_task.
        # Let's check kernel.py again.
        
        return run_demo_task(policy_path=self.policy_path)

    def replay_run(
        self,
        run_path: str
    ) -> Dict[str, Any]:
        """
        Replay a past run deterministically.
        
        Args:
            run_path: Path to the original run JSON file.
            
        Returns:
            A dictionary containing the replayed run artifact.
        """
        _, replayed_run = replay_run(run_path, save_to_disk=False)
        return replayed_run
