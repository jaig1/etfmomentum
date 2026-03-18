# FMP API Key Management Guide

## ⚠️ STRICT REQUIREMENT: API Key is Mandatory

**This package will NOT work without an FMP API key.**

The key is checked immediately on import and will raise an error if not found.
This is **by design** - every project using this package must provide their own key.

---

## 🔒 Security: .env is NOT Included in Git

Your `.env` file is properly protected:

```gitignore
# Line 46 in .gitignore
.env
```

✅ **The .env file will NOT be pushed to GitHub**
✅ **Your API key stays private**
✅ **Safe to use Option 2 (Git install)**

---

## How API Keys Work with Option 2

### What Happens

When someone installs from GitHub:

```bash
pip install git+https://github.com/user/etfmomentum.git
```

**They get:**
- ✅ All Python code
- ✅ Configuration files
- ✅ ETF lists (CSV files)

**They DON'T get:**
- ❌ Your `.env` file
- ❌ Your FMP_API_KEY
- ❌ Any cached data

### What Each Project Needs to Provide

**Every project using your module MUST provide their own FMP API key.**

---

## Three Ways to Provide the API Key

### Option A: Create .env File in Their Project (Recommended)

```bash
# In the other project directory
echo "FMP_API_KEY=their_key_here" > .env
```

Then the key is automatically loaded when they import:
```python
from etfmomentum import generate_current_signals

# Works! Loads FMP_API_KEY from .env
signals = generate_current_signals(universe='sp500')
```

### Option B: Export Environment Variable

```bash
# Set in shell
export FMP_API_KEY="their_key_here"

# Or in their project's .bashrc / .zshrc
echo 'export FMP_API_KEY="their_key_here"' >> ~/.bashrc
```

### Option C: Load from Specific Path

```python
from dotenv import load_dotenv
import os

# Load from specific location
load_dotenv('/path/to/.env')

# Or set programmatically
os.environ['FMP_API_KEY'] = 'their_key_here'

# Now import etfmomentum
from etfmomentum import generate_current_signals
```

---

## Current Behavior (Potential Issue)

Your current `config.py` has this:

```python
FMP_API_KEY = os.getenv("FMP_API_KEY")
if not FMP_API_KEY:
    raise ValueError("FMP_API_KEY not found in .env file. Please set it up.")
```

**Problem:** This raises an error **immediately on import**, even if they don't need the API yet.

### Example of the Problem

```python
# This will fail even if they just want to check the version
import etfmomentum  # ❌ ValueError: FMP_API_KEY not found!
print(etfmomentum.__version__)
```

---

## Recommended Fix: Lazy Loading

Make the API key optional on import, only required when actually fetching data:

```python
# config.py - Better approach
FMP_API_KEY = os.getenv("FMP_API_KEY")

def get_api_key():
    """Get API key, raising error only when actually needed."""
    if not FMP_API_KEY:
        raise ValueError(
            "FMP_API_KEY not found in environment.\n"
            "Please set it in one of these ways:\n"
            "  1. Create .env file with: FMP_API_KEY=your_key\n"
            "  2. Export: export FMP_API_KEY=your_key\n"
            "  3. Set in code: os.environ['FMP_API_KEY'] = 'your_key'"
        )
    return FMP_API_KEY
```

Then in `data_fetcher.py`:

```python
def get_price_data(..., api_key=None):
    if api_key is None:
        api_key = config.get_api_key()  # Only fails here, not on import
    ...
```

This allows:
```python
# ✅ Works - no API calls yet
import etfmomentum
print(etfmomentum.__version__)

# ❌ Fails only when trying to fetch data
from etfmomentum import get_price_data
data = get_price_data(...)  # Now raises error about missing key
```

---

## Documentation for Other Project Users

### In Your README or INSTALL Guide

```markdown
## Setup API Key

ETF Momentum requires a Financial Modeling Prep (FMP) API key.

1. Get a free API key: https://financialmodelingprep.com/developer/docs/
2. Set it in your project:

**Option 1: Create .env file (recommended)**
\```bash
echo "FMP_API_KEY=your_key_here" > .env
\```

**Option 2: Export environment variable**
\```bash
export FMP_API_KEY="your_key_here"
\```

**Option 3: Set in code**
\```python
import os
os.environ['FMP_API_KEY'] = 'your_key_here'

from etfmomentum import generate_current_signals
\```
```

---

## Sharing API Keys (Team Scenario)

### Option 1: Each Team Member Has Their Own Key (Recommended)
```bash
# Each person creates their own .env
echo "FMP_API_KEY=person1_key" > .env
```

✅ **Pros:** Individual usage tracking, revocable
❌ **Cons:** Everyone needs their own key

### Option 2: Shared Key via Secrets Manager (Production)
```python
# Use AWS Secrets Manager, 1Password, etc.
import boto3

def get_api_key():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='FMP_API_KEY')
    return response['SecretString']
```

✅ **Pros:** Centralized, auditable, secure
❌ **Cons:** Requires infrastructure

### Option 3: Shared .env (Dev Only, Not Committed)
```bash
# Share via secure channel (Slack, 1Password)
# Each person copies to their local .env
# NEVER commit to git!
```

⚠️ **Warning:** Don't commit shared keys to git

---

## Example: Complete Setup for New User

### Scenario: Team member wants to use your package

**Step 1: Install the package**
```bash
pip install git+https://github.com/user/etfmomentum.git@v0.1.0
```

**Step 2: Get FMP API key**
- Sign up at https://financialmodelingprep.com/
- Copy their API key

**Step 3: Create .env file**
```bash
cd /path/to/their/project
echo "FMP_API_KEY=abc123xyz" > .env
```

**Step 4: Add .env to their .gitignore**
```bash
echo ".env" >> .gitignore
```

**Step 5: Use the package**
```python
from etfmomentum import generate_current_signals

# Works! Uses their API key
signals = generate_current_signals(universe='sp500')
```

---

## Security Best Practices

### ✅ DO

- Keep .env in .gitignore
- Each environment has its own .env file
- Use secrets manager for production
- Rotate keys periodically
- Document key setup in README

### ❌ DON'T

- Commit .env to git
- Hardcode API keys in code
- Share keys in public channels
- Use production keys in development

---

## Testing Without Real API Key

For testing/development, you might want to support mock data:

```python
# config.py
FMP_API_KEY = os.getenv("FMP_API_KEY")
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "false").lower() == "true"

# data_fetcher.py
def get_price_data(...):
    if config.USE_MOCK_DATA:
        return load_mock_data()  # Load from test fixtures
    else:
        api_key = config.get_api_key()  # Only require key for real data
        return fetch_from_fmp(api_key)
```

Then users can test without a key:
```bash
export USE_MOCK_DATA=true
python test_script.py  # Works without FMP_API_KEY
```

---

## Summary

**With Option 2 (Git Install):**

| Item | Status | Notes |
|------|--------|-------|
| `.env` file | ❌ NOT included | In .gitignore |
| Your API key | ❌ NOT shared | Stays private |
| Code | ✅ Included | Public in repo |
| User must provide key | ✅ YES | Via .env or export |

**Each project using your module must:**
1. ✅ Have their own FMP API key
2. ✅ Set it via .env file or environment variable
3. ✅ Keep their .env file in .gitignore

**Your .env file is safe and will NOT be pushed to GitHub!** ✅
