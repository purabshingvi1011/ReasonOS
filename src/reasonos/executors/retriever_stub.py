from typing import Any
from ..evidence.sentence_retriever import retrieve_evidence

def execute(step: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """
    Execute a step using the Retriever stub.
    
    Behavior:
    - Retrieves evidence from document using existing logic.
    - Returns dict with retrieved_evidence and summary.
    
    Args:
        step: The step dictionary.
        context: Execution context (must contain inputs with paragraph and document_path/text).
        
    Returns:
        Dictionary containing retrieval results.
    """
    inputs = context.get("inputs", {})
    paragraph = inputs.get("paragraph")
    
    # Document text might be in inputs or we might need to read it
    # Ideally context has what we need. 
    # In run_paper_verification_task, we have document_text available.
    # We should pass it in context.
    document_text = context.get("document_text")
    
    if not paragraph or not document_text:
        return {
            "retrieved_evidence": [],
            "summary": "Retriever failed: missing paragraph or document text"
        }
        
    evidence_results = retrieve_evidence(paragraph, document_text, k=3)
    
    return {
        "retrieved_evidence": evidence_results,
        "summary": f"Retrieved {len(evidence_results)} evidence sentences"
    }
