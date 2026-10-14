## Setting up a Z3 Environment in VSCode

This guide walks through creating a Python virtual environment (`z3env`) and installing the Z3 SAT/SMT solver (`z3-solver`) using the built-in VSCode terminal.

## Prerequisites

- [VSCode](https://code.visualstudio.com/) installed
- Python 3.8+ installed and available on your system PATH
- The VSCode [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python) installed

Check your Python version first:

```bash
python3 --version
```

(On Windows, this may just be `python --version` — see the Windows notes below.)

## 1. Open the integrated terminal

In VSCode, open the terminal with:

- **Menu:** Terminal → New Terminal
- **Shortcut:** `` Ctrl+` `` (Windows/Linux) or `` Cmd+` `` (Mac)

Make sure the terminal is opened in your project's root folder.

## 2. Create the virtual environment

From the project folder, run:

**macOS / Linux:**
```bash
python3 -m venv z3env
```

**Windows:**
```bash
python -m venv z3env
```

This creates a `z3env/` folder in your project directory containing an isolated Python installation.

## 3. Activate the virtual environment

**macOS / Linux:**
```bash
source z3env/bin/activate
```

**Windows (PowerShell):**
```powershell
z3env\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
z3env\Scripts\activate.bat
```

Once activated, your terminal prompt should be prefixed with `(z3env)`, confirming the environment is active.

> **Note (Windows PowerShell):** If you get a script-execution error, run this once in an admin PowerShell, then retry activation:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

## 4. Install the Z3 solver

With `z3env` active, install the `z3-solver` package via pip:

```bash
pip install z3-solver
```

This installs the Python bindings for Z3 (Microsoft's theorem prover), including the `z3` module.

## 5. Verify the installation

Run a quick sanity check:

```bash
python -c "from z3 import *; x = Int('x'); s = Solver(); s.add(x > 5); print(s.check(), s.model())"
```

Expected output:

```
sat [x = 6]
```

If you see `sat` along with a model, Z3 is installed and working correctly.

## 6. Point VSCode to the new environment

So that VSCode's editor (IntelliSense, debugging, etc.) uses `z3env` too:

1. Open the Command Palette: `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
2. Type and select **Python: Select Interpreter**
3. Choose the interpreter located at `./z3env/bin/python` (macOS/Linux) or `.\z3env\Scripts\python.exe` (Windows)

VSCode will now use `z3env` for running and debugging scripts in this workspace.

## 7. Deactivating the environment

When you're done working, deactivate with:

```bash
deactivate
```

## Quick reference

| Step | Command (macOS/Linux) | Command (Windows) |
|---|---|---|
| Create env | `python3 -m venv z3env` | `python -m venv z3env` |
| Activate | `source z3env/bin/activate` | `z3env\Scripts\activate` |
| Install Z3 | `pip install z3-solver` | `pip install z3-solver` |
| Deactivate | `deactivate` | `deactivate` |

## Troubleshooting

- **`pip: command not found`** — try `pip3` instead, or ensure the venv is activated (activation should automatically put the right `pip` on your PATH).
- **VSCode terminal doesn't show `(z3env)`** — close and reopen the terminal after creating the venv, or re-run the activate command.
- **Wrong Python version used in scripts** — double check the interpreter selected in Step 6 matches the `z3env` path.