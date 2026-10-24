AGENCY_KEYWORDS = [
    "агентство нерухомості", "агенство нерухомості", "ан ", "ріелтор", "риелтор",
]

def is_agency(title: str, description: str, seller_type: str) -> bool:
    text = f"{title} {description}".lower()
    return any(kw in text for kw in AGENCY_KEYWORDS)
