# 06 — Agent Skills Specification (agentskills.io)

**Research date:** 2026-10-03
**Dimension:** The Agent Skills specification at https://agentskills.io/specification
**Verification method:** All facts below were fetched live in this task from primary docs on `agentskills.io` and from the reference implementation source on `github.com/agentskills/agentskills`. Nothing here is from memory.

## Sources actually fetched

| # | URL | What it gave |
|---|-----|--------------|
| S1 | https://agentskills.io/specification | The normative spec (HTML render) |
| S2 | https://agentskills.io/specification.md | Same page as clean markdown (identical content; used for verbatim quotes) |
| S3 | https://agentskills.io/llms.txt | Full doc index (exists — confirmed) |
| S4 | https://agentskills.io/home.md | Overview, directory tree, progressive-disclosure stages, client list |
| S5 | https://agentskills.io/skill-creation/quickstart.md | Install path `.agents/skills/<name>/SKILL.md`, complete working example |
| S6 | https://agentskills.io/skill-creation/best-practices.md | 500-line / 5,000-token guidance, authoring patterns |
| S7 | https://agentskills.io/skill-creation/optimizing-descriptions.md | `description` writing rules, 1024-char hard limit restated |
| S8 | https://agentskills.io/client-implementation/adding-skills-support.md | Discovery paths, 3-tier loading table, lenient-validation rules |
| S9 | https://github.com/agentskills/agentskills/tree/main/skills-ref | The validator: install + CLI commands |
| S10 | https://raw.githubusercontent.com/agentskills/agentskills/main/skills-ref/src/skills_ref/validator.py | Exact validation checks, error strings, constants |
| S11 | https://raw.githubusercontent.com/agentskills/agentskills/main/skills-ref/src/skills_ref/parser.py | Exact parse errors, field list |
| S12 | https://api.github.com/repos/agentskills/agentskills/git/trees/main?recursive=1 | Repo file tree (confirms `skills-ref/` layout) |

There is **no JSON Schema** published for SKILL.md. The `skills-ref/` tree is `README.md`, `pyproject.toml`, `LICENSE`, and `src/skills_ref/{__init__,cli,errors,models,parser,prompt,validator}.py` plus tests — no `.json`/`.yaml` schema file (S12). Treat `validator.py` as the executable schema.

---

## 1. Directory structure (verbatim, S2)

> A skill is a directory containing, at minimum, a `SKILL.md` file:
>
> ```
> skill-name/
> ├── SKILL.md          # Required: metadata + instructions
> ├── scripts/          # Optional: executable code
> ├── references/       # Optional: documentation
> ├── assets/           # Optional: templates, resources
> └── ...               # Any additional files or directories
> ```

Identical tree appears on the overview page as `my-skill/` (S4).

### Where the skill directory lives — IMPORTANT NUANCE

The spec itself does **not** mandate an install location. Verbatim (S8):

> While the Agent Skills specification does not mandate where skill directories live (it only defines what goes inside them), scanning `.agents/skills/` means skills installed by other compliant clients are automatically visible to yours, and vice versa.

The task brief's assumed path `skills/<name>/SKILL.md` is only partly right. The documented **conventional** paths are (verbatim table, S8):

| Scope | Path | Purpose |
| - | - | - |
| Project | `<project>/.<your-client>/skills/` | Your client's native location |
| Project | `<project>/.agents/skills/` | Cross-client interoperability |
| User | `~/.<your-client>/skills/` | Your client's native location |
| User | `~/.agents/skills/` | Cross-client interoperability |

Plus, verbatim (S8):

> Some implementations also scan `.claude/skills/` (both project-level and user-level) for pragmatic compatibility, since many existing skills are installed there. Other additional locations include ancestor directories up to the git root (useful for monorepos), [XDG](https://specifications.freedesktop.org/basedir-spec/latest/) config directories, and user-configured paths.

The quickstart (S5) uses, verbatim: `.agents/skills/roll-dice/SKILL.md`, and says "VS Code looks for skills in `.agents/skills/` by default."

What *is* scanned for, verbatim (S8):

> Within each skills directory, look for **subdirectories containing a file named exactly `SKILL.md`**:
>
> ```
> ~/.agents/skills/
> ├── pdf-processing/
> │   ├── SKILL.md          ← discovered
> │   └── scripts/
> │       └── extract.py
> ├── data-analysis/
> │   └── SKILL.md          ← discovered
> └── README.md             ← ignored (not a skill directory)
> ```

Name collisions, verbatim (S8): "**project-level skills override user-level skills.**"

---

## 2. SKILL.md format

Verbatim (S2): "The `SKILL.md` file must contain YAML frontmatter followed by Markdown content."

### 2.1 Front matter table (verbatim, S2)

| Field | Required | Constraints |
| - | - | - |
| `name` | Yes | Max 64 characters. Lowercase letters, numbers, and hyphens only. Must not start or end with a hyphen. |
| `description` | Yes | Max 1024 characters. Non-empty. Describes what the skill does and when to use it. |
| `license` | No | License name or reference to a bundled license file. |
| `compatibility` | No | Max 500 characters. Indicates environment requirements (intended product, system packages, network access, etc.). |
| `metadata` | No | Arbitrary key-value mapping for additional metadata (a map from string keys to string values). |
| `allowed-tools` | No | Space-separated string of pre-approved tools the skill may use. (Experimental) |

**That is the complete field list. There are exactly 6 fields — 2 required, 4 optional.**

### 2.2 Exact spellings (hyphens vs underscores)

- `allowed-tools` — **hyphen**, not `allowed_tools`. (S2)
- `name`, `description`, `license`, `compatibility`, `metadata` — single lowercase words.
- **There is NO top-level `version` field.** The spec's own example puts version *inside* `metadata` as a quoted string: `metadata:` → `version: "1.0"` (S2). A top-level `version:` is an unexpected field and the reference validator **errors** on it (S10).

### 2.3 `name` field — full rules (verbatim, S2)

> The required `name` field:
>
> * Must be 1-64 characters
> * May only contain unicode lowercase alphanumeric characters (`a-z`, `0-9`) and hyphens (`-`)
> * Must not start or end with a hyphen (`-`)
> * Must not contain consecutive hyphens (`--`)
> * Must match the parent directory name

Valid examples, verbatim (S2):

```yaml
name: pdf-processing
```

```yaml
name: data-analysis
```

```yaml
name: code-review
```

Invalid examples, verbatim (S2):

```yaml
name: PDF-Processing  # uppercase not allowed
```

```yaml
name: -pdf  # cannot start with hyphen
```

```yaml
name: pdf--processing  # consecutive hyphens not allowed
```

Note: no underscores, no dots, no spaces — the character set is `a-z`, `0-9`, `-` only.

### 2.4 `description` field — full rules (verbatim, S2)

> The required `description` field:
>
> * Must be 1-1024 characters
> * Should describe both what the skill does and when to use it
> * Should include specific keywords that help agents identify relevant tasks

Good example, verbatim (S2):

```yaml
description: Extracts text and tables from PDF files, fills PDF forms, and merges multiple PDFs. Use when working with PDF documents or when the user mentions PDFs, forms, or document extraction.
```

Poor example, verbatim (S2):

```yaml
description: Helps with PDFs.
```

Writing rules, verbatim (S7):

> * **Use imperative phrasing.** Frame the description as an instruction to the agent: "Use this skill when..." rather than "This skill does..." The agent is deciding whether to act, so tell it when to act.
> * **Focus on user intent, not implementation.** Describe what the user is trying to achieve, not the skill's internal mechanics. The agent matches against what the user asked for.
> * **Err on the side of being pushy.** Explicitly list contexts where the skill applies, including cases where the user doesn't name the domain directly: "even if they don't explicitly mention 'CSV' or 'analysis.'"
> * **Keep it concise.** A few sentences to a short paragraph is usually right — long enough to cover the skill's scope, short enough that it doesn't bloat the agent's context across many skills. The [specification](/specification#description-field) enforces a hard limit of 1024 characters.

Also verbatim (S7) — a real gotcha for LetterLens: a skill may not trigger at all on trivial requests:

> One important nuance: agents typically only consult skills for tasks that require knowledge or capabilities beyond what they can handle alone. A simple, one-step request like "read this PDF" may not trigger a PDF skill even if the description matches perfectly, because the agent can handle it with basic tools.

Before/after example, verbatim (S7) — note it uses a YAML folded block scalar `>`:

```yaml
# Before
description: Process CSV files.

# After
description: >
  Analyze CSV and tabular data files — compute summary statistics,
  add derived columns, generate charts, and clean messy data. Use this
  skill when the user has a CSV, TSV, or Excel file and wants to
  explore, transform, or visualize the data, even if they don't
  explicitly mention "CSV" or "analysis."
```

### 2.5 `license` field (verbatim, S2)

> The optional `license` field:
>
> * Specifies the license applied to the skill
> * We recommend keeping it short (either the name of a license or the name of a bundled license file)

```yaml
license: Proprietary. LICENSE.txt has complete terms
```

(The front-matter table's minimal example also uses `license: Apache-2.0`.)

### 2.6 `compatibility` field (verbatim, S2)

> The optional `compatibility` field:
>
> * Must be 1-500 characters if provided
> * Should only be included if your skill has specific environment requirements
> * Can indicate intended product, required system packages, network access needs, etc.

```yaml
compatibility: Designed for Claude Code (or similar products)
```

```yaml
compatibility: Requires git, docker, jq, and access to the internet
```

```yaml
compatibility: Requires Python 3.14+ and uv
```

> **Note:** Most skills do not need the `compatibility` field.

### 2.7 `metadata` field (verbatim, S2)

> The optional `metadata` field:
>
> * A map from string keys to string values
> * Clients can use this to store additional properties not defined by the Agent Skills spec
> * We recommend making your key names reasonably unique to avoid accidental conflicts

```yaml
metadata:
  author: example-org
  version: "1.0"
```

Values are **strings** — note `"1.0"` is quoted so YAML does not parse it as a float. The reference parser describes `metadata` as "optional, dict with string key-value pairs" (S11).

### 2.8 `allowed-tools` field (verbatim, S2)

> The optional `allowed-tools` field:
>
> * A space-separated string of tools that are pre-approved to run
> * Experimental. Support for this field may vary between agent implementations

```yaml
allowed-tools: Bash(git:*) Bash(jq:*) Read
```

It is a **single space-separated string**, not a YAML list.

---

## 3. Body / Markdown conventions and size limits

Verbatim (S2):

> ### Body content
>
> The Markdown body after the frontmatter contains the skill instructions. There are no format restrictions. Write whatever helps agents perform the task effectively.
>
> Recommended sections:
>
> * Step-by-step instructions
> * Examples of inputs and outputs
> * Common edge cases
>
> Note that the agent will load this entire file once it's decided to activate a skill. Consider splitting longer `SKILL.md` content into referenced files.

**Size limits (all RECOMMENDATIONS, not hard failures):**

- "Keep your main `SKILL.md` under 500 lines. Move detailed reference material to separate files." (S2)
- "**Instructions** (\< 5000 tokens recommended): The full `SKILL.md` body is loaded when the skill is activated" (S2)
- Restated verbatim (S6): "The [specification](/specification#progressive-disclosure) recommends keeping `SKILL.md` under 500 lines and 5,000 tokens — just the core instructions the agent needs on every run."

There is **no word-count limit** anywhere in the spec. The limits are 500 lines / ~5,000 tokens, and neither is enforced by the validator.

The only **hard** character limits are: `name` ≤ 64, `description` ≤ 1024, `compatibility` ≤ 500.

---

## 4. Progressive disclosure

Verbatim (S2):

> Agents load skills *progressively*, pulling in more detail only as a task calls for it. Skills should be structured to take advantage of this:
>
> 1. **Metadata** (\~100 tokens): The `name` and `description` fields are loaded at startup for all skills
> 2. **Instructions** (\< 5000 tokens recommended): The full `SKILL.md` body is loaded when the skill is activated
> 3. **Resources** (as needed): Files (e.g. those in `scripts/`, `references/`, or `assets/`) are loaded only when required
>
> Keep your main `SKILL.md` under 500 lines. Move detailed reference material to separate files.

The implementation guide states the same as a three-tier table, verbatim (S8):

| Tier | What's loaded | When | Token cost |
| - | - | - | - |
| 1. Catalog | Name + description | Session start | \~50-100 tokens per skill |
| 2. Instructions | Full `SKILL.md` body | When the skill is activated | \<5000 tokens (recommended) |
| 3. Resources | Scripts, references, assets | When the instructions reference them | Varies |

Overview phrasing of the same three stages, verbatim (S4): **Discovery** → **Activation** → **Execution**.

### How referenced files are meant to be loaded

Verbatim (S2):

> ## File references
>
> When referencing other files in your skill, use relative paths from the skill root:
>
> ```markdown
> See [the reference guide](references/REFERENCE.md) for details.
>
> Run the extraction script:
> scripts/extract.py
> ```
>
> Keep file references one level deep from `SKILL.md`. Avoid deeply nested reference chains.

Critically — the *trigger condition* must be written into SKILL.md. Verbatim (S6):

> The key is telling the agent *when* to load each file. "Read `references/api-errors.md` if the API returns a non-200 status code" is more useful than a generic "see references/ for details." This lets the agent load context on demand rather than up front, which is how [progressive disclosure](/specification#progressive-disclosure) is designed to work.

And on the harness side, verbatim (S8): "When a dedicated activation tool returns skill content, it can also enumerate supporting files (scripts, references, assets) in the skill directory — but it should **not eagerly read them**."

Path resolution guidance given to the model, verbatim (S8):

```
When a skill references relative paths, resolve them against the skill's
directory (the parent of SKILL.md) and use absolute paths in tool calls.
```

---

## 5. Optional directories (verbatim, S2)

> A skill directory may contain any files and directories beyond the required `SKILL.md`. The conventions below are recommendations for organizing common types of content.
>
> ### `scripts/`
>
> Contains executable code that agents can run. Scripts should:
>
> * Be self-contained or clearly document dependencies
> * Include helpful error messages
> * Handle edge cases gracefully
>
> Supported languages depend on the agent implementation. Common options include Python, Bash, and JavaScript.
>
> ### `references/`
>
> Contains additional documentation that agents can read when needed:
>
> * `REFERENCE.md` - Detailed technical reference
> * `FORMS.md` - Form templates or structured data formats
> * Domain-specific files (`finance.md`, `legal.md`, etc.)
>
> Keep individual [reference files](#file-references) focused. Agents load these on demand, so smaller files mean less use of context.
>
> ### `assets/`
>
> Contains static resources:
>
> * Templates (document templates, configuration templates)
> * Images (diagrams, examples)
> * Data files (lookup tables, schemas)

These three directory names are **conventions, not requirements**. "Any additional files or directories" are allowed.

---

## 6. Complete minimal VALID examples (verbatim)

### 6.1 The spec's minimal example (S2)

File: `SKILL.md`

```markdown
---
name: skill-name
description: A description of what this skill does and when to use it.
---
```

(Yes — the spec's literal minimal example has an **empty body**. Only the front matter is structurally required.)

### 6.2 The spec's example with optional fields (S2)

File: `SKILL.md`

```markdown
---
name: pdf-processing
description: Extract PDF text, fill forms, merge files. Use when handling PDFs.
license: Apache-2.0
metadata:
  author: example-org
  version: "1.0"
---
```

### 6.3 The quickstart's complete working skill (S5)

File: `.agents/skills/roll-dice/SKILL.md`

~~~markdown
---
name: roll-dice
description: Roll dice using a random number generator. Use when asked to roll a die (d6, d20, etc.), roll dice, or generate a random dice roll.
---

To roll a die, use the following command that generates a random number from 1
to the given number of sides:

```bash
echo $((RANDOM % <sides> + 1))
```

```powershell
Get-Random -Minimum 1 -Maximum (<sides> + 1)
```

Replace `<sides>` with the number of sides on the die (e.g., 6 for a standard
die, 20 for a d20).
~~~

Quickstart commentary, verbatim (S5):

> That's it — one file, under 20 lines. Here's what each part does:
>
> * **`name`** — A short identifier for the skill. Must match the folder name.
> * **`description`** — Tells the agent when to use this skill. This is how the agent decides whether to activate it.
> * **The body** — Instructions the agent follows when the skill activates.

---

## 7. INVALID checklist — what makes a skill fail

Derived from the spec (S2) and confirmed against the reference validator source (S10) and parser source (S11). Severity column: **ERROR** = `skills-ref validate` reports a problem; **WARN** = real clients are documented to warn but load anyway (S8).

### Structural

- [ ] **Path does not exist** → ERROR `"Path does not exist"` (S10)
- [ ] **Target is not a directory** → ERROR `"Not a directory"` (S10)
- [ ] **No `SKILL.md` in the directory** → ERROR `"Missing required file: SKILL.md"` (S10). The filename must be exactly `SKILL.md` — uppercase, with `.md` (S8).
- [ ] **File does not begin with `---`** → ERROR `"SKILL.md must start with YAML frontmatter (---)"` (S11)
- [ ] **Front matter never closed with `---`** → ERROR `"SKILL.md frontmatter not properly closed with ---"` (S11)
- [ ] **Front matter is not a YAML mapping** (e.g. a list or scalar) → ERROR `"SKILL.md frontmatter must be a YAML mapping"` (S11)
- [ ] **Invalid YAML** → ERROR `"Invalid YAML in frontmatter: {e}"` (S11)

### Fields

- [ ] **Missing `name`** → ERROR `"Missing required field in frontmatter: name"` (S10, S11)
- [ ] **Missing `description`** → ERROR `"Missing required field in frontmatter: description"` (S10, S11)
- [ ] **`name` empty or not a string** → ERROR `"Field 'name' must be a non-empty string"` (S10, S11)
- [ ] **`description` empty or not a string** → ERROR `"Field 'description' must be a non-empty string"` (S10, S11). Note (S8): a missing/empty description means real clients **skip the skill entirely**, not just warn.
- [ ] **`name` > 64 characters** → ERROR (constant `MAX_SKILL_NAME_LENGTH = 64`) (S10)
- [ ] **`name` contains uppercase** → ERROR `"Skill name must be lowercase"` (S10)
- [ ] **`name` starts or ends with `-`** → ERROR (S10)
- [ ] **`name` contains `--`** → ERROR (S10)
- [ ] **`name` contains anything but letters, digits, hyphens** (underscores, dots, spaces, slashes) → ERROR (S10)
- [ ] **`name` ≠ parent directory name** → ERROR `"Directory name must match skill name"` (S10). Real clients: WARN and load anyway (S8).
- [ ] **`description` > 1024 characters** → ERROR (constant `MAX_DESCRIPTION_LENGTH = 1024`) (S10)
- [ ] **`compatibility` not a string** → ERROR `"Field 'compatibility' must be a string"` (S10)
- [ ] **`compatibility` > 500 characters** → ERROR (constant `MAX_COMPATIBILITY_LENGTH = 500`) (S10)
- [ ] **ANY field outside the allowed set** → ERROR. The validator errors on unexpected fields; the allowed set is exactly `{name, description, license, allowed-tools, metadata, compatibility}` (S10). **This is the one that bites: top-level `version:`, `author:`, `tags:`, `model:`, `allowed_tools:` (underscore) are all invalid. Put extras under `metadata:`.**

### Author-side smells that are NOT validation failures

- `SKILL.md` over 500 lines or over ~5,000 tokens — recommendation only, not checked (S2, S6).
- No `scripts/`, `references/`, `assets/` — those directories are optional conventions (S2).
- Empty markdown body — the spec's own minimal example has one (S2).
- Reference chains more than one level deep — "Avoid deeply nested reference chains" is advice, not a rule (S2).

### YAML gotcha worth knowing (verbatim, S8)

> Skill files authored for other clients may contain technically invalid YAML that their parsers happen to accept. The most common issue is unquoted values containing colons:
>
> ```yaml
> # Technically invalid YAML — the colon breaks parsing
> description: Use this skill when: the user asks about PDFs
> ```

Fix: quote the value or use a block scalar (`>` or `|`).

### Lenient-loading rules real clients are told to follow (verbatim, S8)

> * Name doesn't match the parent directory name → warn, load anyway
> * Name exceeds 64 characters → warn, load anyway
> * Description is missing or empty → skip the skill (a description is essential for disclosure), log the error
> * YAML is completely unparseable → skip the skill, log the error

So there are effectively two conformance bars: **strict** (the spec + `skills-ref validate`) and **lenient** (what shipping agents actually accept). Author to the strict bar.

---

## 8. Validator / linter

**Tool name:** `skills-ref` — "the reference library for Agent Skills" (S2), self-described in its README as "designed for demonstration purposes only and not intended for production use" (S9). Apache 2.0. It is **Python** (pip/uv), **not npm and not cargo** (S9).

Spec's own pointer, verbatim (S2):

> ## Validation
>
> Use the [skills-ref](https://github.com/agentskills/agentskills/tree/main/skills-ref) reference library to validate your skills:
>
> ```bash
> skills-ref validate ./my-skill
> ```
>
> This checks that your `SKILL.md` frontmatter is valid and follows all naming conventions.

### Install (S9)

macOS/Linux with pip:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Windows with pip:

```bash
python -m venv .venv
.venv\Scripts\activate.bat
pip install -e .
```

Installed from a clone of `github.com/agentskills/agentskills`, from inside the `skills-ref/` directory (`pip install -e .`). It is **not** documented as published to PyPI — plan on a git clone. After setup the `skills-ref` executable is on PATH inside the venv.

### CLI commands (S9)

```bash
skills-ref validate path/to/skill
skills-ref read-properties path/to/skill
skills-ref to-prompt path/to/skill-a path/to/skill-b
```

- `validate` — checks a skill directory for issues
- `read-properties` — outputs skill metadata as JSON
- `to-prompt` — creates the `<available_skills>` XML block for agent prompts

### Python API (S9)

```python
validate(Path)            # validates skill directory; returns a problems list
read_properties(Path)     # retrieves skill metadata
to_prompt(List[Path])     # generates <available_skills> XML for agent system prompts
```

**Exit codes are NOT documented** (S9) — confidence low. If you wire this into CI, assert on the problems list / stdout rather than assuming a particular exit status, or read `skills-ref/src/skills_ref/cli.py` first.

---

## 9. Catalog format a host injects (verbatim, S8)

Useful if LetterLens ever needs to emulate or parse what a host shows the model:

```xml
<available_skills>
  <skill>
    <name>pdf-processing</name>
    <description>Extract PDF text, fill forms, merge files. Use when handling PDFs.</description>
    <location>/home/user/.agents/skills/pdf-processing/SKILL.md</location>
  </skill>
  <skill>
    <name>data-analysis</name>
    <description>Analyze datasets, generate charts, and create summary reports.</description>
    <location>/home/user/project/.agents/skills/data-analysis/SKILL.md</location>
  </skill>
</available_skills>
```

And the optional structured wrapping of activated content (verbatim, S8):

```xml
<skill_content name="pdf-processing">
# PDF Processing

## When to use this skill
Use this skill when the user needs to work with PDF files...

[rest of SKILL.md body]

Skill directory: /home/user/.agents/skills/pdf-processing
Relative paths in this skill are relative to the skill directory.

<skill_resources>
  <file>scripts/extract.py</file>
  <file>scripts/merge.py</file>
  <file>references/pdf-spec-summary.md</file>
</skill_resources>
</skill_content>
```

Note (S8): a `disable-model-invocation` flag is mentioned **only** as an example of a client-specific opt-out ("e.g., via a `disable-model-invocation` flag") — it is **not** a spec field and would be rejected as an unexpected field by `skills-ref`. If you need it, it belongs under `metadata:` or is client-proprietary.

---

## 10. Authoring patterns worth copying (verbatim excerpts, S6)

These are the reusable structural patterns the best-practices page names. Each has a verbatim example on that page.

- **Gotchas sections** — "environment-specific facts that defy reasonable assumptions… concrete corrections to mistakes the agent will make without being told otherwise." Keep them in `SKILL.md`, not a reference file: "for non-obvious issues, the agent may not recognize the trigger."
- **Templates for output format** — "Short templates can live inline in `SKILL.md`; for longer templates, or templates only needed in certain cases, store them in `assets/` and reference them from `SKILL.md` so they only load when needed."
- **Checklists for multi-step workflows**:
  ```markdown
  ## Form processing workflow

  Progress:
  - [ ] Step 1: Analyze the form (run `scripts/analyze_form.py`)
  - [ ] Step 2: Create field mapping (edit `fields.json`)
  - [ ] Step 3: Validate mapping (run `scripts/validate_fields.py`)
  - [ ] Step 4: Fill the form (run `scripts/fill_form.py`)
  - [ ] Step 5: Verify output (run `scripts/verify_output.py`)
  ```
- **Validation loops**:
  ```markdown
  ## Editing workflow

  1. Make your edits
  2. Run validation: `python scripts/validate.py output/`
  3. If validation fails:
     - Review the error message
     - Fix the issues
     - Run validation again
  4. Only proceed when validation passes
  ```
- **Plan-validate-execute** — for batch/destructive ops, write an intermediate plan file, validate it against a source-of-truth file with a script, then execute.
- **Provide defaults, not menus** — "pick a default and mention alternatives briefly rather than presenting them as equal options."
- **Add what the agent lacks, omit what it knows** — "Would the agent get this wrong without this instruction?" If no, cut it.
- **Match specificity to fragility** — be loose where multiple approaches work, prescriptive where sequence matters ("Run exactly this sequence… Do not modify the command or add additional flags.").

---

## 11. Bottom line for LetterLens

A valid skill is: a directory named exactly like its `name`, containing `SKILL.md`, whose front matter has `name` + `description` and nothing outside the six allowed keys. Everything else — `scripts/`, `references/`, `assets/`, the 500-line budget, one-level-deep references — is convention and advice, not validation.

The two things most likely to break a LetterLens skill:

1. A top-level `version:` (or any other extra key) in front matter. It must go under `metadata:` as a **quoted string**.
2. Putting the skill somewhere the host doesn't scan. The spec is silent on location; use `.agents/skills/<name>/SKILL.md` for portability and `.claude/skills/<name>/SKILL.md` for Claude Code compatibility. Both are documented conventions, neither is normative.
