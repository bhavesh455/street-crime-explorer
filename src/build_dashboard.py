"""
Build dashboard: render a self-contained static HTML report from the
tidy data (data/clean/crimes_tidy.csv) using matplotlib charts saved as
PNGs next to the HTML file. No JavaScript, no CDN, no external assets -
open output/index.html in any browser and it just works.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean" / "crimes_tidy.csv"
OUT_DIR = ROOT / "output"

BRISTOL = "#7b1e3b"   # dark claret
LONDON = "#1f4e79"    # deep blue
GREY = "#666666"


def area_month_totals(df):
    t = (df.groupby(["area_name", "month"]).size()
           .unstack(fill_value=0).sort_index(axis=1))
    return t


def chart_monthly_totals(df, path):
    t = area_month_totals(df)
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for area in t.index:
        colour = BRISTOL if area.startswith("Bristol") else LONDON
        ax.plot([str(m) for m in t.columns], t.loc[area], marker="o",
                label=area, color=colour, linewidth=2)
    ax.set_title("Total recorded street crimes per month, by area")
    ax.set_ylabel("Crimes")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def chart_top_categories(df, path):
    top = (df.groupby("category_label").size()
             .sort_values(ascending=True).tail(8))
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.barh(top.index, top.values, color=LONDON)
    ax.set_title("Most common crime categories (all areas, all months)")
    ax.set_xlabel("Crimes")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def chart_area_split(df, path):
    latest = df[df["month"] == df["month"].max()]
    split = (latest.groupby(["area_name", "category_label"]).size()
                   .unstack(fill_value=0))
    top_cats = split.sum().sort_values(ascending=False).head(5).index
    split = split[top_cats]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    split.plot(kind="bar", ax=ax)
    ax.set_title(f"Category mix by area, latest month ({df['month'].max()})")
    ax.set_ylabel("Crimes")
    ax.legend(fontsize=8, title="Category")
    plt.xticks(rotation=15, ha="right")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def html_table(df):
    return df.to_html(index=False, classes="data", border=0,
                      justify="left")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(CLEAN, parse_dates=["month"])
    df["month"] = df["month"].dt.date

    chart_monthly_totals(df, OUT_DIR / "monthly_totals.png")
    chart_top_categories(df, OUT_DIR / "top_categories.png")
    chart_area_split(df, OUT_DIR / "area_category_mix.png")

    totals = area_month_totals(df).reset_index()
    totals.columns = ["Area"] + [str(c) for c in totals.columns[1:]]
    totals["Total (3 months)"] = totals.iloc[:, 1:].sum(axis=1)

    months = sorted(df["month"].unique())
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Bristol &amp; London Street Crime Explorer</title>
<style>
  body {{ font-family: Georgia, 'Times New Roman', serif; margin: 2rem auto;
         max-width: 880px; padding: 0 1rem; color: #222; line-height: 1.5; }}
  h1 {{ font-size: 1.7rem; margin-bottom: 0.2rem; }}
  h2 {{ font-size: 1.2rem; margin-top: 2rem; border-bottom: 2px solid #1f4e79;
        padding-bottom: 0.2rem; }}
  .sub {{ color: {GREY}; margin-top: 0; }}
  table.data {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
  table.data th, table.data td {{ border: 1px solid #ccc; padding: 0.35rem 0.6rem;
        text-align: left; font-size: 0.92rem; }}
  table.data th {{ background: #eef3f8; }}
  img {{ max-width: 100%; }}
  .note {{ background: #f7f7f7; border-left: 4px solid {BRISTOL};
           padding: 0.6rem 1rem; font-size: 0.92rem; }}
</style>
</head>
<body>
<h1>Bristol &amp; London Street Crime Explorer</h1>
<p class="sub">Recorded street-level crimes within roughly one mile of four
neighbourhood points, {months[0]} to {months[-1]}. Data: data.police.uk.</p>

<p><strong>Who this is for:</strong> anyone weighing up a move between
Bristol and London - for example a graduate relocating for a first job -
who wants an honest, like-for-like picture of the types and volumes of
recorded crime near specific neighbourhoods, rather than city-wide
averages that hide local differences.</p>

<h2>Totals by area and month</h2>
{html_table(totals)}
<p>Counts are recorded crimes at street level. London points sit in dense
commercial centres, so higher volumes there partly reflect footfall, not
just risk to residents - see the caveats below.</p>
<img src="monthly_totals.png" alt="Line chart of monthly crime totals by area">

<h2>What kinds of crime dominate?</h2>
<img src="top_categories.png" alt="Bar chart of top crime categories">
<img src="area_category_mix.png" alt="Bar chart of category mix by area, latest month">

<div class="note">
<strong>Read this before drawing conclusions:</strong> police.uk data is
published with a lag of around two months. Street-level locations are
anonymised - each crime is snapped to a nearby point on a map of anonymous
locations, so a crime shown "on or near" a street did not necessarily
happen exactly there. These figures count <em>recorded</em> crime only, and
recording practices differ between forces.
</div>

<p class="sub">Built with a small Python pipeline: API extract &rarr;
pandas/SQLite transform &rarr; this static page. Source and raw data are
in the project repository.</p>
</body>
</html>
"""
    (OUT_DIR / "index.html").write_text(html)
    print(f"Dashboard written -> {OUT_DIR / 'index.html'}")
    print(f"Charts: monthly_totals.png, top_categories.png, area_category_mix.png")
    print(f"Rows behind dashboard: {len(df)}")


if __name__ == "__main__":
    main()
