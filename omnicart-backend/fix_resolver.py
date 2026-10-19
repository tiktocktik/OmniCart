import re

with open("app/resolver.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace invalid fields in PricePrediction
content = re.sub(
    r'PricePrediction\(\s*verdict=[^\n]+,\s*confidence_score=[^\n]+,\s*detail=(f?"[^\n]+"),\s*best_action=[^\n]+,\s*price_direction=[^\n]+,\s*badge="VERIFY ON STORE"\s*\)',
    r'PricePrediction(badge="VERIFY ON STORE", detail=\1, drop_likelihood="LOW", confidence=75)',
    content
)

with open("app/resolver.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated resolver.py successfully!")
