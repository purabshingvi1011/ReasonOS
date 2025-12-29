# ReasonOS Reasoning Specification Language (RSL) v0.1

## 1. Purpose

RSL is the canonical representation of reasoning inside ReasonOS.
It defines how tasks, steps, evidence, verification, contradictions, and outputs are stored, audited, replayed, and shared.

RSL is designed to be:
- model agnostic
- tool agnostic
- human readable
- machine enforceable
- serializable
- stable over time

RSL is not chain of thought text.
RSL is reasoning as data.

## 2. Design Goals

RSL must enable the following:
- explicit step decomposition and dependencies
- evidence binding per step
- verification status per step
- revision history and provenance
- cross step contradiction tracking
- replay and audit of a run
- persistence into memory

## 3. Non Goals

RSL is not:
- a UI format
- a prompt format
- an embedding format
- a database schema for every internal component

RSL is the portable contract, not the full internal implementation.

## 4. Core Entities

RSL defines these core entities:
- Task
- Run
- Step
- Evidence
- Verification
- Contradiction
- FinalConclusion
- MemoryWrite

## 5. Status Enums

### 5.1 Task Status
Allowed values:
- CREATED
- DECOMPOSED
- RUNNING
- CONSISTENCY_CHECKED
- FINALIZED
- FAILED

### 5.2 Step Status
Allowed values:
- CREATED
- SCHEDULED
- EVIDENCE_ATTACHED
- EXECUTED
- VERIFIED
- FAILED

### 5.3 Verification Status
Allowed values:
- SUPPORTED
- PARTIALLY_SUPPORTED
- WEAK
- CONTRADICTED
- UNKNOWN

## 6. Canonical RSL Schema v0.1

RSL v0.1 is a single JSON document per run.

### 6.1 Top Level Object

Fields:
- rsl_version
- task
- run
- steps
- contradictions
- final_conclusion
- memory_writes
- audit

### 6.2 Task Object

Required fields:
- task_id: string (uuid)
- objective: string
- domain: string
- created_at: string (ISO 8601)
- inputs: object

Optional fields:
- constraints: array of strings
- provided_sources: array of SourceRef

Task.inputs must include:
- user_input: string
- context: string or null

### 6.3 Run Object

Required fields:
- run_id: string (uuid)
- status: Task Status
- started_at: string
- ended_at: string or null
- model_policy: object
- tool_policy: object

Run.model_policy examples:
- allowed_models
- preferred_model
- fallback_models

Run.tool_policy examples:
- allowed_tools
- web_access_allowed

### 6.4 Step Object

Each step represents one atomic reasoning unit.

Required fields:
- step_id: string
- title: string
- description: string
- status: Step Status
- depends_on: array of step_ids
- executor: ExecutorSpec
- evidence_required: boolean
- evidence: array of Evidence
- execution: StepExecution
- verification: Verification
- revisions: array of RevisionRecord

Notes:
- depends_on may be empty
- evidence may be empty if evidence_required is false
- revisions may be empty in the first pass

### 6.5 ExecutorSpec

Required fields:
- type: string (MODEL or TOOL)
- name: string
- config: object

If type is MODEL:
- name is a model identifier like gpt, claude, gemini, local
- config includes parameters like temperature or max_tokens

If type is TOOL:
- name is tool identifier like web_search, calculator, sql_query
- config includes tool parameters

### 6.6 Evidence Object

Required fields:
- evidence_id: string
- source: SourceRef
- content: string
- relevance_score: number between 0 and 1
- extracted_at: string

Optional fields:
- span: object (start, end) if evidence references a document span
- tool_output: object if evidence came from a tool call

### 6.7 SourceRef

Required fields:
- source_type: string (DOCUMENT, TOOL, MEMORY, WEB)
- source_id: string
- uri: string or null

Examples:
- DOCUMENT with source_id set to a document hash or filename
- TOOL with source_id set to tool call id
- MEMORY with source_id set to memory key
- WEB with uri set to a URL

### 6.8 StepExecution

Required fields:
- input_summary: string
- output: string
- started_at: string
- ended_at: string
- prompt_ref: string or null
- tool_call_ref: string or null

Notes:
- prompt_ref is a template ID, not raw prompt text
- tool_call_ref is a tool call ID if a tool was used

### 6.9 Verification Object

Required fields:
- status: Verification Status
- confidence: number between 0 and 1
- issues: array of strings
- checked_evidence_ids: array of evidence_id
- verifier: VerifierSpec
- verified_at: string

### 6.10 VerifierSpec

Required fields:
- type: string (MODEL, RULE, HYBRID)
- name: string
- config: object

Examples:
- MODEL verifier uses a second model to judge support
- RULE verifier uses deterministic checks
- HYBRID uses both

### 6.11 RevisionRecord

Each revision captures one corrective attempt.

Required fields:
- revision_id: string
- reason: string
- action: string
- previous_verification_status: Verification Status
- new_execution_output: string or null
- new_verification: Verification or null
- revised_at: string

Action examples:
- FETCH_MORE_EVIDENCE
- REEXECUTE_STEP
- CHANGE_EXECUTOR
- ESCALATE_UNCERTAINTY

### 6.12 Contradiction Object

Required fields:
- contradiction_id: string
- step_ids: array of step_id
- description: string
- severity: string (LOW, MEDIUM, HIGH)
- detected_by: VerifierSpec
- detected_at: string

### 6.13 FinalConclusion Object

Required fields:
- content: string
- confidence: number between 0 and 1
- supported_step_ids: array of step_id
- unresolved_contradictions: array of contradiction_id
- finalized_at: string

### 6.14 MemoryWrite Object

Optional but recommended.

Required fields:
- memory_id: string
- type: string (FACT, CONSTRAINT, DECISION, CONTRADICTION)
- content: string
- confidence: number between 0 and 1
- derived_from_step_ids: array of step_id
- written_at: string

### 6.15 Audit Object

Required fields:
- kernel_version: string
- rsl_version: string
- logs: array of LogEvent

LogEvent required fields:
- event_id: string
- event_type: string
- timestamp: string
- payload: object

## 7. Full Example RSL Document

This example shows a minimal run with two steps.

{
  "rsl_version": "0.1",
  "task": {
    "task_id": "9b25f40b-4a9b-4bd3-8c5d-8d9c3a1d2c10",
    "objective": "Verify whether the paragraph's claim is supported by the provided document.",
    "domain": "research_verification",
    "created_at": "2025-12-29T10:00:00Z",
    "inputs": {
      "user_input": "Check this paragraph for correctness.",
      "context": null
    },
    "constraints": [],
    "provided_sources": [
      { "source_type": "DOCUMENT", "source_id": "paper.pdf", "uri": null }
    ]
  },
  "run": {
    "run_id": "b0d6f2d7-0d3d-4a8d-8d26-8a4a1f0c7e98",
    "status": "FINALIZED",
    "started_at": "2025-12-29T10:00:05Z",
    "ended_at": "2025-12-29T10:00:40Z",
    "model_policy": {
      "allowed_models": ["gpt", "claude", "gemini"],
      "preferred_model": "gpt",
      "fallback_models": ["claude"]
    },
    "tool_policy": {
      "allowed_tools": ["vector_search"],
      "web_access_allowed": false
    }
  },
  "steps": [
    {
      "step_id": "S1",
      "title": "Extract main claim",
      "description": "Identify the primary factual claim in the paragraph.",
      "status": "VERIFIED",
      "depends_on": [],
      "executor": { "type": "MODEL", "name": "gpt", "config": { "temperature": 0.2 } },
      "evidence_required": false,
      "evidence": [],
      "execution": {
        "input_summary": "Paragraph text",
        "output": "The paragraph claims X causes Y under condition Z.",
        "started_at": "2025-12-29T10:00:06Z",
        "ended_at": "2025-12-29T10:00:10Z",
        "prompt_ref": "decompose.extract_claim.v1",
        "tool_call_ref": null
      },
      "verification": {
        "status": "SUPPORTED",
        "confidence": 0.90,
        "issues": [],
        "checked_evidence_ids": [],
        "verifier": { "type": "RULE", "name": "schema_check", "config": {} },
        "verified_at": "2025-12-29T10:00:11Z"
      },
      "revisions": []
    },
    {
      "step_id": "S2",
      "title": "Bind evidence and verify claim",
      "description": "Find evidence in the document and judge support for the claim.",
      "status": "VERIFIED",
      "depends_on": ["S1"],
      "executor": { "type": "MODEL", "name": "gpt", "config": { "temperature": 0.2 } },
      "evidence_required": true,
      "evidence": [
        {
          "evidence_id": "E1",
          "source": { "source_type": "DOCUMENT", "source_id": "paper.pdf", "uri": null },
          "content": "In our experiments, X increased Y by 12 percent under condition Z.",
          "relevance_score": 0.87,
          "extracted_at": "2025-12-29T10:00:15Z"
        }
      ],
      "execution": {
        "input_summary": "Claim plus evidence snippets",
        "output": "The evidence supports the claim under condition Z but does not generalize beyond it.",
        "started_at": "2025-12-29T10:00:16Z",
        "ended_at": "2025-12-29T10:00:25Z",
        "prompt_ref": "verify.support_check.v1",
        "tool_call_ref": null
      },
      "verification": {
        "status": "PARTIALLY_SUPPORTED",
        "confidence": 0.78,
        "issues": ["Claim overgeneralizes beyond documented condition Z."],
        "checked_evidence_ids": ["E1"],
        "verifier": { "type": "MODEL", "name": "claude", "config": { "temperature": 0.0 } },
        "verified_at": "2025-12-29T10:00:28Z"
      },
      "revisions": []
    }
  ],
  "contradictions": [],
  "final_conclusion": {
    "content": "The paragraph is partially supported. The evidence supports the effect under condition Z, but the paragraph should narrow its scope.",
    "confidence": 0.80,
    "supported_step_ids": ["S1", "S2"],
    "unresolved_contradictions": [],
    "finalized_at": "2025-12-29T10:00:39Z"
  },
  "memory_writes": [],
  "audit": {
    "kernel_version": "0.1",
    "rsl_version": "0.1",
    "logs": []
  }
}

## 8. Validation Rules

The kernel must enforce:
- Every step has a status.
- If evidence_required is true, checked_evidence_ids must not be empty for SUPPORTED or PARTIALLY_SUPPORTED.
- confidence must be between 0 and 1.
- final_conclusion must list which steps support it.
- unresolved contradictions must be listed explicitly.
