import re
from typing import List, Dict, Any

# Vibe keywords mapped to categories
VIBE_KEYWORDS = {
    "beach": ["beach", "sea", "ocean", "coast", "sand", "waves", "surf", "snorkel", "dive", "swim"],
    "adventure": ["adventure", "trek", "hike", "climb", "extreme", "thrilling", "bungee", "rafting", "skydive", "zip"],
    "nature": ["nature", "forest", "mountains", "hills", "wildlife", "green", "scenic", "waterfall", "valley", "lake"],
    "culture": ["culture", "history", "heritage", "temple", "fort", "museum", "art", "architecture", "traditional"],
    "nightlife": ["nightlife", "party", "club", "bar", "dance", "music", "night", "pub", "drinks", "cocktail"],
    "relaxation": ["relax", "peaceful", "calm", "rest", "spa", "serene", "quiet", "retreat", "unwind", "chill"],
    "food": ["food", "cuisine", "eat", "restaurant", "street food", "taste", "delicious", "culinary", "chef"],
    "spiritual": ["spiritual", "temple", "meditation", "yoga", "monastery", "sacred", "holy", "pilgrimage", "pray"],
    "snow": ["snow", "skiing", "snowboard", "cold", "winter", "frost", "ice", "glacier", "blizzard"],
    "desert": ["desert", "dunes", "camel", "sand", "arid", "hot", "barren", "safari"],
    "photography": ["photography", "photo", "scenic", "view", "landscape", "instagram", "picturesque", "sunset"],
    "family": ["family", "kids", "children", "safe", "comfortable", "fun", "theme park", "zoo"],
}

BUDGET_PATTERNS = [
    r'budget[:\s]+(?:rs\.?|inr|₹)?\s*(\d[\d,]*)',
    r'(?:rs\.?|inr|₹)\s*(\d[\d,]*)\s*(?:per\s+(?:day|person|night))?',
    r'(\d[\d,]*)\s*(?:rs|inr|rupees)',
    r'budget\s+(?:of|around|about|approx)?\s*(?:rs\.?|inr|₹)?\s*(\d[\d,]*)',
    r'spend\s+(?:around|about|upto|up to)?\s*(?:rs\.?|inr|₹)?\s*(\d[\d,]*)',
    r'(\d[\d,]*)\s*(?:a\s+day|per\s+day|\/day)',
]

CITY_KEYWORDS = [
    "mumbai", "delhi", "bangalore", "bengaluru", "hyderabad", "chennai", "kolkata",
    "pune", "ahmedabad", "jaipur", "lucknow", "surat", "kanpur", "nagpur", "patna",
    "indore", "thane", "bhopal", "visakhapatnam", "pimpri", "chandigarh", "kochi"
]

def extract_budget(messages: List[str]) -> int:
    """Extract budget from chat messages."""
    all_text = " ".join(messages).lower()
    budgets = []
    for pattern in BUDGET_PATTERNS:
        matches = re.findall(pattern, all_text, re.IGNORECASE)
        for m in matches:
            try:
                val = int(m.replace(",", ""))
                if 500 <= val <= 50000:
                    budgets.append(val)
            except:
                pass
    if budgets:
        return max(budgets)
    return 3000  # default budget per person per day

def extract_starting_city(messages: List[str]) -> str:
    """Extract starting city from messages."""
    all_text = " ".join(messages).lower()
    for city in CITY_KEYWORDS:
        if city in all_text:
            return city.title()
    return "Unknown"

def extract_vibes(messages: List[str]) -> Dict[str, float]:
    """Extract vibe preferences from all messages with confidence scores."""
    all_text = " ".join(messages).lower()
    vibe_scores = {}
    for vibe, keywords in VIBE_KEYWORDS.items():
        count = sum(all_text.count(kw) for kw in keywords)
        if count > 0:
            vibe_scores[vibe] = min(count / 3.0, 1.0)
    return vibe_scores

def extract_per_user_vibes(messages_by_user: Dict[str, List[str]]) -> Dict[str, Dict[str, float]]:
    """Extract vibes per user for fairness calculation."""
    user_vibes = {}
    for user, msgs in messages_by_user.items():
        user_vibes[user] = extract_vibes(msgs)
    return user_vibes

def analyze_chat(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Full chat analysis returning budget, vibes, city, and per-user preferences.
    messages: list of {"sender": str, "content": str}
    """
    all_texts = [m["content"] for m in messages]
    
    # Per-user messages
    user_messages: Dict[str, List[str]] = {}
    for m in messages:
        user_messages.setdefault(m["sender"], []).append(m["content"])
    
    budget = extract_budget(all_texts)
    starting_city = extract_starting_city(all_texts)
    group_vibes = extract_vibes(all_texts)
    per_user_vibes = extract_per_user_vibes(user_messages)
    
    # Top vibes sorted
    top_vibes = sorted(group_vibes.items(), key=lambda x: x[1], reverse=True)
    
    return {
        "budget": budget,
        "starting_city": starting_city,
        "group_vibes": group_vibes,
        "top_vibes": [v[0] for v in top_vibes[:5]],
        "per_user_vibes": per_user_vibes,
        "total_users": len(user_messages),
    }
