# Prepare MIWBS for GitHub

**Important:** `C:\Builds` currently has a messy parent git state (many staged paths).  
**Do not** push `C:\Builds` as the MIWBS repo. This folder (`miwbs/`) should be its **own** git repository.

## One-time local setup

From PowerShell:

```powershell
cd C:\Builds\miwbs

# 1) Own repo (nested .git — fine; parent Builds should not track this)
git init

# 2) Confirm ignore rules (worlds/, __pycache__, egg-info, …)
#    File: .gitignore already in tree

# 3) Stage product files only
git add .gitignore README.md GITHUB.md pyproject.toml requirements.txt
git add docs/ src/miwbs/ tests/ scripts/
# Do NOT add worlds/*.db or __pycache__

git status
# Review: no .world.db, no egg-info, no pyc

# 4) First commit
git commit -m "Initial MIWBS: mentalor Day of Days, Cycle·node, studio modal"
```

## Create the remote (GitHub)

**Option A — GitHub CLI** (if `gh` is logged in):

```powershell
cd C:\Builds\miwbs
gh repo create miwbs --private --source=. --remote=origin --description "MIWBS — Multidimensional Interactive World Builder Studio"
git push -u origin main
```

Use `--public` if you want it public. Change `miwbs` to your preferred repo name.

**Option B — website**

1. github.com → New repository → name e.g. `miwbs` → empty (no README).
2. Then:

```powershell
cd C:\Builds\miwbs
git branch -M main
git remote add origin https://github.com/YOUR_USER/miwbs.git
git push -u origin main
```

## What to publish vs keep local

| Publish | Keep local only |
|---------|-----------------|
| `src/miwbs/`, `tests/`, `docs/` | `worlds/*.world.db` |
| `README.md`, `pyproject.toml` | personal Day of Days playthroughs |
| `GITHUB.md` (optional later) | `.env`, secrets |

## Sanity check before push

```powershell
cd C:\Builds\miwbs
py -3.12 -m pip install -e . -q
py -3.12 -m unittest discover -s tests -q
git status   # clean after commit
```

## Optional polish later

- [ ] LICENSE (MIT / your choice)
- [ ] GitHub Actions: run `unittest` on push
- [ ] Tag `v0.1.0` when Day of Days feels playable
- [ ] Separate private repo for world DBs if you ever want backup (not this code repo)

## Parent `C:\Builds` git

If you use a monorepo later, that’s a different decision. For now, treat **MIWBS = this directory’s `.git` only**. Unstage or ignore `miwbs/` from any parent repo so it doesn’t double-track.
