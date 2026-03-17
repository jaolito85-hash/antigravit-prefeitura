# Agent Instructions
>
> This file is mirrored across CLAUDE.md, AGENTS.md, and GEMINI.md so the same
instructions load in any AI environment.
You operate within a 3-layer architecture that separates concerns to maximize reliability. LLMs
are probabilistic, whereas most business logic is deterministic and requires consistency. This
system fixes that mismatch.

## The 3-Layer Architecture

**Layer 1: Directive (What to do)**

- Basically just SOPs written in Markdown, live in `directives/`
- Define the goals, inputs, tools/scripts to use, outputs, and edge cases
- Natural language instructions, like you'd give a mid-level employee
**Layer 2: Orchestration (Decision making)**
- This is you. Your job: intelligent routing.
- Read directives, call execution tools in the right order, handle errors, ask for clarification,
update directives with learnings
- You're the glue between intent and execution. E.g you don't try scraping websites
yourself—you read `directives/city_feedback_monitor.md` and come up with inputs/outputs and then
run the appropriate `execution/` scripts
**Layer 3: Execution (Doing the work)**
- Deterministic Python scripts in `execution/`
- Environment variables, api tokens, etc are stored in `.env`
- Handle API calls, data processing, file operations, database interactions
- Reliable, testable, fast. Use scripts instead of manual work. Commented well.
**Why this works:** if you do everything yourself, errors compound. 90% accuracy per step =
59% success over 5 steps. The solution is push complexity into deterministic code. That way
you just focus on decision-making.

## App Context

This is the **Prefeitura Node Data** app — a dashboard for monitoring citizen feedback about
municipal services in real time. It receives WhatsApp messages, classifies them by category
(Infraestrutura, Saúde, Educação, Segurança, Limpeza, Transporte), sentiment, and city region,
then displays everything on a real-time dashboard.

## Operating Principles

**1. Check for tools first**
Before writing a script, check `execution/` per your directive. Only create new scripts if none
exist.
**2. Self-anneal when things break**

- Read error message and stack trace
- Fix the script and test it again (unless it uses paid tokens/credits/etc—in which case you check
w user first)
- Update the directive with what you learned (API limits, timing, edge cases)
**3. Update directives as you learn**
Directives are living documents. When you discover API constraints, better approaches,
common errors, or timing expectations—update the directive.

## File Organization

- `.tmp/` - All intermediate files (never commit)
- `execution/` - Python scripts (deterministic tools)
- `directives/` - SOPs in Markdown (instruction set)
- `.env` - Environment variables and API keys
