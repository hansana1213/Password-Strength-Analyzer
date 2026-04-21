from flask import Flask, render_template, request, jsonify
import math
import re
import string
import random
import json

app = Flask(__name__)

# Common passwords dictionary (subset for demonstration)
COMMON_PASSWORDS = {
    "password", "123456", "password1", "qwerty", "abc123", "letmein",
    "monkey", "dragon", "master", "sunshine", "princess", "welcome",
    "shadow", "superman", "michael", "football", "baseball", "iloveyou",
    "trustno1", "jennifer", "hunter", "buster", "soccer", "harley",
    "batman", "andrew", "tiger", "ranger", "joshua", "1234567890",
    "passw0rd", "admin", "login", "hello", "charlie", "donald",
    "password123", "qwerty123", "12345678", "1234567", "111111",
    "1234", "123123", "654321", "666666", "121212", "000000",
    "google", "youtube", "facebook", "twitter", "linkedin", "instagram",
    "mustang", "access", "hockey", "dallas", "jessica", "wizard",
    "magic", "silver", "summer", "jordan", "jessica", "freedom",
}

# Keyboard adjacency for pattern detection
KEYBOARD_ROWS = [
    "qwertyuiop", "asdfghjkl", "zxcvbnm",
    "QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM",
    "1234567890", "!@#$%^&*()"
]

def build_adjacency():
    adj = {}
    for row in KEYBOARD_ROWS:
        for i, ch in enumerate(row):
            neighbors = set()
            if i > 0: neighbors.add(row[i-1])
            if i < len(row)-1: neighbors.add(row[i+1])
            adj.setdefault(ch, set()).update(neighbors)
    return adj

KEYBOARD_ADJ = build_adjacency()

def get_charset_size(password):
    size = 0
    has_lower = bool(re.search(r'[a-z]', password))
    has_upper = bool(re.search(r'[A-Z]', password))
    has_digit = bool(re.search(r'\d', password))
    has_symbol = bool(re.search(r'[^a-zA-Z0-9]', password))
    has_unicode = any(ord(c) > 127 for c in password)
    if has_lower: size += 26
    if has_upper: size += 26
    if has_digit: size += 10
    if has_symbol: size += 32
    if has_unicode: size += 64
    return size, has_lower, has_upper, has_digit, has_symbol, has_unicode

def calculate_entropy(password):
    charset, *_ = get_charset_size(password)
    if charset == 0 or len(password) == 0:
        return 0.0
    return len(password) * math.log2(charset)

def shannon_entropy(password):
    if not password:
        return 0.0
    freq = {}
    for c in password:
        freq[c] = freq.get(c, 0) + 1
    total = len(password)
    return -sum((f/total) * math.log2(f/total) for f in freq.values())

def raw_entropy(password):
    return len(password) * math.log2(256) if password else 0.0

def estimate_guesses(entropy):
    return 10 ** (entropy / math.log2(10)) if entropy > 0 else 1

def crack_times(guesses):
    scenarios = {
        "Online · throttled (100/hr)": guesses / (100 / 3600),
        "Online · unthrottled (10/s)": guesses / 10,
        "Offline · slow hash (10⁴/s)": guesses / 10_000,
        "Offline · GPU (10¹⁰/s)": guesses / 10_000_000_000,
    }
    results = {}
    for label, seconds in scenarios.items():
        results[label] = format_time(seconds)
    return results

def format_time(seconds):
    if seconds < 0.001:
        return "instant"
    if seconds < 1:
        return f"{seconds*1000:.0f} ms"
    if seconds < 60:
        return f"{seconds:.1f} sec"
    if seconds < 3600:
        return f"{seconds/60:.1f} min"
    if seconds < 86400:
        return f"{seconds/3600:.1f} hrs"
    if seconds < 31536000:
        return f"{seconds/86400:.1f} days"
    if seconds < 3.154e9:
        return f"{seconds/31536000:.1f} years"
    return "centuries"

def detect_patterns(password):
    patterns = []
    if not password:
        return patterns

    # Check keyboard walk
    if len(password) >= 3:
        walk_len = 1
        max_walk = 1
        walk_start = 0
        for i in range(1, len(password)):
            if password[i].lower() in KEYBOARD_ADJ.get(password[i-1].lower(), set()):
                walk_len += 1
                if walk_len > max_walk:
                    max_walk = walk_len
                    walk_start = i - walk_len + 1
            else:
                walk_len = 1
        if max_walk >= 3:
            snippet = password[walk_start:walk_start+max_walk]
            penalty = max_walk * 2
            patterns.append({
                "type": "Keyboard pattern",
                "detail": f"'{snippet}' follows the keyboard layout",
                "bits": -penalty
            })

    # Check repeated characters
    repeats = re.findall(r'(.)\1{2,}', password)
    if repeats:
        for r in repeats:
            patterns.append({
                "type": "Repeated characters",
                "detail": f"'{r}' repeated consecutively",
                "bits": -4
            })

    # Check sequential letters/numbers
    seq_found = []
    for i in range(len(password) - 2):
        a, b, c = password[i], password[i+1], password[i+2]
        if (ord(b) - ord(a) == 1) and (ord(c) - ord(b) == 1):
            seq_found.append(password[i:i+3])
        elif (ord(a) - ord(b) == 1) and (ord(b) - ord(c) == 1):
            seq_found.append(password[i:i+3])
    if seq_found:
        patterns.append({
            "type": "Sequential characters",
            "detail": f"Sequence like '{seq_found[0]}' detected",
            "bits": -3
        })

    # Check date patterns
    date_match = re.search(r'(19|20)\d{2}|0[1-9]|1[0-2]', password)
    if date_match:
        patterns.append({
            "type": "Date-like pattern",
            "detail": f"'{date_match.group()}' looks like a date segment",
            "bits": -5
        })

    # Check leet speak
    leet_map = {'@': 'a', '3': 'e', '1': 'i', '0': 'o', '5': 's', '7': 't', '4': 'a'}
    normalized = ''.join(leet_map.get(c, c) for c in password.lower())
    if normalized != password.lower() and normalized in COMMON_PASSWORDS:
        patterns.append({
            "type": "Leet speak substitution",
            "detail": "Common word with character substitutions",
            "bits": -8
        })

    return patterns

def dictionary_check(password):
    lower = password.lower()
    # Check direct
    if lower in COMMON_PASSWORDS:
        return True, "Direct match in common password dictionary"
    # Check leet speak normalization
    leet_map = {'@': 'a', '3': 'e', '1': 'i', '0': 'o', '5': 's', '7': 't', '4': 'a'}
    normalized = ''.join(leet_map.get(c, c) for c in lower)
    if normalized in COMMON_PASSWORDS:
        return True, f"Matches '{normalized}' after leet-speak normalization"
    # Check if password contains a common word
    for word in COMMON_PASSWORDS:
        if len(word) >= 4 and word in lower:
            return True, f"Contains common word '{word}'"
    return False, "No match in common password dictionary (incl. leetspeak normalization)."

def get_suggestions(password, strength_score, has_lower, has_upper, has_digit, has_symbol):
    suggestions = []
    if len(password) < 12:
        suggestions.append("Use at least 12 characters (16+ is much better).")
    if not has_upper:
        suggestions.append("Add uppercase letters.")
    if not has_digit:
        suggestions.append("Add digits (0–9).")
    if not has_symbol:
        suggestions.append("Add symbols (!, @, #, $, etc.).")
    if strength_score <= 2:
        suggestions.append("Avoid common words and keyboard patterns.")
    if len(password) >= 8 and not suggestions:
        suggestions.append("Consider using a passphrase of 4+ random words for better memorability.")
    return suggestions

def get_strength(entropy, patterns):
    penalty = sum(abs(p['bits']) for p in patterns)
    effective = max(0, entropy - penalty)
    if effective < 28:
        return 0, "Very Weak"
    elif effective < 36:
        return 1, "Weak"
    elif effective < 50:
        return 2, "Fair"
    elif effective < 64:
        return 3, "Strong"
    else:
        return 4, "Very Strong"

def generate_password(length=16):
    chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?"
    while True:
        pwd = ''.join(random.choice(chars) for _ in range(length))
        if (re.search(r'[a-z]', pwd) and re.search(r'[A-Z]', pwd) and
                re.search(r'\d', pwd) and re.search(r'[^a-zA-Z0-9]', pwd)):
            return pwd

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    password = data.get('password', '')

    if not password:
        return jsonify({
            'length': 0, 'charset': 0, 'entropy': 0.0, 'guesses_exp': 0.0,
            'strength_score': -1, 'strength_label': '',
            'crack_times': {}, 'patterns': [],
            'dictionary': {'found': False, 'message': ''},
            'composition': {}, 'raw_entropy': 0.0, 'shannon': 0.0,
            'suggestions': []
        })

    charset, has_lower, has_upper, has_digit, has_symbol, has_unicode = get_charset_size(password)
    entropy = calculate_entropy(password)
    guesses = estimate_guesses(entropy)
    guesses_exp = math.log10(guesses) if guesses > 0 else 0
    patterns = detect_patterns(password)
    strength_score, strength_label = get_strength(entropy, patterns)
    times = crack_times(guesses)
    dict_found, dict_msg = dictionary_check(password)
    suggestions = get_suggestions(password, strength_score, has_lower, has_upper, has_digit, has_symbol)
    raw_ent = raw_entropy(password)
    shannon = shannon_entropy(password) * len(password)

    return jsonify({
        'length': len(password),
        'charset': charset,
        'entropy': round(entropy, 1),
        'guesses_exp': round(guesses_exp, 1),
        'strength_score': strength_score,
        'strength_label': strength_label,
        'crack_times': times,
        'patterns': patterns,
        'dictionary': {'found': dict_found, 'message': dict_msg},
        'composition': {
            'lower': has_lower,
            'upper': has_upper,
            'digit': has_digit,
            'symbol': has_symbol,
            'unicode': has_unicode
        },
        'raw_entropy': round(raw_ent, 1),
        'shannon': round(shannon, 1),
        'suggestions': suggestions
    })

@app.route('/generate', methods=['GET'])
def generate():
    pwd = generate_password()
    return jsonify({'password': pwd})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
