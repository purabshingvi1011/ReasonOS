# ReasonOS Kernel Specification v0.1

## 1. Purpose

The ReasonOS Kernel is the minimal, non optional core that manages reasoning as a system.
It is responsible for turning model output into a structured, verifiable, persistent reasoning artifact.

The kernel does not replace language models.
It governs how models and tools are used to produce reasoning that can be inspected and trusted.

## 2. Kernel Non Goals

The kernel is not:
- a chat application
- a prompt library
- a vector database
- a model training system
- a UI framework
- an agent demo

The kernel must remain small and enforceable.

## 3. Core Objects Owned by the Kernel

The kernel owns and persists:
- Task
- Step
- Evidence
- Verification
- Policy
- MemoryItem
- Contradiction
- RunLog

These are represented using RSL or RSL derived structures.

## 4. Kernel Responsibilities

### 4.1 Task Intake
The kernel must accept a task input, normalize it, and create a Task object.

Minimum required inputs:
- objective: what is being asked
- context: optional background information
- sources: optional documents or tool connectors available

Outputs:
- Task ID
- Task state initialized to CREATED

### 4.2 Decomposition
The kernel must decompose the task into explicit reasoning steps.
The kernel may use an LLM to propose steps, but the kernel owns the final step structure.

Decomposition requirements:
- steps must be atomic
- steps must have explicit dependencies
- each step must define whether evidence is required

Output:
- Step list created
- Task state becomes DECOMPOSED

### 4.3 Step Scheduling
The kernel must schedule step execution.

Scheduling requirements:
- steps cannot execute until dependencies are satisfied
- steps must be assigned an executor type: model or tool
- the kernel must record scheduling decisions

Output:
- Step state becomes SCHEDULED

### 4.4 Evidence Binding
If a step requires evidence, the kernel must attach evidence candidates.
Evidence may come from:
- provided documents
- web search or internal tools
- memory store
- computations from tools

Evidence requirements:
- evidence must include source type and provenance
- evidence must include content snippet or tool output
- evidence must include relevance score

Output:
- evidence attached to step
- Step state becomes EVIDENCE_ATTACHED

### 4.5 Step Execution
The kernel must execute a step through its assigned executor.
Executors:
- Model executor: calls a model adapter
- Tool executor: calls a tool interface

Execution requirements:
- execution must be deterministic at the kernel level
- the kernel must record prompt template ID or tool name
- the kernel must store step output

Output:
- Step output stored
- Step state becomes EXECUTED

### 4.6 Verification
The kernel must verify each step output.
Verification determines if:
- output is supported by evidence
- output is contradicted by evidence
- output is speculative or weak
- output has missing assumptions

Verification requirements:
- verification must return a status
- verification must return a confidence score
- verification must return issues list
- verification must bind to the evidence used for judgement

Output:
- Verification object stored
- Step state becomes VERIFIED

### 4.7 Revision Control
If verification status is weak or contradicted, the kernel must decide whether to revise.
Revision actions include:
- request more evidence
- rerun step with constraints
- ask for alternative reasoning
- stop and surface uncertainty

Revision requirements:
- revision decisions must be policy driven
- every revision must be logged
- kernel must cap recursion and retries

Output:
- Step state may return to EVIDENCE_ATTACHED or EXECUTED
- or Step state becomes FAILED

### 4.8 Consistency Checking
The kernel must run a cross step consistency check.

Consistency targets:
- internal contradictions between steps
- contradictions with persistent memory
- contradictions with sources

Output:
- Contradiction objects stored
- Task state becomes CONSISTENCY_CHECKED

### 4.9 Finalization
The kernel must produce a final answer that references the verified reasoning graph.
The kernel must compute final confidence based on:
- step confidence aggregation
- number and severity of contradictions
- policy constraints

Output:
- FinalConclusion stored
- Task state becomes FINALIZED

## 5. Kernel State Machine

Task states:
- CREATED
- DECOMPOSED
- RUNNING
- CONSISTENCY_CHECKED
- FINALIZED
- FAILED

Step states:
- CREATED
- SCHEDULED
- EVIDENCE_ATTACHED
- EXECUTED
- VERIFIED
- FAILED

## 6. Policy Engine

Policies control:
- confidence thresholds
- allowed tools
- allowed models
- domain constraints
- retry limits
- escalation rules
- fail closed rules

Policy examples:
- If any step is contradicted, do not finalize without a revision attempt.
- If domain is medical, require evidence for every step.
- If final confidence below threshold, ask clarifying questions instead of answering.

## 7. Logging and Audit

Kernel must log:
- model calls
- prompts or prompt template IDs
- tool calls
- evidence sources
- verification outputs
- revisions
- contradictions
- finalization decisions

Logs must be:
- queryable
- exportable
- attachable to a final report

## 8. Invariants

The kernel must enforce the following invariants:
- Every step has an explicit status.
- Every verified step has evidence bindings when evidence is required.
- Every revision is logged.
- Final outputs reference a reasoning graph, not just free text.
- Uncertainty is surfaced when verification is weak.

## 9. Failure Modes

The kernel must anticipate:
- missing or low quality evidence
- contradictory sources
- model refusal or low quality responses
- tool failures
- runaway recursion in revisions

The safe default is to fail closed:
- present uncertainty
- request more evidence
- or stop the run
