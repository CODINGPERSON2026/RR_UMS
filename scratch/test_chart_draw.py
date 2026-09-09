import io
import base64
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def generate_progression_line_chart_uri(milestones_or_chart_data, title="90-Day Physical Readiness & Weight Projection Curve", lang="en"):
    """
    Generates a simplified 90-day physical readiness vs weight projection line graph
    (Actual vs AI Projected) matching military specifications.
    Returns:
        str: base64 data URI (data:image/png;base64,...)
    """
    labels = ["Current Baseline", "30 Days Projected", "60 Days Projected", "90 Days Projected"]
    scores = [65.4, 74.1, 84.4, 94.8]
    weights = [69.0, 67.2, 65.5, 64.0]

    # Parse actual data if provided
    if isinstance(milestones_or_chart_data, dict):
        if 'chart_data' in milestones_or_chart_data and milestones_or_chart_data['chart_data']:
            cd = milestones_or_chart_data['chart_data']
            if cd.get('score_series'):
                scores = [float(s) for s in cd['score_series']]
            if cd.get('weight_series'):
                weights = [float(w) for w in cd['weight_series']]
            if cd.get('labels') and len(cd['labels']) == 4:
                labels = [str(l) for l in cd['labels']]
        elif 'milestones' in milestones_or_chart_data and milestones_or_chart_data['milestones']:
            ms = milestones_or_chart_data['milestones']
            if len(ms) >= 4:
                scores = [float(m.get('fitness_score', 0)) for m in ms[:4]]
                weights = [float(m.get('weight_kg', 0)) for m in ms[:4]]
                labels = [str(m.get('period', labels[i])) for i, m in enumerate(ms[:4])]
    elif isinstance(milestones_or_chart_data, list) and len(milestones_or_chart_data) >= 4:
        scores = [float(m.get('fitness_score', 0)) for m in milestones_or_chart_data[:4]]
        weights = [float(m.get('weight_kg', 0)) for m in milestones_or_chart_data[:4]]
        labels = [str(m.get('period', labels[i])) for i, m in enumerate(milestones_or_chart_data[:4])]

    # Modern high-density figure
    fig, ax1 = plt.subplots(figsize=(7.5, 2.7), dpi=180)
    fig.patch.set_facecolor('#ffffff')
    ax1.set_facecolor('#ffffff')

    x_indices = list(range(len(labels)))

    # Dual axis: ax1 = Readiness Score (PTS), ax2 = Weight (kg)
    ax2 = ax1.twinx()

    # Determine dynamic limits for clean spacing
    min_score = min(scores)
    max_score = max(scores)
    score_margin = max(5.0, (max_score - min_score) * 0.25)
    ax1.set_ylim(max(0.0, min_score - score_margin), min(100.0, max_score + score_margin + 5.0))

    min_wt = min(weights)
    max_wt = max(weights)
    wt_margin = max(2.0, (max_wt - min_wt) * 0.35)
    ax2.set_ylim(max(40.0, min_wt - wt_margin), max_wt + wt_margin + 2.0)

    # 1. Plot Readiness Score (Solid Emerald Green with circular markers)
    line1 = ax1.plot(
        x_indices, scores,
        color='#059669',
        linestyle='-',
        linewidth=2.2,
        marker='o',
        markersize=6.5,
        markerfacecolor='#059669',
        markeredgecolor='#047857',
        label='Readiness Score (PTS)'
    )

    # 2. Plot Weight (Dashed Royal Blue with square markers)
    line2 = ax2.plot(
        x_indices, weights,
        color='#2563eb',
        linestyle='--',
        linewidth=2.0,
        marker='s',
        markersize=6.0,
        markerfacecolor='#2563eb',
        markeredgecolor='#1d4ed8',
        label='Projected Weight (kg)'
    )

    # Value callouts on points
    for i, (sc, wt) in enumerate(zip(scores, weights)):
        # Score label
        ax1.annotate(
            f"{sc:.1f}" if isinstance(sc, float) and sc % 1 != 0 else f"{int(sc)}",
            (i, sc),
            textcoords="offset points",
            xytext=(0, 7 if i > 0 else -14),
            ha='center',
            fontsize=8.5,
            fontweight='bold',
            color='#065f46'
        )
        # Weight label
        ax2.annotate(
            f"{wt:.1f}kg",
            (i, wt),
            textcoords="offset points",
            xytext=(0, -14 if i > 0 else 7),
            ha='center',
            fontsize=8.5,
            fontweight='bold',
            color='#1e40af'
        )

    # Labels and Ticks
    ax1.set_xticks(x_indices)
    ax1.set_xticklabels(labels, fontsize=8.5, fontweight='bold', color='#1e293b')
    ax1.set_ylabel('Readiness Score (PTS)', color='#059669', fontsize=9.0, fontweight='bold', labelpad=6)
    ax2.set_ylabel('Weight (kg)', color='#2563eb', fontsize=9.0, fontweight='bold', labelpad=6)

    ax1.tick_params(axis='y', labelcolor='#059669', labelsize=8.0)
    ax2.tick_params(axis='y', labelcolor='#2563eb', labelsize=8.0)
    ax1.tick_params(axis='x', labelsize=8.5)

    # Grid
    ax1.grid(True, linestyle=':', alpha=0.5, color='#94a3b8')
    ax2.grid(False)

    # Title
    plt.title(title, fontsize=10.0, fontweight='bold', color='#1e3a8a', pad=10)

    # Combined Legend top-left
    lines = line1 + line2
    legend_labels = [l.get_label() for l in lines]
    legend = ax1.legend(
        lines, legend_labels,
        loc='upper left',
        frameon=True,
        facecolor='#ffffff',
        edgecolor='#cbd5e1',
        framealpha=0.92,
        fontsize=7.8
    )
    legend.get_frame().set_linewidth(0.8)

    # Clean borders
    for spine in ax1.spines.values():
        spine.set_color('#64748b')
        spine.set_linewidth(1.0)

    fig.tight_layout()

    out_path = r"E:\UMS-LATEST\scratch\test_progression_chart.png"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, format='png', dpi=180, bbox_inches='tight')
    plt.close(fig)

    print(f"Chart saved to {out_path}")

if __name__ == '__main__':
    generate_progression_line_chart_uri({})
