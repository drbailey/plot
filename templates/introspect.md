# Command: `.introspect`

Perform a retrospective analysis of the current session.

## Syntax

```
.introspect
<optional focus_area - specific aspect to analyze>
```

## Parsing Rules

- If text follows `.introspect`, it's the focus_area
- focus_area narrows the analysis to a specific aspect

## Execution

### Step 1: Review Conversation History

Analyze the conversation for:
- Errors, failures, or unexpected results
- Misunderstandings or misinterpretations
- Repeated attempts or corrections
- Inefficient patterns (excessive tool calls, redundant reads, etc.)

### Step 2: Evaluate Addons

If the current story used a plan, evaluate how the addon system performed. Read `plot/templates/evaluate-addons.md` for the registry.

**2a: Registry Accuracy**

For each addon in the registry:
- Was it **included** in the plan? Check the plan's `Addons` metadata field.
- If included: did the criteria correctly trigger? Or was it a false positive (criteria matched but the work didn't actually benefit from the addon)?
- If excluded: should it have been included? Did the work involve something the criteria missed?

**2b: Addon Value (for each included addon)**

Read the addon template that was included (e.g., `plot/templates/addons/data-pipeline.md`) and evaluate:
- Did the addon section in the plan get used during execution? Did executors reference it?
- Was the content accurate and complete enough to be useful?
- Were there gaps — stages, fields, or examples that were missing or wrong?
- Was any part of the addon section unnecessary noise that added no value?

**2c: Corrective Actions**

Based on findings from 2a and 2b, propose concrete changes:

- **False positive** (addon included, no value): Tighten the registry criteria in `plot/templates/evaluate-addons.md` to exclude this case. Edit the "Include when" cell to add exclusion language or narrow the trigger conditions.
- **False negative** (addon not included, should have been): Broaden the registry criteria to capture the missed case. Add signal words or conditions.
- **Addon content gaps**: Propose edits to the addon template itself (e.g., missing stages, unclear examples, section structure that didn't fit the work).
- **Addon content noise**: Propose removing or making optional the parts that added no value.

Apply corrective edits directly — introspect should leave the system better than it found it.

### Step 3: Provide Actionable Guidance

Organize findings by category:

**Tool Usage Improvements**
- Function calls that failed or required retry
- Better parameter choices or tool selection
- Opportunities to parallelize or batch calls

**Template/Prompt Improvements**
- Ambiguities in instructions that caused confusion
- Missing context that would have helped
- Suggested edits to templates or prompts

**Addon Improvements**
- Summary of findings from Step 2 (registry accuracy, addon value, corrective actions taken)
- Any addons that consistently underperform and may need redesign

**User Input Improvements**
- Information that should have been provided upfront
- Clearer ways to phrase requests
- Useful context patterns for future sessions

**Efficiency Gains**
- Unnecessary steps that could be eliminated
- Faster paths to the same result
- Caching or reuse opportunities

### Step 4: Format Output

- Group findings by category
- For each issue: describe what happened, why, and the recommended fix
- Prioritize by impact (high-impact improvements first)
- Include specific file/line references for template or code changes

## Optional focus_area

If provided, narrow the analysis to that aspect (e.g., "tool usage", "templates", "addons", "efficiency").

## Examples

### Full retrospective

```
.introspect
```

### Focused on templates

```
.introspect templates
```

### Focused on a specific problem

```
.introspect
Why did task decomposition require multiple retries?
```
