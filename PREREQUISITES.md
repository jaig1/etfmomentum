# Prerequisites for Using ETF Momentum Package

## ⚠️ Mandatory Requirements

Before installing or using this package in any project, you **MUST** satisfy these prerequisites:

---

## 1. FMP API Key (REQUIRED)

### What is it?
Financial Modeling Prep (FMP) API key for fetching historical ETF price data.

### Why is it required?
- ✅ The package checks for this key **immediately on import**
- ❌ Without it, the package will **fail to load** with an error
- 🔒 This is **by design** - ensures every user provides their own key

### How to get it
1. Visit: https://financialmodelingprep.com/developer/docs/
2. Sign up for a free or paid account
3. Copy your API key

### Free vs Paid
- **Free tier:** Limited requests, basic data
- **Premium tier:** 3000 calls/min, 30 years of historical data (recommended)

---

## 2. Setting Up the API Key

You have **two options** to provide the API key:

### Option A: .env File (Recommended)

Create a `.env` file in your project directory:

```bash
# In your project directory
echo "FMP_API_KEY=your_actual_key_here" > .env

# IMPORTANT: Add .env to .gitignore to keep it private
echo ".env" >> .gitignore
```

**Verification:**
```bash
# Check .env exists
cat .env

# Should show:
# FMP_API_KEY=your_actual_key_here
```

### Option B: Environment Variable

Export the key in your shell:

```bash
# Temporary (current session only)
export FMP_API_KEY="your_actual_key_here"

# Permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export FMP_API_KEY="your_actual_key_here"' >> ~/.bashrc
source ~/.bashrc
```

**Verification:**
```bash
echo $FMP_API_KEY
# Should print your key
```

---

## 3. Python Requirements

- **Python version:** >= 3.11
- **Dependencies:** Will be installed automatically via pip/uv

---

## 4. Installation Methods

Choose one based on your use case:

### Option 1: Local Editable Install (Development)
```bash
cd /path/to/your/project
pip install -e /Users/jaig/etfmomentum
```

### Option 2: Git Repository Install (Distribution)
```bash
pip install git+https://github.com/user/etfmomentum.git@v0.1.0
```

---

## Pre-Installation Checklist

Before running `pip install`, verify:

- [ ] **FMP API key obtained** from financialmodelingprep.com
- [ ] **API key set** via `.env` file OR environment variable
- [ ] **.env file added** to `.gitignore` (if using .env)
- [ ] **Python 3.11+** installed
- [ ] **Current directory** is your target project

---

## What Happens Without API Key

If you try to import without the key:

```python
import etfmomentum  # ❌ This will fail!
```

**Error you'll see:**
```
ValueError:
======================================================================
❌ PREREQUISITE ERROR: FMP_API_KEY not found
======================================================================
This package requires a Financial Modeling Prep API key.

To fix this, create a .env file in your project directory:

  1. Create .env file:
     echo 'FMP_API_KEY=your_key_here' > .env

  2. OR export environment variable:
     export FMP_API_KEY='your_key_here'

Get a free API key at: https://financialmodelingprep.com/developer/docs/
======================================================================
```

---

## Quick Setup Guide (2 Minutes)

### For New Users

**Step 1: Get API Key**
```bash
# Visit and sign up
open https://financialmodelingprep.com/developer/docs/
```

**Step 2: Set Up Your Project**
```bash
# Navigate to your project
cd /path/to/your/project

# Create .env file with your key
echo "FMP_API_KEY=paste_your_key_here" > .env

# Keep it private
echo ".env" >> .gitignore
```

**Step 3: Install Package**
```bash
# Install etfmomentum
pip install -e /Users/jaig/etfmomentum

# Test it works
python -c "import etfmomentum; print('✓ Success!')"
```

**Done!** You can now use the package.

---

## Verification Script

Run this to check all prerequisites:

```bash
python /Users/jaig/etfmomentum/test_installation.py
```

**Expected output:**
```
✅ PASS: Imports
✅ PASS: Config
✅ PASS: Universe
✅ PASS: Environment
```

If you see **❌ FAIL: Environment**, your API key is not set correctly.

---

## Team Setup

If you're setting this up for a team:

### Each Team Member Must:
1. ✅ Get their own FMP API key (or use shared key)
2. ✅ Create their own `.env` file locally
3. ✅ **Never commit** `.env` to git
4. ✅ Install the package: `pip install -e /path` or from git

### Sharing Keys (If Needed)
```bash
# Share via secure channel (Slack DM, 1Password, etc.)
# Each person creates their own .env file locally
# DO NOT commit shared keys to version control!
```

---

## Troubleshooting

### "FMP_API_KEY not found" error

**Check 1: Does .env exist?**
```bash
ls -la .env
cat .env
```

**Check 2: Is it in the right directory?**
```bash
# .env should be in the directory where you run python
pwd
ls .env
```

**Check 3: Is the format correct?**
```bash
# Should be exactly:
FMP_API_KEY=your_key_here

# NOT:
FMP_API_KEY = your_key_here  # ❌ Spaces
FMP_API_KEY="your_key_here"  # ❌ Quotes (optional but can cause issues)
```

**Check 4: Environment variable set?**
```bash
echo $FMP_API_KEY
# Should print your key
```

### "Module not found" error

```bash
# Reinstall the package
pip uninstall etfmomentum
pip install -e /Users/jaig/etfmomentum
```

### Still having issues?

```bash
# Run the verification script
python /Users/jaig/etfmomentum/test_installation.py

# Check detailed error
python -c "import etfmomentum"
```

---

## Summary

| Requirement | Status | How to Verify |
|-------------|--------|---------------|
| FMP API Key | **MANDATORY** | `echo $FMP_API_KEY` |
| .env file OR export | **ONE REQUIRED** | `cat .env` or `echo $FMP_API_KEY` |
| Python 3.11+ | Required | `python --version` |
| Package installed | Required | `pip show etfmomentum` |

**Without the API key, the package will not work. This is by design.** 🔒
