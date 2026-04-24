import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Create folder for all result plots
os.makedirs("results_plots", exist_ok=True)

# Load CSV
df = pd.read_csv("data/feedback.csv")

# Clean hidden spaces from column names
df.columns = df.columns.str.strip()

# Print columns so you can verify names
print("Columns in dataset:")
print(df.columns)

sns.set(style="whitegrid")


############################################
# GRAPH 1: Performance Metrics Bar Chart
############################################

metrics = {
    'Destination Relevance': df['destination_relevance'].mean(),
    'Vibe Match': df['vibe_match'].mean(),
    'Overall Satisfaction': df['overall_satisfaction'].mean(),
    'Budget Accuracy': df['budget_accuracy'].mean()
}

scores = [(v/5)*100 for v in metrics.values()]

plt.figure(figsize=(10,6))

plt.bar(metrics.keys(), scores)

plt.title("Performance Evaluation Metrics")
plt.ylabel("Percentage")
plt.ylim(0,100)

plt.savefig("results_plots/metric_bar_chart.png")
plt.show()



############################################
# GRAPH 2: Satisfaction Distribution
############################################

plt.figure(figsize=(8,5))

sns.histplot(
    df['overall_satisfaction'],
    bins=5
)

plt.title("User Satisfaction Distribution")
plt.xlabel("Rating")
plt.ylabel("Frequency")

plt.savefig("results_plots/satisfaction_histogram.png")
plt.show()



############################################
# GRAPH 3: Re-usage Intent Pie Chart
############################################

reuse = df['would_use_again'].value_counts()

plt.figure(figsize=(7,7))

plt.pie(
    reuse,
    labels=reuse.index,
    autopct='%1.1f%%'
)

plt.title("Re-usage Intent")

plt.savefig("results_plots/reuse_pie_chart.png")
plt.show()



############################################
# GRAPH 4: Destination Diversity
############################################

# If this errors, check printed column names
dest_counts = df['recommended_city'].value_counts()

plt.figure(figsize=(12,6))

dest_counts.plot(kind='bar')

plt.title("Destination Coverage Diversity")
plt.xlabel("Destination")
plt.ylabel("Recommendations")

plt.savefig("results_plots/destination_diversity.png")
plt.show()



############################################
# GRAPH 5: Radar Chart
############################################

categories = [
    'Destination Relevance',
    'Vibe Match',
    'Overall Satisfaction',
    'Budget Accuracy'
]

values = [
    df['destination_relevance'].mean(),
    df['vibe_match'].mean(),
    df['overall_satisfaction'].mean(),
    df['budget_accuracy'].mean()
]

# Close radar loop
values += values[:1]

angles = np.linspace(
    0,
    2*np.pi,
    len(categories),
    endpoint=False
).tolist()

angles += angles[:1]

fig = plt.figure(figsize=(8,8))

ax = plt.subplot(
    111,
    polar=True
)

ax.plot(angles, values)

ax.fill(
    angles,
    values,
    alpha=0.25
)

ax.set_xticks(angles[:-1])

ax.set_xticklabels(categories)

plt.title("System Performance Radar")

plt.savefig("results_plots/radar_chart.png")
plt.show()



############################################
# Summary Statistics for Paper
############################################

print("\nSummary Statistics:")
print(
    df[
        [
            'overall_satisfaction',
            'vibe_match',
            'budget_accuracy',
            'destination_relevance'
        ]
    ].describe()
)

print("\nAll plots saved inside results_plots/ folder.")