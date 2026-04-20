import re
from typing import List, Dict, Any

VIBE_KEYWORDS = {
    "beach":       ["beach", "sea", "ocean", "coast", "sand", "waves", "surf", "snorkel", "dive", "swim"],
    "adventure":   ["adventure", "trek", "hike", "climb", "extreme", "thrilling", "bungee", "rafting", "skydive", "zip"],
    "nature":      ["nature", "forest", "mountains", "hills", "wildlife", "green", "scenic", "waterfall", "valley", "lake"],
    "culture":     ["culture", "history", "heritage", "temple", "fort", "museum", "art", "architecture", "traditional"],
    "nightlife":   ["nightlife", "party", "club", "bar", "dance", "music", "night", "pub", "drinks", "cocktail"],
    "relaxation":  ["relax", "peaceful", "calm", "rest", "spa", "serene", "quiet", "retreat", "unwind", "chill"],
    "food":        ["food", "cuisine", "eat", "restaurant", "street food", "taste", "delicious", "culinary", "chef"],
    "spiritual":   ["spiritual", "temple", "meditation", "yoga", "monastery", "sacred", "holy", "pilgrimage", "pray"],
    "snow":        ["snow", "skiing", "snowboard", "cold", "winter", "frost", "ice", "glacier", "blizzard"],
    "desert":      ["desert", "dunes", "camel", "sand", "arid", "hot", "barren", "safari"],
    "photography": ["photography", "photo", "scenic", "view", "landscape", "instagram", "picturesque", "sunset"],
    "family":      ["family", "kids", "children", "safe", "comfortable", "fun", "theme park", "zoo"],
    "waterpark":   ["waterpark", "water park", "water slide", "aqua park", "amusement park", "splash"],
    "water sports":["water sport", "water sports", "watersport", "jet ski", "kayak", "parasail",
                    "speed boat", "scuba", "snorkeling", "surfing", "wakeboard", "banana boat"],
}

BUDGET_PATTERNS = [
    r'budget[:\s]+(?:rs\.?|inr|₹)?\s*(\d[\d,]*)',
    r'(?:rs\.?|inr|₹)\s*(\d[\d,]*)\s*(?:per\s+(?:day|person|night))?',
    r'(\d[\d,]*)\s*(?:rs|inr|rupees)',
    r'budget\s+(?:of|around|about|approx|to)?\s*(?:rs\.?|inr|₹)?\s*(\d[\d,]*)',
    r'spend\s+(?:around|about|upto|up to)?\s*(?:rs\.?|inr|₹)?\s*(\d[\d,]*)',
    r'(\d[\d,]*)\s*(?:a\s+day|per\s+day|\/day)',
    r'exceed.*?(?:rs\.?|inr|₹)?\s*(\d[\d,]*)',
    r'increase.*?(?:rs\.?|inr|₹)?\s*(\d[\d,]*)',
    r'ready\s+to\s+(?:pay|spend|go|exceed|go up to).*?(?:rs\.?|inr|₹)?\s*(\d[\d,]*)',
    r'(?:rs\.?|inr|₹)\s*(\d[\d,]*)\s*per\s+day',
]

CITY_KEYWORDS = [
    "mumbai", "delhi", "bangalore", "bengaluru", "hyderabad", "chennai", "kolkata",
    "pune", "ahmedabad", "jaipur", "lucknow", "surat", "kanpur", "nagpur", "patna",
    "indore", "thane", "bhopal", "visakhapatnam", "pimpri", "chandigarh", "kochi"
]

STATE_KEYWORDS = [
    "maharashtra", "goa", "rajasthan", "kerala", "karnataka", "tamil nadu", "tamilnadu",
    "gujarat", "himachal pradesh", "himachal", "uttarakhand", "uttar pradesh",
    "west bengal", "punjab", "haryana", "andhra pradesh", "telangana", "odisha",
    "madhya pradesh", "chhattisgarh", "jharkhand", "assam", "sikkim", "meghalaya",
    "manipur", "nagaland", "arunachal pradesh", "mizoram", "tripura",
    "jammu kashmir", "jammu & kashmir", "ladakh",
]

# Common misspellings / shortcuts
STATE_ALIASES = {
    "karnatak": "karnataka",
    "karnataka": "karnataka",
    "maha": "maharashtra",
    "gujrat": "gujarat",
    "rajsthan": "rajasthan",
    "uttrakhand": "uttarakhand",
    "hp": "himachal pradesh",
    "uk": "uttarakhand",
    "ap": "andhra pradesh",
    "wb": "west bengal",
    "mp": "madhya pradesh",
}

NEGATION_PATTERNS = [
    r"not\s+(?:for\s+)?(\w[\w\s]*?)(?:\s+but|\s+and|\s*[,\.\!]|$)",
    r"no\s+(\w+)",
    r"don[\'t]*\s+want\s+(\w[\w\s]*?)(?:\s+but|\s*[,\.\!]|$)",
    r"don[\'t]*\s+like\s+(\w[\w\s]*?)(?:\s+but|\s*[,\.\!]|$)",
    r"avoid\s+(\w[\w\s]*?)(?:\s+but|\s*[,\.\!]|$)",
    r"without\s+(\w+)",
    r"hate\s+(\w+)",
    r"dislike\s+(\w+)",
    r"skip\s+(\w+)",
    r"except\s+(\w+)",
]

# Patterns that mean the user is EXPANDING acceptable states (not restricting)
OK_WITH_PATTERNS = [
    r"ok\s+with\s+(?:even\s+)?([a-z\s&]+?)(?:\s*state|\s*too|\s*also|\s*[,\.\!]|$)",
    r"also\s+ok\s+with\s+([a-z\s&]+?)(?:\s*state|\s*[,\.\!]|$)",
    r"fine\s+with\s+([a-z\s&]+?)(?:\s*state|\s*[,\.\!]|$)",
    r"okay\s+with\s+([a-z\s&]+?)(?:\s*state|\s*[,\.\!]|$)",
    r"can\s+(?:also\s+)?go\s+to\s+([a-z\s&]+?)(?:\s*state|\s*[,\.\!]|$)",
    r"even\s+([a-z\s&]+?)\s+(?:state\s+)?(?:is\s+)?(?:ok|fine|okay|good|alright)",
]

# Patterns that mean the user is RESTRICTING to a state
RESTRICT_STATE_PATTERNS = [
    r"only\s+in\s+([a-z\s&]+?)(?:\s+only|\s*[,\.\!]|$)",
    r"within\s+([a-z\s&]+?)(?:\s*[,\.\!]|$)",
    r"in\s+([a-z\s&]+?)\s+only",
    r"([a-z\s&]+?)\s+only",
    r"places?\s+in\s+([a-z\s&]+?)(?:\s*[,\.\!]|$)",
    r"choose\s+.*?in\s+([a-z\s&]+?)(?:\s+only|\s*[,\.\!]|$)",
    r"i\s+(?:am|m)\s+in\s+([a-z\s&]+?)\s+(?:right\s+now|now|so)",
    r"(?:from|based\s+in)\s+([a-z\s&]+?)(?:\s*[,\.\!]|$)",
]


def _match_state(candidate: str) -> str:
    """Return the canonical state name if candidate matches any state, else ''."""
    c = candidate.strip().lower()
    # Check aliases first
    if c in STATE_ALIASES:
        return STATE_ALIASES[c]
    # Check against full state list
    for state in STATE_KEYWORDS:
        if state in c or c in state:
            return state
    return ""


def extract_budget(messages: List[str]) -> int:
    """Extract budget — uses the MAXIMUM mentioned to handle 'increase budget' messages."""
    all_text = " ".join(messages).lower()
    budgets = []
    for pattern in BUDGET_PATTERNS:
        for m in re.findall(pattern, all_text, re.IGNORECASE):
            try:
                val = int(str(m).replace(",", ""))
                if 500 <= val <= 100000:
                    budgets.append(val)
            except:
                pass
    # Use the maximum mentioned budget (covers "ready to increase budget to 3000")
    return max(budgets) if budgets else 3000


def extract_starting_city(messages: List[str]) -> str:
    all_text = " ".join(messages).lower()
    for city in CITY_KEYWORDS:
        if city in all_text:
            return city.title()
    return "Unknown"


def extract_preferred_states(messages: List[str]) -> List[str]:
    """
    Returns a list of acceptable states.
    - If user says "Maharashtra only" → [maharashtra]
    - If user also says "ok with Karnataka" → [maharashtra, karnataka]
    - If no state mentioned → [] (means no filter — all states allowed)
    """
    all_text = " ".join(messages).lower()
    restricted = []
    expanded   = []

    # --- Restriction patterns ---
    for pattern in RESTRICT_STATE_PATTERNS:
        for match in re.findall(pattern, all_text, re.IGNORECASE):
            s = _match_state(match)
            if s and s not in restricted:
                restricted.append(s)

    # --- "ok with / also ok" patterns ---
    for pattern in OK_WITH_PATTERNS:
        for match in re.findall(pattern, all_text, re.IGNORECASE):
            s = _match_state(match)
            if s and s not in expanded:
                expanded.append(s)

    combined = list(dict.fromkeys(restricted + expanded))  # preserve order, deduplicate
    return combined


def extract_excluded_vibes(messages: List[str]) -> List[str]:
    """Extract vibe categories the user explicitly does NOT want."""
    all_text = " ".join(messages).lower()
    excluded = set()

    for neg_pattern in NEGATION_PATTERNS:
        for match in re.findall(neg_pattern, all_text, re.IGNORECASE):
            match_lower = match.strip().lower()
            for vibe, keywords in VIBE_KEYWORDS.items():
                if match_lower == vibe:
                    excluded.add(vibe)
                    break
                if match_lower in keywords:
                    excluded.add(vibe)
                    break
                if any(match_lower in kw or kw in match_lower for kw in keywords):
                    excluded.add(vibe)
                    break

    return list(excluded)


def extract_vibes(messages: List[str]) -> Dict[str, float]:
    """Extract positive vibe preferences with confidence scores."""
    all_text = " ".join(messages).lower()
    vibe_scores = {}
    for vibe, keywords in VIBE_KEYWORDS.items():
        count = sum(all_text.count(kw) for kw in keywords)
        if count > 0:
            vibe_scores[vibe] = min(count / 3.0, 1.0)
    return vibe_scores


def extract_per_user_vibes(messages_by_user: Dict[str, List[str]]) -> Dict[str, Dict[str, float]]:
    user_vibes = {}
    for user, msgs in messages_by_user.items():
        user_vibes[user] = extract_vibes(msgs)
    return user_vibes


def analyze_chat(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Full analysis of ALL messages every time it is called.
    Always reads the latest state of the conversation — no caching.
    """
    all_texts = [m["content"] for m in messages]

    user_messages: Dict[str, List[str]] = {}
    for m in messages:
        user_messages.setdefault(m["sender"], []).append(m["content"])

    budget           = extract_budget(all_texts)
    starting_city    = extract_starting_city(all_texts)
    preferred_states = extract_preferred_states(all_texts)
    excluded_vibes   = extract_excluded_vibes(all_texts)
    group_vibes      = extract_vibes(all_texts)
    per_user_vibes   = extract_per_user_vibes(user_messages)

    # Remove excluded vibes from positive scores
    for ev in excluded_vibes:
        group_vibes.pop(ev, None)

    top_vibes = sorted(group_vibes.items(), key=lambda x: x[1], reverse=True)

    return {
        "budget":            budget,
        "starting_city":     starting_city,
        "preferred_states":  preferred_states,   # list now, not single string
        "excluded_vibes":    excluded_vibes,
        "group_vibes":       group_vibes,
        "top_vibes":         [v[0] for v in top_vibes[:5]],
        "per_user_vibes":    per_user_vibes,
        "total_users":       len(user_messages),
    }
