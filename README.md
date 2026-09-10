# IndVarLTL

IndVarLTL is a research prototype for decomposing Boolean variables in Linear
Temporal Logic (LTL) formulas. It uses repeated satisfiability/model-checking
queries to identify groups of system variables that depend on one another and
can therefore be handled independently of the other groups.

Environment variables are treated as shared inputs: they influence the
decomposition but are not included in the resulting system-variable groups.

## Current capabilities

- Parse propositional formulas and LTL formulas over Boolean variables.
- Partition variables with either [NuSMV](https://nusmv.fbk.eu/) or
  [Aalta](https://github.com/lijwen2748/aalta) as the back-end solver.
- Read a formula interactively or from a multiline text file.
- Write file-based results to the `results/` directory.
- Derive formula components for propositional and supported temporal formulas.
- Certify temporal components by checking both directions of LTL equivalence.

For LTL input, extraction uses the known output partition, exact rewriting,
context propagation, and whole-formula polarity analysis. Extraction is sound
when certified but incomplete: some independent partitions may not yield LTL
components with the implemented rules.

## Requirements

- Python 3
- `parsimonious==0.10.0` (installed through `requirements.txt`)
- One external solver:
  - NuSMV on macOS or Linux; or
  - Aalta on macOS or Linux

Windows is not supported by the current command-line entry point. NuSMV is the
default on macOS; either solver can be selected explicitly with `--solver`.

## Installation

Clone the repository and install the Python dependency in a virtual
environment:

```bash
git clone https://github.com/Josuoehu/IndVarLTL.git
cd IndVarLTL
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Install NuSMV or Aalta separately and make sure its executable is available on
your `PATH`. The expected executable names are `NuSMV` and `aalta`,
respectively.

Aalta can be downloaded from its official source repository:

- [Aalta source code on GitHub](https://github.com/lijwen2748/aalta)

To build it from source:

```bash
git clone https://github.com/lijwen2748/aalta.git
cd aalta
make release
```

## Quick start

Run the command from the repository root:

```bash
python scripts/general.py -f files/running_example.txt
```

On Linux, select NuSMV or Aalta when prompted. On macOS, NuSMV is selected by
default. The tool then prints the decomposition and asks whether another formula
should be processed.

Select a backend explicitly on either platform with `--solver`:

```bash
python scripts/general.py --solver nusmv -f files/running_example.txt
python scripts/general.py --solver aalta -f files/running_example.txt
```

For the included `running_example.txt`, the variable decomposition is:

```text
[['v', 'u', 'w'], ['t']]
```

Because a file was supplied, the same result is written to
`results/running_example_r.txt`.

### Interactive input

Run the program without `-f` to enter a one-line formula at the prompt:

```bash
python scripts/general.py
```

For a temporal formula, the program also asks for its environment variables.
Enter a comma-separated list such as `request,reset`, or enter `-` if there are
none.

## Input format

An input file contains a formula, optionally split across several lines. For a
temporal formula, environment variables may be declared on the final line:

```text
G((p -> X(v & !t)) &
  (!p -> X(!v & t)) &
  (v -> X(!w & u)) &
  (!v -> X(w & !u)))
env_vars: p
```

If the `env_vars:` line is omitted, the program asks for the environment
variables interactively. Variable names should use lowercase letters, digits,
and underscores.

### Supported operators

| Meaning | Syntax |
| --- | --- |
| Negation | `!p` or `~p` |
| Conjunction | `p & q` or `p && q` |
| Disjunction | `p \| q` or `p \|\| q` |
| Implication | `p -> q` |
| Equivalence | `p <-> q` |
| Next | `X(p)` |
| Eventually | `F(p)` |
| Globally | `G(p)` |

Temporal operators must be followed by a parenthesized expression. Binary
temporal operators such as Until (`U`) and Release (`R`) are not currently
supported.

## Output

Every run prints the variable decomposition. For propositional formulas, it
also prints the formula decomposition:

- **Variable decomposition**: lists of variables that belong to the same
  dependent component.
- **Formula decomposition**: simplified components for propositional input.

For LTL input, the output includes an extraction status:

- `certified`: both implication directions were explicitly proved by the solver.
- `incomplete`: candidate formulas do not reconstruct the original; a witness is
  included. This does not establish that the supplied groups are dependent.
- `unknown`: the solver failed or did not return an explicit answer.

Uncertified formulas are labeled as candidates, including in saved results.

When `-f FILE` is used, the program also creates
`results/<input-name>_r.txt`. Interactive input is printed only to the terminal.

## Solver discovery

On its first run, IndVarLTL searches the shell `PATH` for the selected solver
and generates a local launcher (`scripts/call_nusmv.sh` or
`scripts/call_aalta.sh`). This supports standard package-manager locations such
as Homebrew's `/opt/homebrew/bin`. The launchers are machine-specific and
intentionally ignored by Git.

If the executable is not on `PATH`, the original filesystem search is used as a
fallback. It checks `/Users` and `/bin` on macOS, or `/home` and `/bin` on
Linux. If neither method finds the solver, create the appropriate launcher
manually.

For NuSMV:

```bash
#!/usr/bin/env bash
"/absolute/path/to/NuSMV" -int "$2" <<< "$1"
```

For Aalta:

```bash
#!/usr/bin/env bash
cat "$1" | "/absolute/path/to/aalta" -e > "$2"
```

Save the file in `scripts/` with the name shown above and make it executable:

```bash
chmod +x scripts/call_nusmv.sh  # or scripts/call_aalta.sh
```

## Repository layout

```text
IndVarLTL/
├── files/          Example input formulas
├── results/        Saved decompositions for file-based runs
├── scripts/        Parser, decomposition algorithm, and CLI entry point
├── smv/            Example SMV model
└── source/         Sphinx documentation sources
```

## Project status

IndVarLTL is an experimental research tool, not a production-ready library.
The CLI is interactive and solver integration uses generated shell scripts.
See the examples in `files/` for the formulas accepted by the current parser.

Run the regression tests with:

```bash
python -m unittest discover -s tests -v
```

## Temporal component extraction

The program first rewrites conjunctions under `G`, `X`, and implications, and
assigns requirements to the known output groups. For remaining mixed
requirements, it retains assigned requirements as context. Current-state facts
never cross a temporal operator. Global conjuncts `G(p)` or `G(!p)` can constrain
other requirements throughout the future, while retaining their justification.
For example, `G(b) & G(a | !b)` yields `G(a)` and `G(b)`.

For each group, remaining foreign outputs with a single polarity in the **whole
simplified formula** can be eliminated exactly: positive signals become true,
negative signals become false. Mixed-polarity signals are not eliminated this
way. Local consequences are collected and their complete conjunction is checked
against the original formula. There is no approximate literal-erasure step.
The AST API reserves `true`/`false` (also uppercase) for Boolean constants.

The Python API, with `scripts/` on the import path, is:

```python
from ltl_decompose import decompose_ltl

result = decompose_ltl(
    'G(b) & G(a | !b)',
    env_vars=[],
    independent_groups=[['a'], ['b']],
    solver='nusmv',
)
# result.status == 'certified'
# result.components == ['G(a)', 'G(b)']
```

Input-only obligations are retained in every component. With no outputs, the
result contains one input-only obligation. The certificate preserves realizability
under synchronous synthesis with the original inputs observable to every
component, disjoint controlled outputs, and the same Mealy/Moore convention.
It does not decide realizability or synthesize controllers.

The extractor supports the existing Boolean/X/F/G fragment. It does not infer
arbitrary temporal invariants or guarantee extraction for every independent
partition. NuSMV/Aalta launchers must already be configured (the CLI configures
them normally). Semantic tests run with NuSMV when its executable and launcher
are available; otherwise those integration tests are skipped.
