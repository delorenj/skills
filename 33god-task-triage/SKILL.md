---
name: 33god-task-triage
description: Facilitates a single point of ingress for any and all tasks. Used when pulling a new `inbox` task from the 33god plane workspace, or any prompt that explicitly or implicitly describes a non-trivial task. Triggered by `add a feature`, `task.inbox.new` event.
---

# Task Triage Skill

There’s a large amount of friction when deciding:

- where a task should live
- how it fits into the overall system
- what dependencies are affected
- breaking the task into subtasks
- notifying the correct stakeholders

Handing this responsibility to a dedicated specialist promotes standardization, increases organizational potential, and decreases system entropy.

## What problem does this solve?

1. Lowers friction when going from idea to scoped plan.
2. Improves organization by handing responsibility to a single agent
3. Increases project velocity by reducing human cognitive load required to go from ‘idea’ to ‘scoped task’

## Workflow

1. Think deeply about the task and answer the following questions:
   1. Why is this task likely being proposed?
   2. How would the end result lead to an improvement in the relative system(s) affected?
   3. Given the current state of the implied dependencies, does this task make sense in terms of overall improvement?
   4. Are there any recent issues, bugs, or complications that would likely have been mitigated or avoided had this been implemented or in place at the time of incident?
2. Determine the task’s classification
   1. Are this task’s dependencies bound by a single component (i.e. add a view to Holocene) or does this task require cross-component changes (i.e. Implement a new command - requires Holyfields schema, Bloodbank changes, new consumer service, etc), or does it refer to a single repo project or mobile app (i.e. Overworld, ChoreScore, Wean, SVGMe, etc)
   2. Is the task a metatask that doesn’t directly live in a component or domain, but contributes to improvements indirectly (i.e. research how BMAD workflows and skills can enhance each other, i.e. encapsulate the following workflow in a global skill)
   3. Is the task defining a new repo, component, or project that may require a plane project to be properly classified?
3. Determine the task’s (`T0`) approximate t-shirt size level of effort (LoE)
4. Decompose the task into a logical and reasonable set of subtasks described in a temp file `T0-subtasks.md`. Take care to include ticket classifications and stakeholders.
5. For each subtask in `T0-subtasks.md` repeat from step 3 with `Tn` where `n=number of recursion levels` with a hard max of `nMAX=5`
6. For each task/subtask generated, convert them to plane ticket dev stories in the appropriate project board’s backlog
