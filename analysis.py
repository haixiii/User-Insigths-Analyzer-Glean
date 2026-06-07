import anthropic
import os
import csv
from collections import defaultdict
from dotenv import load_dotenv

# Load your API key
load_dotenv()

# Connect to Anthropic
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Read the CSV file
category_counts = defaultdict(int)
signals_by_category = defaultdict(list)
themes = []

with open("results.csv", "r") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        # Count each category
        categories = row["Categories"].split(",")
        for category in categories:
            category = category.strip()
            if category:
                category_counts[category] += 1

        # Store signals by category
        signals = row["Signals"].split("|")
        for signal in signals:
            signal = signal.strip()
            if ":" in signal:
                category = signal.split(":")[0].replace("-", "").strip()
                explanation = signal.split(":", 1)[1].strip()
                signals_by_category[category].append(explanation)

        # Collect themes
        if row["Primary Theme"]:
            themes.append(row["Primary Theme"])

# Step 1 — Print category distribution
print("=" * 50)
print("CATEGORY DISTRIBUTION")
print("=" * 50)
total = sum(category_counts.values())
for category, count in sorted(category_counts.items(),
                               key=lambda x: x[1], reverse=True):
    percentage = round((count / total) * 100)
    bar = "█" * (count // 2)
    print(f"{category:<15} {count:>3} signals ({percentage}%) {bar}")

# Step 2 — Analyze inhibitor themes
print("\n" + "=" * 50)
print("INHIBITOR THEME ANALYSIS")
print("=" * 50)

inhibitor_signals = "\n".join(signals_by_category.get("Inhibitor", []))

if inhibitor_signals:
    theme_message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""You are a market intelligence analyst.

Here are all the inhibitor signals from Glean customer reviews.
Group them into 3-5 distinct themes.

For each theme provide:
- Theme name (3-5 words)
- How many signals belong to it
- One sentence describing the pattern
- The single most representative signal

Inhibitor signals:
{inhibitor_signals}"""
            }
        ]
    )
    print(theme_message.content[0].text)
else:
    print("No inhibitor signals found")

# Step 3 — Strategic summary
print("\n" + "=" * 50)
print("STRATEGIC SUMMARY AND RECOMMENDATIONS")
print("=" * 50)

all_signals_text = ""
for category, signals in signals_by_category.items():
    all_signals_text += f"\n{category}:\n"
    for signal in signals:
        all_signals_text += f"- {signal}\n"

summary_message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=2048,
    messages=[
        {
            "role": "user",
            "content": f"""You are a senior brand strategist.

Based on this customer signal analysis for Glean (a B2B enterprise
AI search tool), write a strategic summary including:

1. Core strategic problem — one clear paragraph
2. Three specific recommendations ranked by priority
3. The single most important insight a CEO should act on immediately

Be direct and specific. Avoid generic advice.

Customer signals by category:
{all_signals_text}"""
        }
    ]
)

print(summary_message.content[0].text)

# Save full report
print("\n" + "=" * 50)
print("Saving report...")

with open("glean_analysis_report.txt", "w") as f:
    f.write("GLEAN CUSTOMER SIGNAL ANALYSIS REPORT\n")
    f.write("=" * 50 + "\n\n")

    f.write("CATEGORY DISTRIBUTION\n")
    f.write("-" * 30 + "\n")
    for category, count in sorted(category_counts.items(),
                                   key=lambda x: x[1], reverse=True):
        percentage = round((count / total) * 100)
        f.write(f"{category}: {count} signals ({percentage}%)\n")

    f.write("\n\nINHIBITOR THEME ANALYSIS\n")
    f.write("-" * 30 + "\n")
    f.write(theme_message.content[0].text)

    f.write("\n\nSTRATEGIC SUMMARY AND RECOMMENDATIONS\n")
    f.write("-" * 30 + "\n")
    f.write(summary_message.content[0].text)

print("Report saved to glean_analysis_report.txt")
print("=" * 50)