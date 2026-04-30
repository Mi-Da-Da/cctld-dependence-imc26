# -*- coding: utf-8 -*-
import os
import re
from typing import List, Tuple

import matplotlib.pyplot as plt


def extract_country_code(folder_name: str) -> str:
    parts = folder_name.split("_", 1)
    if len(parts) == 2 and parts[1]:
        return parts[1].split("_", 1)[0].upper()
    return folder_name.upper()


def parse_single_vendor(path: str) -> Tuple[int, float, List[Tuple[str, float]]]:
    """Return (total_domains, weak dependency percent, top3 providers with percent) from single_vendor_stats.txt."""
    total_domains = 0
    weak_pct = None
    top3: List[Tuple[str, float]] = []
    weak_section = False
    total_re = re.compile(r"总域名数:\s*(\d+)")
    weak_line_re = re.compile(r"弱单一依赖\s*\(NS=IP\):.*\(([\d\.]+)%\)")
    provider_line_re = re.compile(r"(.+?):\s+\d+\s+\(([\d\.]+)%\)")

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if total_domains == 0:
                m_total = total_re.search(line)
                if m_total:
                    total_domains = int(m_total.group(1))
            if weak_pct is None:
                m = weak_line_re.search(line)
                if m:
                    weak_pct = float(m.group(1))
            if line.startswith("--- 弱单一依赖分布 ---"):
                weak_section = True
                continue
            if line.startswith("--- 强单一依赖分布 ---"):
                weak_section = False
                continue
            if weak_section and len(top3) < 3:
                m = provider_line_re.match(line)
                if m:
                    prov = m.group(1).strip()
                    pct = float(m.group(2))
                    top3.append((prov, pct))
    return total_domains, (weak_pct if weak_pct is not None else 0.0), top3


def collect_data(root: str) -> List[Tuple[str, float, List[Tuple[str, float]]]]:
    """Collect (country, weak_pct, top3 providers (name,pct)) for each out_* folder where total > 40."""
    results: List[Tuple[str, float, List[Tuple[str, float]]]] = []
    for folder in os.listdir(root):
        if not folder.startswith("out_"):
            continue
        folder_path = os.path.join(root, folder)
        if not os.path.isdir(folder_path):
            continue
        stats_path = os.path.join(folder_path, "single_vendor_stats.txt")
        if not os.path.exists(stats_path):
            continue
        total_domains, weak_pct, top3 = parse_single_vendor(stats_path)
        if total_domains <= 40:
            continue
        country = extract_country_code(folder)
        results.append((country, weak_pct, top3))
    return results


def main() -> None:
    current_dir = os.getcwd()
    data = collect_data(current_dir)
    if not data:
        print("No single_vendor_stats.txt data found.")
        return

    # sort by weak single dependency percent descending
    data.sort(key=lambda x: x[1], reverse=True)
    countries = [d[0] for d in data]
    weak_percents = [d[1] for d in data]
    top3_list = [d[2] for d in data]

    # prepare stacked values for top3 within weak dependency
    stack_segments: List[Tuple[float, float, float]] = []
    for weak_pct, top3 in zip(weak_percents, top3_list):
        segs = [pct for _, pct in top3[:3]]
        while len(segs) < 3:
            segs.append(0.0)
        stack_segments.append((segs[0], segs[1], segs[2]))

    fig_width = max(18, 0.4 * len(countries))
    fig_height = 10
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    x_pos = range(len(countries))
    colors_rank = ["#4e79a7", "#f28e2b", "#e15759"]  # rank1, rank2, rank3
    labels_rank = ["Top1", "Top2", "Top3"]

    bottom = [0.0] * len(countries)
    for idx, label in enumerate(labels_rank):
        heights = [seg[idx] for seg in stack_segments]
        ax.bar(
            x_pos,
            heights,
            bottom=bottom,
            color=colors_rank[idx],
            label=label,
            width=0.8,
            edgecolor="white",
            linewidth=0.5,
        )
        bottom = [b + h for b, h in zip(bottom, heights)]

    # annotate provider names + percents on each segment if height significant
    max_height = max([sum(seg) for seg in stack_segments]) if stack_segments else 0
    for x, segs, names in zip(x_pos, stack_segments, top3_list):
        cumulative = 0.0
        for (prov_name, prov_pct), height in zip(names[:3], segs):
            if not prov_name or height <= max_height * 0.015:
                cumulative += height
                continue
            short_name = prov_name
            words = prov_name.split()
            if len(words) > 2:
                short_name = " ".join(words[:2]) + "..."
            ax.text(
                x,
                cumulative + height / 2,
                short_name,
                ha="center",
                va="center",
                fontsize=5,
                color="black",
            )
            cumulative += height

    # add overall weak_pct marker
    ax.plot(x_pos, weak_percents, "o", color="#222222", markersize=4, alpha=0.6, label="Total weak%")

    ax.set_xticks(list(x_pos))
    ax.set_xticklabels(countries, rotation=90, fontsize=11)
    ax.set_ylabel("Weak single dependency (%)", fontsize=13)
    ax.set_title("Weak single dependency (NS=IP) with Top3 providers (stacked)", fontsize=15, fontweight="bold")
    ax.tick_params(axis="y", labelsize=12)
    ax.legend(
        title="Rank / total",
        fontsize=19,
        title_fontsize=19,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.12),
        ncol=4,
    )

    plt.tight_layout()
    plt.savefig("single2_vendor_weak.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("Generated single2_vendor_weak.png")


if __name__ == "__main__":
    main()
