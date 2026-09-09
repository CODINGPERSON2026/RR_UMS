"""
Chart Generator for UMS AI Fitness Report.
Generates simplified, high-resolution line graphs for 90-day physical readiness & weight projection
(Actual baseline vs AI projected trajectory) to embed directly into PDF reports.
"""

import io
import base64
import logging

logger = logging.getLogger("fitness_trend.pdf.chart_generator")


def generate_progression_line_chart_uri(progression_data, title="90-Day Physical Readiness & Weight Projection Curve", lang="en"):
    """
    Generates a publication-grade, simplified 90-day physical readiness vs weight projection line graph
    (Actual vs AI Projected) matching military dossier styling.
    
    Args:
        progression_data (dict): Dictionary with 'milestones' and/or 'chart_data'
        title (str): Chart title
        lang (str): Target language code
        
    Returns:
        str: Base64 data URI (data:image/png;base64,...) or empty string on failure.
    """
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        labels = ["Current Baseline", "30 Days Projected", "60 Days Projected", "90 Days Projected"]
        scores = [65.4, 74.1, 84.4, 94.8]
        weights = [69.0, 67.2, 65.5, 64.0]

        if isinstance(progression_data, dict):
            if 'chart_data' in progression_data and progression_data['chart_data']:
                cd = progression_data['chart_data']
                if cd.get('score_series'):
                    scores = [float(s) for s in cd['score_series']]
                if cd.get('weight_series'):
                    weights = [float(w) for w in cd['weight_series']]
                if cd.get('labels') and len(cd['labels']) == 4:
                    labels = [str(l) for l in cd['labels']]
            elif 'milestones' in progression_data and progression_data['milestones']:
                ms = progression_data['milestones']
                if len(ms) >= 4:
                    scores = [float(m.get('fitness_score', 0)) for m in ms[:4]]
                    weights = [float(m.get('weight_kg', 0)) for m in ms[:4]]
                    labels = [str(m.get('period', labels[i])) for i, m in enumerate(ms[:4])]

        # Dynamic figure dimensions suited for A4 width
        fig, ax1 = plt.subplots(figsize=(7.4, 2.65), dpi=180)
        fig.patch.set_facecolor('#ffffff')
        ax1.set_facecolor('#ffffff')

        x_indices = list(range(len(labels)))
        ax2 = ax1.twinx()

        # Dynamic axis limits
        min_score = min(scores)
        max_score = max(scores)
        score_margin = max(6.0, (max_score - min_score) * 0.25)
        ax1.set_ylim(max(0.0, min_score - score_margin), min(100.0, max_score + score_margin + 4.0))

        min_wt = min(weights)
        max_wt = max(weights)
        wt_margin = max(2.5, (max_wt - min_wt) * 0.35)
        ax2.set_ylim(max(40.0, min_wt - wt_margin), max_wt + wt_margin + 2.0)

        # 1. Plot Readiness Score (Solid Emerald Green line with circular markers)
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

        # 2. Plot Weight (Dashed Royal Blue line with square markers)
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

        # Intelligent point annotations to prevent overlapping
        for i, (sc, wt) in enumerate(zip(scores, weights)):
            # Normalize positions to detect proximity
            norm_sc = (sc - ax1.get_ylim()[0]) / (ax1.get_ylim()[1] - ax1.get_ylim()[0])
            norm_wt = (wt - ax2.get_ylim()[0]) / (ax2.get_ylim()[1] - ax2.get_ylim()[0])
            diff = norm_sc - norm_wt

            if diff >= 0:
                sc_offset = 7
                wt_offset = -14
            else:
                sc_offset = -14
                wt_offset = 7

            # Score label
            ax1.annotate(
                f"{sc:.1f}" if isinstance(sc, float) and sc % 1 != 0 else f"{int(sc)}",
                (i, sc),
                textcoords="offset points",
                xytext=(0, sc_offset),
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
                xytext=(0, wt_offset),
                ha='center',
                fontsize=8.5,
                fontweight='bold',
                color='#1e40af'
            )

        # Axis configurations
        ax1.set_xticks(x_indices)
        ax1.set_xticklabels(labels, fontsize=8.2, fontweight='bold', color='#1e293b')
        ax1.set_ylabel('Readiness Score (PTS)', color='#059669', fontsize=8.8, fontweight='bold', labelpad=6)
        ax2.set_ylabel('Weight (kg)', color='#2563eb', fontsize=8.8, fontweight='bold', labelpad=6)

        ax1.tick_params(axis='y', labelcolor='#059669', labelsize=8.0)
        ax2.tick_params(axis='y', labelcolor='#2563eb', labelsize=8.0)
        ax1.tick_params(axis='x', labelsize=8.2)

        # Subtle background grid
        ax1.grid(True, linestyle=':', alpha=0.5, color='#94a3b8')
        ax2.grid(False)

        # Title
        plt.title(title, fontsize=9.8, fontweight='bold', color='#1e3a8a', pad=10)

        # Top-left combined legend
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

        # Dark borders
        for spine in ax1.spines.values():
            spine.set_color('#64748b')
            spine.set_linewidth(1.0)

        fig.tight_layout()

        # Buffer export
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=180, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)

        b64_str = base64.b64encode(buf.read()).decode('utf-8')
        return f"data:image/png;base64,{b64_str}"

    except Exception as e:
        logger.warning(f"Failed to generate progression line chart image: {e}")
        return ""
