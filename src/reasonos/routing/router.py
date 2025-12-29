from typing import Any, Dict

def route_executor(policy: Dict[str, Any], domain: str, step: Dict[str, Any]) -> Dict[str, Any]:
    """
    Determine the executor for a step based on policy routing rules.
    
    Priority:
    1. Existing TOOL executor (preserved)
    2. Step-specific override (S1, S2, etc.)
    3. Domain-specific override
    4. Default model executor
    
    Args:
        policy: The loaded policy dictionary.
        domain: The task domain.
        step: The step dictionary.
        
    Returns:
        ExecutorSpec dictionary with type, name, and config.
    """
    current_executor = step.get("executor")
    
    # 1. If step is already a TOOL step (from build_step), preserve it
    # Note: build_step sets executor to a string like "tool" or "model".
    # We need to handle that.
    # If it's just a string "tool", we treat it as type="TOOL".
    
    if isinstance(current_executor, str):
        if current_executor.lower() == "tool":
            return {"type": "TOOL", "name": "tool_executor", "config": {}}
    elif isinstance(current_executor, dict):
        if current_executor.get("type") == "TOOL":
            return current_executor

    # Routing configuration
    routing = policy.get("routing", {})
    step_overrides = routing.get("step_overrides", {})
    domain_overrides = routing.get("domain_overrides", {})
    default_executor = routing.get("default_model_executor", "gpt_stub")
    
    # Determine logical step ID (e.g., S1, S2)
    # We assume S{index+1} mapping as established in Step 7
    step_index = step.get("step_index", 0)
    logical_id = f"S{step_index + 1}"
    
    executor_name = default_executor
    
    # 3. Domain override
    if domain in domain_overrides:
        executor_name = domain_overrides[domain]
        
    # 2. Step override (higher priority)
    if logical_id in step_overrides:
        executor_name = step_overrides[logical_id]
        
    return {
        "type": "MODEL",
        "name": executor_name,
        "config": {}
    }

def resolve_and_attach_executor(policy: Dict[str, Any], domain: str, step: Dict[str, Any]) -> None:
    """
    Resolve the executor for the step and attach the spec to the step.
    
    Mutates the step dictionary.
    
    Args:
        policy: The loaded policy dictionary.
        domain: The task domain.
        step: The step dictionary.
    """
    executor_spec = route_executor(policy, domain, step)
    step["executor"] = executor_spec
