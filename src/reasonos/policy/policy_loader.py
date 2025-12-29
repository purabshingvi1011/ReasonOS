import json
import os
from typing import Dict, Any

def load_policy(path: str) -> Dict[str, Any]:
    """
    Loads a policy JSON file from the given path.
    
    Args:
        path: Path to the policy JSON file.
        
    Returns:
        The loaded policy as a dictionary.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
        ValueError: If the policy shape is invalid.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Policy file not found at: {path}")
        
    with open(path, 'r') as f:
        policy = json.load(f)
        
    validate_policy_shape(policy)
    return policy

def validate_policy_shape(policy: Dict[str, Any]) -> None:
    """
    Validates that the policy dictionary has the required structure.
    
    Args:
        policy: The policy dictionary to validate.
        
    Raises:
        ValueError: If required keys are missing.
    """
    required_keys = ["policy_version", "domain_defaults", "global_rules"]
    for key in required_keys:
        if key not in policy:
            raise ValueError(f"Policy missing required key: {key}")
            
    if "global_rules" in policy:
        global_rules = policy["global_rules"]
        required_global = ["block_if_confidence_below", "block_message", "allowed_domains"]
        for key in required_global:
            if key not in global_rules:
                raise ValueError(f"Policy global_rules missing required key: {key}")
