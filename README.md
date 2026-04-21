# 🔐 Password Strength Analyzer

A client-side-safe, feature-rich password strength analyzer built with Python (Flask) and a dark cybersecurity-themed UI.

## Features

- **Entropy Analysis** — Real bit-level entropy calculation based on charset size and length
- **Strength Rating** — Very Weak → Weak → Fair → Strong → Very Strong
- **Crack-time Estimates** — Online throttled, unthrottled, offline slow hash, and GPU scenarios
- **Composition Detection** — Detects lowercase, uppercase, digits, symbols, and unicode usage
- **Pattern Detection** — Keyboard walks, repeated characters, sequences, date patterns, leet speak
- **Dictionary Attack Simulation** — Checks against common passwords including leetspeak normalization
- **Smart Suggestions** — Actionable tips to improve password strength
- **Password Generator** — Generates cryptographically strong passwords
- **Copy & Show/Hide** — Easy clipboard copy and visibility toggle

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
python app.py
```

### 3. Open in browser
```
http://localhost:5000
```

## Project Structure

```
password_analyzer/
├── app.py              # Flask backend with all analysis logic
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── templates/
    └── index.html      # Frontend UI
```

## How it Works

| Component | Description |
|-----------|-------------|
| `calculate_entropy()` | `length × log₂(charset_size)` |
| `shannon_entropy()` | Character frequency-based entropy |
| `detect_patterns()` | Keyboard adjacency graph, regex patterns |
| `dictionary_check()` | Set lookup + leet normalization |
| `crack_times()` | Divides guess space by attack speed |
| `get_strength()` | Entropy with penalty deductions |
