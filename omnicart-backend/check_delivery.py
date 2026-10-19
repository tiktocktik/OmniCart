import re
from datetime import datetime

with open('amazon_dump.html', 'r', encoding='utf-8') as f:
    text = f.read()

stamps = set(re.findall(r'deliveryDate[^\w]+(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z)', text))
print('Parsed ISO Stamps:', stamps)

# Convert ISO stamps to readable dates
formatted_dates = []
for s in sorted(stamps):
    dt = datetime.strptime(s, "%Y-%m-%dT%H:%M%z")
    formatted_dates.append(dt.strftime("%d %B"))

print("Formatted Delivery Dates from Amazon payload:", formatted_dates)
