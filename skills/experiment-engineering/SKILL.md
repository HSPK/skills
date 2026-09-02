---
name: experiment-engineering
description: >-
  Use for ML/RL experiment systems, architecture changes, rollout or training
  debugging, performance studies, and remote job recovery. Encodes rules the
  user repeatedly reinforces in sessions: inspect real code, preserve experiment
  truth, design by ownership, validate completely, and operate until healthy.
  Not for model or hyperparameter recommendations, general application
  development, or platform-specific command syntax.
---

# Experiment Engineering

This skill combines instructions repeatedly reinforced across the user's
experiment, refactor, debugging, and job-operation sessions with established
engineering best practices.

Repository rules and stricter platform-specific safety requirements override
this skill's defaults.

## What this is for

Use this skill for distributed ML/RL system design, experiment implementation,
Rollout and training diagnosis, controlled performance comparisons, validation,
and end-to-end remote experiment operation.

Do not use it as a substitute for:

- repository-specific architecture and coding instructions;
- the official harness, paper, or benchmark specification;
- platform-specific skills for Azure Jobs, amlt, Kubernetes, or another CLI;
- scientific advice about which model, loss, or hyperparameter is intrinsically
  better.

Use this order:

1. Repeated user instructions define priorities and non-negotiable intent.
2. Repository rules define project-specific implementation.
3. Engineering best practices fill gaps and improve correctness, reliability,
   security, maintainability, and testability.

Do not use a best practice as an excuse for unrelated refactoring,
overengineering, or changing requested behavior.

## Operating mode

| Mode | Required behavior |
| --- | --- |
| Read-only | Inspect and report; never change files or remote state. |
| Implement | Make only requested local changes and validate offline. |
| Operate | Submit, monitor, diagnose, repair, and recover the requested run. |

Never cross modes implicitly.

## Read the real system and keep scope exact

- Read the actual code, config, working tree, diffs, and runtime evidence before
  proposing a design or change.
- Use documentation as an entry point, not as proof. Report stale docs,
  implementation deviations, hidden assumptions, and unfinished behavior.
- For architecture analysis, trace the data path, control path, process
  topology, transport, state owner, and failure propagation.
- Cite exact files, symbols, and line ranges when evidence is requested.
- Separate verified facts, measurements, inference, and recommendations.
- Modify only the requested scope. Do not fix unrelated issues.
- Continue through exact verification; working-looking code is not completion.

## System development philosophy

- Design for the stated large-scale target, not a toy file layout and not an
  imagined unlimited future.
- Do not constrain file, class, or module counts. Split by responsibility,
  ownership, lifecycle, protocol boundary, and failure domain.
- Keep Agent, Rollout, Trainer, and other replaceable systems independent.
  Connect them through narrow typed contracts.
- Give every task identity, queue, process, connection, asynchronous task,
  checkpoint, and mutable protocol state one clear owner.
- The owner that starts a resource owns cancellation, draining, cleanup,
  awaiting, and failure reporting.
- Make dependencies directional. Put code in a shared package only when it is
  genuinely shared.
- Keep APIs and watched state minimal. Remove redundant aliases, snapshots,
  compatibility layers, identity checks, and mirrored state.
- Use one domain vocabulary across architecture, APIs, logs, and documentation.
- Represent distributed coordination with explicit typed state machines.
  Multi-phase operations fail closed and clean up partial state.
- Publish coherent protocol state atomically, use bounded waits, and propagate
  peer failures.
- Create and name asynchronous tasks at the lifecycle site that cancels and
  awaits them.
- Inject narrow values, `*_fn` functions, and `on_*` callbacks instead of
  passing an owner object with hidden state.
- Borrow mechanisms from reference implementations, not their architecture.
  Adapt ownership, invariants, protocols, and failure semantics.
- Add abstraction only for a concrete current responsibility.

## Experiment development philosophy

- Improve the model and system, not the appearance of reward or dashboards.
- Treat official harnesses, verifiers, datasets, prompts, limits, and paper
  settings as fixed experiment semantics.
- Pin and reuse official implementations where practical; do not recreate
  behavior from memory.
- Never tune harness workflow around model failure merely to improve reward,
  merge success, or evaluation numbers.
- Treat the harness as a black box: fix implementation bugs, not model behavior.
- Analyze Rollout cases and infrastructure before discussing or changing the
  algorithm.
- Model failures are normally training signal; infrastructure failures follow
  explicit retry, recovery, or discard policies.
- In comparisons, change one variable and hold seeds, task order, prompts,
  checkpoint, harness, topology, and measurement window fixed.
- Persist the exact code revision, resolved config, environment identity,
  topology, task identity, and output location.
- Start with fixed representative cases before paying for a complete run.
- Never present an estimate as a measured result.

## Evidence-first debugging

- Metrics locate symptoms; complete cases explain them.
- Find the earliest abnormal Rollout and trace the first violated invariant.
- For training degradation, first look for false positives that received
  positive reward or entered training.
- Verify that a representative case is common before changing code.
- Track why trajectories are accepted, rejected, stale, retried, or discarded,
  together with latency, length, and contribution distributions.
- Check whether filtering, scheduling, retry, or normalization creates
  systematic selection or gradient bias.
- Fix the root cause, rerun the same case, then test a broader sample.

## Validation, performance, and observability

Use this ladder:

`targeted tests -> CPU mocks -> real-process tests -> component smoke -> minimal remote smoke -> full-scale run`

- Do not claim GPU, multi-node, recovery, or performance validation from mocks.
- Preserve existing defaults; make costly or risky new behavior opt-in.
- Measure before changing concurrency, workers, nodes, batch size, or queue
  capacity.
- Distinguish insufficient parallelism from engine idleness, CPU, storage,
  network, serialization, RPC fanout, and backpressure.
- Measure throughput, utilization, queue depth, latency, completion rate,
  retries, and stage timing over a stable window.
- Count control-plane and data-plane calls at the intended scale.
- Simulate scaling hypotheses, then perform a real controlled test.
- Prefer the simplest reliable control until measurements justify a dynamic
  policy.
- Keep instrumentation low overhead; avoid high-frequency logs that slow
  training.

## Code and documentation

- Write code that a new contributor can understand.
- Inline simple private logic and prefer functional composition when mutable
  object identity is unnecessary.
- Give every production function and method a concise behavioral docstring.
- Split functions or methods of 80 lines or more into responsibility blocks
  with short intent comments.
- Comments explain intent and invariants, not the next line.
- Avoid broad catches, silent fallbacks, and defensive branches for impossible
  states.
- Keep architecture and usage docs aligned with code. Explain what files to
  read, in what order, and what each component owns.
- Distinguish pure refactoring from behavior changes.
- Use `uv` for Python when the repository has not selected another tool.
- Keep engineering artifacts in English unless the repository says otherwise;
  use concise Chinese for user discussion when established.
- Organize commits by semantic reason and explain why the change exists.

## Remote operations and data

- An explicitly requested end-to-end run authorizes monitoring and repaired
  recovery submissions without repeated confirmation, subject to stricter
  platform rules.
- Diagnose the root cause and validate offline before recovery; never retry
  blindly.
- Never request more than eight Pods per submission unless explicitly changed.
- Read-only mode forbids cancellation, deletion, and resubmission.
- Do not repeat a mutation whose outcome is ambiguous.
- Treat capacity-only Pending as scheduling, not a reason to rewrite the run.
- In explicit debug mode, keep failed Pods alive when practical to avoid
  repeated setup.
- Report meaningful state changes and stop monitoring when the requested goal
  or terminal result is reached.
- Analyze data on local or compute-local storage. Copy only required artifacts
  from remote or Blob storage.
- Keep temporary artifacts in the project's designated temporary directory.
- Preserve private credentials, redact operational output, and never publish
  private code, logs, data, or secrets.

## Execution sequence

`inspect -> frame -> design -> implement -> validate -> operate -> conclude`

At conclusion, compare with the predefined baseline and report evidence,
uncertainty, regressions, and resource cost.

## Failure patterns learned repeatedly

- Reading only documentation and missing the real implementation.
- Changing code outside the requested scope.
- Treating an aggregate metric as the explanation.
- Generalizing from one exceptional Rollout case.
- Tuning the harness to hide model failure.
- Changing the algorithm before checking Rollout and infrastructure.
- Hiding ownership, asynchronous task creation, cleanup, or failure propagation.
- Building a central object that owns unrelated lifecycles.
- Enforcing a toy file-count rule on a large system.
- Copying reference code without adapting its assumptions.
- Scaling resources before measuring the bottleneck.
- Launching a full run before a minimal smoke test.
- Retrying a remote failure without a diagnosed and validated fix.
- Logging high-frequency details until observability slows training.
- Processing a complete remote experiment through a slow mounted filesystem.
- Claiming success without verifying the exact requested outcome.
