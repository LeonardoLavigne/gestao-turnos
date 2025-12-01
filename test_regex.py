import re

# Current Regex (approximate, will be replaced by actual one from file if I imported it, but here I copy it to test the logic)
# I will use the one I plan to implement to test if it works.

LINHA_REGEX_NEW = re.compile(
    r"^(?:dia\s+(?P<data>\d{1,2}[/-]\d{1,2}[/-]\d{4})\s*[-–—:]?\s*)?"
    r"(?P<tipo>[^\s\-–—:]+)\s*(?:[-–—:]\s*)?"
    r"(?P<h1>\d{1,2}:\d{2})\s*(?:as|às|a|ate)\s*(?P<h2>\d{1,2}:\d{2})$",
    re.IGNORECASE,
)

examples = [
    "Dia 29/11/2025 - Casino 15:00 as 03:00",
    "Dia 30/11/2025 - Palacio 09:30 as 19:30",
    "Dia 01/12/2025 - REN 00:00 as 08:00",
    "Casino - 21:00 as 03:00",
    "REN 08:00 as 16:00"
]

for ex in examples:
    m = LINHA_REGEX_NEW.match(ex)
    if m:
        print(f"MATCH: '{ex}' -> Data={m.group('data')}, Tipo={m.group('tipo')}, H1={m.group('h1')}, H2={m.group('h2')}")
    else:
        print(f"NO MATCH: '{ex}'")
