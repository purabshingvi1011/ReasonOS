from typing import Any

def execute(step: dict[str, Any], context: dict[str, Any]) -> str:
    """
    Execute a step using the GPT stub.
    
    Behavior:
    - For S1 in research_verification (extract claim): returns paragraph unchanged.
    - Otherwise: returns a generic sentence.
    
    Args:
        step: The step dictionary.
        context: Execution context.
        
    Returns:
        The execution output string.
    """
    # Check if this is S1 in research verification (usually index 0)
    # Context usually contains 'inputs' with 'paragraph' for this task
    inputs = context.get("inputs", {})
    paragraph = inputs.get("paragraph")
    
    if step.get("step_index") == 0 and paragraph:
        return paragraph
        
    return "GPT stub generated this generic response."
