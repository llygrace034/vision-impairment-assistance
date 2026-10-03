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

---

## Independent verification (adversarial pass)

**Verification date:** 2026-10-03
**Method:** Every source below was re-fetched in this pass. The cited URLs in the original note were *not* taken on trust. Reference-implementation files were pulled as raw bytes with `curl` (not summarized by a model) so the quoted code is exact.

### Sources I fetched myself in this pass

| # | URL | How |
|---|-----|-----|
| V1 | https://agentskills.io/specification.md | WebFetch |
| V2 | https://agentskills.io/llms.txt | curl (raw) |
| V3 | https://agentskills.io/client-implementation/adding-skills-support.md | WebFetch |
| V4 | https://agentskills.io/skill-creation/best-practices.md | WebFetch |
| V5 | https://agentskills.io/skill-creation/optimizing-descriptions.md | WebFetch |
| V6 | https://raw.githubusercontent.com/agentskills/agentskills/main/skills-ref/src/skills_ref/validator.py | curl (raw, exact) |
| V7 | https://raw.githubusercontent.com/agentskills/agentskills/main/skills-ref/src/skills_ref/parser.py | curl (raw, exact) |
| V8 | https://raw.githubusercontent.com/agentskills/agentskills/main/skills-ref/src/skills_ref/cli.py | curl (raw, exact) — **not fetched by the original pass** |
| V9 | https://raw.githubusercontent.com/agentskills/agentskills/main/skills-ref/src/skills_ref/models.py | curl (raw, exact) — **not fetched by the original pass** |
| V10 | https://raw.githubusercontent.com/agentskills/agentskills/main/skills-ref/src/skills_ref/prompt.py | curl (raw, exact) — **not fetched by the original pass** |
| V11 | https://raw.githubusercontent.com/agentskills/agentskills/main/skills-ref/src/skills_ref/errors.py | curl (raw, exact) — **not fetched by the original pass** |
| V12 | https://raw.githubusercontent.com/agentskills/agentskills/main/skills-ref/pyproject.toml | curl (raw, exact) — **not fetched by the original pass** |
| V13 | https://raw.githubusercontent.com/agentskills/agentskills/main/skills-ref/README.md | curl (raw, exact) |
| V14 | https://raw.githubusercontent.com/agentskills/agentskills/main/skills-ref/tests/test_parser.py | curl (raw, exact) — **not fetched by the original pass** |
| V15 | https://raw.githubusercontent.com/agentskills/agentskills/main/skills-ref/tests/test_validator.py | curl (raw, exact) — **not fetched by the original pass** |
| V16 | https://api.github.com/repos/agentskills/agentskills/git/trees/main?recursive=1 | curl (raw JSON, `"truncated": false`) |

### Claim-by-claim verdicts

| # | Claim (abridged) | Status |
|---|---|---|
| 1 | Skill = directory with at minimum SKILL.md; YAML frontmatter + Markdown | **CONFIRMED** (V1) |
| 2 | Exactly six frontmatter fields, no others defined | **CONFIRMED** (V1, V6) |
| 3 | No top-level `version`; nested under `metadata` as `"1.0"` | **CONFIRMED** (V1) — but the stated *reason* for quoting is wrong for skills-ref; see Correction C3 |
| 4 | Validator errors on any field outside the six | **CONFIRMED** (V6, V15) |
| 5 | `name`: 1-64 chars, a-z/0-9/hyphen, no leading/trailing/consecutive hyphen, matches dir | **CONFIRMED as spec text** (V1) — **but the validator is materially more permissive**; see Correction C5 |
| 6 | `description`: 1-1024 chars, what + when, keywords | **CONFIRMED** (V1) |
| 7 | `compatibility` 1-500; `metadata` string-to-string map; `allowed-tools` space-separated string, Experimental | **CONFIRMED** (V1) |
| 8 | Spelling is `allowed-tools` (hyphen); `allowed_tools` rejected | **CONFIRMED** (V1, V6, V9) |
| 9 | `MAX_SKILL_NAME_LENGTH=64`, `MAX_DESCRIPTION_LENGTH=1024`, `MAX_COMPATIBILITY_LENGTH=500` | **CONFIRMED** (V6, exact) |
| 10 | Eight "exact" validator error strings | **REFUTED** — 3 of 8 are not what the code emits, 2 more are prefixes only; see Correction C10 |
| 11 | Five exact parser error strings | **CONFIRMED** — all five match the source byte-for-byte (V7) |
| 12 | 500 lines / under 5000 tokens are recommendations, not validated; no word-count limit | **CONFIRMED** (V1, V4, V6) |
| 13 | Three progressive-disclosure tiers with those token figures | **CONFIRMED** (V1, V3) |
| 14 | Relative paths from skill root; one level deep; avoid nesting | **CONFIRMED** (V1) |
| 15 | SKILL.md must state WHEN to load each referenced file | **CONFIRMED** (V4, verbatim match) |
| 16 | Spec does not mandate install location; the four conventions plus `.claude/skills/` | **CONFIRMED** (V3, verbatim match) |
| 17 | Discovery scans for subdirs containing exactly `SKILL.md`; project overrides user | **CONFIRMED for the client guide** (V3) — **but skills-ref itself also accepts `skill.md`**; see Correction C17 |
| 18 | Lenient client validation: warn on name issues, skip on missing description / bad YAML | **CONFIRMED** (V3, verbatim match) |
| 19 | `skills-ref`, Python via pip/uv, three commands, "demonstration purposes only" | **CONFIRMED in substance; the quoted sentence is REFUTED as verbatim** — see Correction C19 |
| 20 | No JSON Schema; skills-ref tree contents | **CONFIRMED on the substance (no schema file)**; the file list is incomplete — see Correction C20 |
| 21 | Exit codes are not documented | **REFUTED** — they are documented, in `cli.py`; see Correction C21 |
| 22 | Skills may not trigger on trivial one-step requests | **CONFIRMED** (V5, verbatim match) |
| 23 | Unquoted colons = invalid YAML, most common cross-client failure | **CONFIRMED** (V3) — with a framing nuance, see Correction C23 |
| 24 | `disable-model-invocation` is a client flag example, not a spec field | **CONFIRMED** (V3, V6) |

---

### Corrections

#### C10 — The validator's error strings are f-strings with interpolated values. DO NOT string-equality-match them.

Exact source (V6). What the claim got right:

```python
return ["Missing required file: SKILL.md"]                   # exact - correct
errors.append("Missing required field in frontmatter: name")  # exact - correct
errors.append("Field 'name' must be a non-empty string")      # exact - correct
errors.append("Field 'compatibility' must be a string")       # exact - correct
```

What the claim got **wrong** — the real code is:

```python
return [f"Path does not exist: {skill_dir}"]      # NOT "Path does not exist"
return [f"Not a directory: {skill_dir}"]          # NOT "Not a directory"
errors.append(f"Skill name '{name}' must be lowercase")
#   NOT "Skill name must be lowercase" - the name is interpolated INSIDE the sentence
errors.append(
    f"Directory name '{skill_dir.name}' must match skill name '{name}'"
)
#   NOT "Directory name must match skill name"
```

Other error strings the original note never captured (all verbatim, V6):

```python
f"Skill name '{name}' exceeds {MAX_SKILL_NAME_LENGTH} character limit ({len(name)} chars)"
"Skill name cannot start or end with a hyphen"
"Skill name cannot contain consecutive hyphens"
f"Skill name '{name}' contains invalid characters. Only letters, digits, and hyphens are allowed."
f"Description exceeds {MAX_DESCRIPTION_LENGTH} character limit ({len(description)} chars)"
f"Compatibility exceeds {MAX_COMPATIBILITY_LENGTH} character limit ({len(compatibility)} chars)"
f"Unexpected fields in frontmatter: {', '.join(sorted(extra_fields))}. Only {sorted(ALLOWED_FIELDS)} are allowed."
```

**Build implication:** if LetterLens asserts on validator output, use substring matching on stable fragments (`"must be lowercase"`, `"Unexpected fields in frontmatter"`, `"must match skill name"`), exactly as the reference tests themselves do (`assert any("lowercase" in e for e in errors)`, V15). Never `==`.

#### C5 — The validator does NOT enforce a-z / 0-9. Unicode names are valid.

The spec text (claim 5) is accurate as spec text, but `validator.py` enforces something looser. Verbatim (V6):

```python
def _validate_name(name: str, skill_dir: Path) -> list[str]:
    """Validate skill name format and directory match.

    Skill names support i18n characters (Unicode letters) plus hyphens.
    Names must be lowercase and cannot start/end with hyphens.
    """
```

and the character check is:

```python
if not all(c.isalnum() or c == "-" for c in name):
```

`str.isalnum()` is Unicode-aware, so any Unicode letter or digit passes. The reference test suite asserts this deliberately (V15):

- `test_i18n_chinese_name` — directory and name both the Chinese word for "skill" (2 CJK chars) -> `assert errors == []`
- `test_i18n_russian_name_with_hyphens` — a Cyrillic hyphenated name -> `assert errors == []`
- `test_i18n_russian_lowercase_valid` — a lowercase Cyrillic name -> `assert errors == []`
- `test_i18n_russian_uppercase_rejected` — the same name uppercased -> `assert any("lowercase" in e for e in errors)`

Also missed: **names and directory names are NFKC-normalized and stripped before comparison** (V6):

```python
name = unicodedata.normalize("NFKC", name.strip())
...
dir_name = unicodedata.normalize("NFKC", skill_dir.name)
if dir_name != name:
```

`test_nfkc_normalization` (V15) confirms a composed directory name matches a decomposed `name:` value. For LetterLens (ASCII kebab-case names) none of this bites — but do not build a stricter in-house regex and claim it mirrors `skills-ref`.

#### C3 — BIGGEST MISS: the reference parser is `strictyaml`, not PyYAML. Everything is a string.

The original note never named the YAML library. It matters a lot.

`pyproject.toml` verbatim (V12):

```toml
[project]
name = "skills-ref"
version = "0.1.0"
description = "Reference library for Agent Skills"
license = "Apache-2.0"
requires-python = ">=3.11"
dependencies = [
    "click>=8.0",
    "strictyaml>=1.7.3",
]

[project.scripts]
skills-ref = "skills_ref.cli:main"
```

`parser.py` verbatim (V7):

```python
import strictyaml
...
    try:
        parsed = strictyaml.load(frontmatter_str)
        metadata = parsed.data
    except strictyaml.YAMLError as e:
        raise ParseError(f"Invalid YAML in frontmatter: {e}")

    if not isinstance(metadata, dict):
        raise ParseError("SKILL.md frontmatter must be a YAML mapping")

    if "metadata" in metadata and isinstance(metadata["metadata"], dict):
        metadata["metadata"] = {str(k): str(v) for k, v in metadata["metadata"].items()}
```

Consequences the build needs:

1. **Unquoted `version: 1.0` is NOT coerced to a float by `skills-ref`.** The reference test proves it (V14, `test_read_with_metadata`): the file contains unquoted `version: 1.0` under `metadata:` and the assertion is `assert props.metadata == {"author": "Test Author", "version": "1.0"}`. So the original note's reasoning ("quoted so YAML does not parse it as a float") is **wrong for skills-ref**. Quote it anyway — PyYAML- and js-yaml-based clients *do* coerce, and the spec's own example quotes it — but do not cite skills-ref as the reason.
2. **The `isinstance(..., str)` guards are near-unreachable for scalars.** Because strictyaml returns `str` for every scalar, `"Field 'name' must be a non-empty string"` and `"Field 'compatibility' must be a string"` can only fire when the value is a mapping or a sequence (or empty/whitespace), not when it is a number or boolean. Do not write a test expecting `compatibility: 42` to produce the "must be a string" error.
3. **strictyaml is a restricted YAML subset.** Use **block style only** for `metadata:` — every spec example (V1), every README example (V13) and every reference test (V14, V15) uses block style. The inline flow form `metadata: { version: "1.0" }` that appears in the original note's blockers list is **not demonstrated anywhere in any primary source I fetched**, and strictyaml is a restricted parser. *Confidence: the strictyaml dependency is CONFIRMED; whether flow style specifically raises is UNVERIFIED — I found no primary doc in this pass that settles it. Treat flow style as unsupported until someone runs it locally.*

Write this, not the flow form:

```yaml
metadata:
  author: letterlens
  version: "0.1.0"
```

#### C17 — `skills-ref` accepts lowercase `skill.md`. The note's "must be exactly SKILL.md" is wrong for the validator.

Section 7 of the original note states the filename "must be exactly `SKILL.md` — uppercase, with `.md`". That is the *client discovery* guidance from V3 ("subdirectories containing a file named exactly `SKILL.md`") and is confirmed as such. But `skills-ref` disagrees. Verbatim (V7):

```python
def find_skill_md(skill_dir: Path) -> Optional[Path]:
    """Find the SKILL.md file in a skill directory.

    Prefers SKILL.md (uppercase) but accepts skill.md (lowercase).
    """
    for name in ("SKILL.md", "skill.md"):
        path = skill_dir / name
        if path.exists():
            return path
    return None
```

Reference tests (V14): `test_find_skill_md_prefers_uppercase`, `test_find_skill_md_accepts_lowercase`, `test_read_properties_with_lowercase_skill_md`. **LetterLens should still always write `SKILL.md` uppercase** — the discovery guidance in V3 is the binding one for real clients — but a lowercase file will *pass* `skills-ref validate` while being invisible to a strict client. That asymmetry is a trap worth a CI check of its own.

#### C21 — Exit codes ARE documented, and errors go to stderr, not stdout. This reverses a stated blocker.

The original pass concluded (confidence: low) that exit codes are undocumented and advised asserting on stdout. Both halves are wrong. `cli.py` verbatim (V8):

```python
@main.command("validate")
@click.argument("skill_path", type=click.Path(exists=True, path_type=Path))
def validate_cmd(skill_path: Path):
    """Validate a skill directory.

    Checks that the skill has a valid SKILL.md with proper frontmatter,
    correct naming conventions, and required fields.

    Exit codes:
        0: Valid skill
        1: Validation errors found
    """
    if _is_skill_md_file(skill_path):
        skill_path = skill_path.parent

    errors = validate(skill_path)

    if errors:
        click.echo(f"Validation failed for {skill_path}:", err=True)
        for error in errors:
            click.echo(f"  - {error}", err=True)
        sys.exit(1)
    else:
        click.echo(f"Valid skill: {skill_path}")
```

Documented exit codes for all three commands (V8 docstrings):

| Command | 0 | 1 |
|---|---|---|
| `validate` | Valid skill | Validation errors found |
| `read-properties` | Success | Parse error |
| `to-prompt` | Success | Error |

**Build implications:**

- `skills-ref validate` **does** exit non-zero on failure. It is safe to use as a CI gate on exit status alone.
- Failure output goes to **stderr** (`err=True`), formatted as `Validation failed for <path>:` then one `  - <error>` line per problem. Success goes to **stdout** as `Valid skill: <path>`. Capture stderr, not stdout, when collecting problems.
- A **third** exit code exists in practice: `click.Path(exists=True)` rejects a nonexistent path *before* `validate()` runs, so Click emits its own usage error and exits **2**. This means the library error `f"Path does not exist: {skill_dir}"` is effectively **unreachable through the CLI** — it only appears when calling `validate()` from Python.
- `skills-ref validate` accepts a path to the **file** as well as the directory, case-insensitively (V8):

```python
def _is_skill_md_file(path: Path) -> bool:
    """Check if path points directly to a SKILL.md or skill.md file."""
    return path.is_file() and path.name.lower() == "skill.md"
```

- A `--version` flag exists (`@click.version_option()` on the group).

#### C19 — The README's production warning, verbatim.

The original note presented `"designed for demonstration purposes only and not intended for production use"` as a quote. It is a paraphrase. The actual text (V13) is a GitHub callout block:

```markdown
> [!IMPORTANT]
> This library is intended for demonstration purposes only. It is not meant to be used in production.
```

Everything else in claim 19 holds: the tool is `skills-ref`; `skills-ref validate ./my-skill` is the spec's own invocation (V1); the three commands are `validate`, `read-properties`, `to-prompt`; it is Python, installed with `pip install -e .` or `uv sync` from a clone, **not** npm and **not** cargo; Apache 2.0.

Details the note missed (V12, V13): `requires-python = ">=3.11"`; dependencies `click>=8.0` and `strictyaml>=1.7.3`; package version `0.1.0`; author `Keith Lazuka <klazuka@anthropic.com>`; build backend `hatchling`; dev group `pytest>=7.0`, `ruff>=0.8.0`. The README also documents a macOS/Linux **uv** path the note omitted:

```bash
uv sync
source .venv/bin/activate
```

and on Windows:

```powershell
uv sync
.venv\Scripts\Activate.ps1
```

#### C20 — The `skills-ref/` file list was incomplete (the conclusion still stands).

The GitHub tree API response (V16) came back with `"truncated": false`, so this is the complete tree. `skills-ref/` actually contains:

```
skills-ref/.gitignore          <- missed by the original note
skills-ref/LICENSE
skills-ref/README.md
skills-ref/pyproject.toml
skills-ref/uv.lock             <- missed by the original note
skills-ref/src/skills_ref/__init__.py
skills-ref/src/skills_ref/cli.py
skills-ref/src/skills_ref/errors.py
skills-ref/src/skills_ref/models.py
skills-ref/src/skills_ref/parser.py
skills-ref/src/skills_ref/prompt.py
skills-ref/src/skills_ref/validator.py
skills-ref/tests/__init__.py
skills-ref/tests/test_parser.py
skills-ref/tests/test_prompt.py
skills-ref/tests/test_validator.py
```

Repo root also has `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `LICENSE`, `README.md`, `package.json`, `.gitignore`, and trees `.claude/` and `docs/`.

**The substantive claim is CONFIRMED: there is no `.json` or `.yaml` schema file anywhere in the repo.** `validator.py` is the executable schema. (Note `uv.lock` exists, so `uv sync` has a pinned resolution — useful if you want a reproducible CI install.)

#### C23 — Framing nuance on the colon gotcha.

The fact is confirmed, but the "quote it or use a block scalar" advice in V3 is addressed to **client implementers building a parse fallback**, not to skill authors. Verbatim (V3):

> Consider a fallback that wraps such values in quotes or converts them to YAML block scalars before retrying. This improves cross-client compatibility at minimal cost.

For LetterLens as an *author*, the actionable rule is the same (quote any description containing a colon, or use a block scalar), but do not expect every client to have implemented the fallback.

---

### Things the researcher missed that the build will need

#### M1 — `read-properties` JSON contract (from `models.py`, V9)

This is the stable machine-readable surface for CI. Verbatim:

```python
    def to_dict(self) -> dict:
        """Convert to dictionary, excluding None values."""
        result = {"name": self.name, "description": self.description}
        if self.license is not None:
            result["license"] = self.license
        if self.compatibility is not None:
            result["compatibility"] = self.compatibility
        if self.allowed_tools is not None:
            result["allowed-tools"] = self.allowed_tools
        if self.metadata:
            result["metadata"] = self.metadata
        return result
```

- `name` and `description` are **always** present.
- `license`, `compatibility`, `allowed-tools` appear **only when non-None**. Do not assume the keys exist.
- `metadata` appears **only when non-empty** (falsy check, not a None check) and defaults to `{}`.
- The JSON key is **`allowed-tools`** (hyphen) even though the Python attribute is `allowed_tools`. `parser.py` reads it as `allowed_tools=metadata.get("allowed-tools")`.
- `name` and `description` are `.strip()`ped by `read_properties` before being stored.

#### M2 — `to_prompt` output format differs from the docs page. The code is authoritative.

The original note recorded only the V3 flavour (indented, values inline). `prompt.py` emits something different — **each value on its own line** (V10):

```python
        lines.append("<skill>")
        lines.append("<name>")
        lines.append(html.escape(props.name))
        lines.append("</name>")
        lines.append("<description>")
        lines.append(html.escape(props.description))
        lines.append("</description>")

        skill_md_path = find_skill_md(skill_dir)
        lines.append("<location>")
        lines.append(str(skill_md_path))
        lines.append("</location>")

        lines.append("</skill>")
```

Matching README example (V13):

```xml
<available_skills>
<skill>
<name>
my-skill
</name>
<description>
What this skill does and when to use it
</description>
<location>
/path/to/my-skill/SKILL.md
</location>
</skill>
</available_skills>
```

Also: `name` and `description` are **HTML-escaped** (`html.escape`); `location` is **not**. Paths are `Path(skill_dir).resolve()`d, so output is absolute. Empty input returns exactly `"<available_skills>\n</available_skills>"`. Note the docstring inside `prompt.py` shows the *inline* form (`<name>pdf-reader</name>`) and contradicts the code it documents — trust the code. If LetterLens parses this block, parse it loosely.

#### M3 — Frontmatter delimiter parsing is naive. Two author-facing traps.

Verbatim (V7):

```python
    if not content.startswith("---"):
        raise ParseError("SKILL.md must start with YAML frontmatter (---)")

    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ParseError("SKILL.md frontmatter not properly closed with ---")

    frontmatter_str = parts[1]
    body = parts[2].strip()
```

- `content.startswith("---")` is byte-literal. A **UTF-8 BOM**, a leading blank line, or a leading comment makes the file invalid. Write `SKILL.md` as BOM-less UTF-8 with `---` on line 1, column 1. (Relevant on Windows: PowerShell `Out-File`/`>` often emits a BOM. Use `Set-Content -Encoding utf8NoBOM` or write via the Write tool.)
- `split("---", 2)` with `maxsplit=2` means a `---` horizontal rule in the **body** is safe, but a `---` inside the frontmatter block is not.
- `body = parts[2].strip()` — leading/trailing body whitespace is discarded.

#### M4 — Error hierarchy, and `validate()` vs `read_properties()` behave differently

`errors.py` verbatim (V11):

```python
class SkillError(Exception):
    """Base exception for all skill-related errors."""

class ParseError(SkillError):
    """Raised when SKILL.md parsing fails."""

class ValidationError(SkillError):
    """Raised when skill properties are invalid.

    Attributes:
        errors: List of validation error messages (may contain just one)
    """
    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors if errors is not None else [message]
```

- `validate(Path)` **returns a list** and never raises for ordinary problems; it catches `ParseError` and returns `[str(e)]`.
- `read_properties(Path)` **raises** — `ParseError` for a missing file or bad YAML, `ValidationError` for a missing or empty `name`/`description`. It explicitly does *not* do full validation: *"This function parses the frontmatter and returns properties. It does NOT perform full validation. Use validate() for that."* (V7)
- `cli.py` catches only `SkillError` in `read-properties` and `to-prompt`.

#### M5 — `validate()` accumulates all errors, except for four early returns

Verbatim control flow (V6): `validate()` returns a single-element list immediately for (1) path missing, (2) not a directory, (3) no SKILL.md, (4) parse error. Otherwise `validate_metadata()` accumulates every problem. **The unexpected-fields check runs first**, so it is always error #1 in the list when present. A skill with five problems reports five lines — do not write CI that only reads the first.

#### M6 — Two docs pages the original note never listed

`llms.txt` (V2) has nine pages. The note's source table covered six of them and never recorded:

- https://agentskills.io/skill-creation/evaluating-skills.md — "How to test whether your skill produces good outputs using eval-driven iteration."
- https://agentskills.io/skill-creation/using-scripts.md — "How to run commands and bundle executable scripts in your skills."
- https://agentskills.io/clients.md — "Agent products that support the Agent Skills format."

If LetterLens ships a skill with `scripts/`, `using-scripts.md` is the page to read and **neither pass has read it**. Flagged, not summarized.

#### M7 — There is a published skill that automates description tuning

Verbatim (V5):

> The [`skill-creator`](https://github.com/anthropics/skills/tree/main/skills/skill-creator) Skill automates this loop end-to-end: it splits the eval set, evaluates trigger rates in parallel, proposes description improvements using Claude, and generates a live HTML report you can watch as it runs.

V5 also gives a complete runnable bash trigger-eval harness (jq plus `claude -p --output-format json`, detecting `tool_use` where `.name == "Skill"` and `.input.skill == $skill`), a 20-query / 8-10-each eval-set recipe, 3 runs per query, a 0.5 trigger-rate threshold, and a 60/40 train/validation split to avoid overfitting. If LetterLens cares whether its skill actually fires, that page is the method — the original note captured only the four writing principles from it.

#### M8 — Client guidance the note omitted that affects where LetterLens puts its skill

From V3:

- **Trust gating:** *"Project-level skills come from the repository being worked on, which may be untrusted... Consider gating project-level skill loading on a trust check — only load them if the user has marked the project folder as trusted."* A project-level LetterLens skill may silently not load in an untrusted folder.
- **Scan bounds:** *"Set reasonable bounds (e.g., max depth of 4-6 levels, max 2000 directories)"* and skip `.git/` and `node_modules/`. Keep the skill shallow.
- **Minimum stored record** is three fields: `name`, `description`, `location` (absolute path to `SKILL.md`).
- **Filtered skills are hidden entirely** from the catalog rather than listed-and-blocked.
- **Frontmatter may or may not reach the model.** *"Among existing implementations with dedicated activation tools, most take this approach — stripping the frontmatter after extracting `name` and `description` during discovery."* So **do not put instructions in frontmatter and expect the model to read them.** Anything the model must act on belongs in the body.

---

### Revised blockers

1. **Install location** — original blocker **stands, CONFIRMED verbatim.** Use `.agents/skills/<name>/SKILL.md` for portability and `.claude/skills/<name>/SKILL.md` for Claude Code. A bare `skills/` directory is documented nowhere.
2. **No top-level `version:`** — original blocker **stands**, but for the right reason. It is invalid because it is outside `ALLOWED_FIELDS`, not because of float coercion. And write `metadata:` in **block style**, not the inline `{ version: "1.0" }` form the original blocker used.
3. **No JSON Schema, no PyPI package** — **stands, CONFIRMED.** Git clone plus `pip install -e .` or `uv sync` from `skills-ref/`. `uv.lock` is present if you want pinned CI.
4. **"Exit codes undocumented, assert on stdout"** — **REVERSED.** Exit codes are documented in `cli.py`: 0 pass, 1 validation errors, and Click adds 2 for a nonexistent path. `skills-ref validate` is safe as a CI gate on exit status. Problems print to **stderr**, not stdout.
5. **Size limits unenforced** — **stands, CONFIRMED.** 500 lines and ~5,000 tokens are recommendations in prose only; nothing in `validator.py` counts lines, tokens or words. Write the check yourself if you want it.
6. **Strict vs lenient conformance diverge** — **stands, CONFIRMED verbatim**, and it is worse than described: `skills-ref` accepts lowercase `skill.md` and Unicode names that a strict reading of the spec would reject, while shipping clients accept name/directory mismatches that `skills-ref` rejects. **Neither bar is a superset of the other.** Author to the intersection: uppercase `SKILL.md`, ASCII kebab-case `name` matching the directory, a non-empty `description` (quoted if it contains a colon), and nothing outside the six fields.
7. **NEW — the YAML parser is `strictyaml`.** Block style only; assume no flow mappings, no anchors, no aliases; every scalar comes back a string. The specific flow-style failure is **unverified** — confirm locally before relying on it either way.
