# Bristol & London Street Crime Explorer

A small, reproducible data pipeline that pulls street-level crime data from
the [data.police.uk API](https://data.police.uk/docs/), cleans it into a tidy
dataset with Python and SQL, and publishes the results as a simple static
dashboard.

**Live output:** open [`output/index.html`](output/index.html) in any browser
(no server, no JavaScript, no external dependencies).

---

## About me

I'm Bhavesh Shekhawat, a data scientist based in Bristol and relocating to
London. I completed an MSc in Data Science (Distinction) at the University of
Bristol in 2026, following a B.Tech (2019-2023).

Before and alongside the MSc I worked as a Junior Data Scientist at Tech Hyaku
in India (May 2023 - June 2025), where introducing CI/CD practices cut manual
deployment steps by 30%, and I founded Epaywebsolution (2023 - present), a B2B
fintech and digital wallet business where I improved transaction-processing
efficiency by 20% in 2024. Most recently I was a Data Analyst Intern at Vayu
Service UK in Bristol (January - April 2026), automating reporting so report
generation ran 25% faster with 15% fewer manual entry errors. My MSc project
modelled spatial transcriptomics data - predicting 44 protein markers across
roughly 166,000 spatial bins, where adding spatial features lifted the TOP10
Spearman correlation from 0.468 to 0.629.

My day-to-day toolkit is Python, SQL, Pandas, NumPy, scikit-learn and PyTorch,
with AWS, GCP, Tableau, Excel and Power Query, and CI/CD on Linux.

- GitHub: https://github.com/bhavesh455
- Portfolio: https://bhavesh-data-portfolio.vercel.app/

## Why I'm applying to the Data School

The parts of my work I enjoy most are the unglamorous ones that everything
else depends on: getting data out of a source system reliably, shaping it
into something clean and consistent, and making sure the numbers at the end
can be trusted. That is data engineering, and it is the direction I want my
career to take. I am applying to the Data School's Data Engineering stream
because I want structured training in the modern data-stack tools I have not
yet used professionally - Snowflake, dbt and Databricks are on the syllabus
precisely because I want to learn them properly, in a training environment,
before using them with clients. This project is my attempt to show, with a
small real example, how I already approach pipeline work.

## The project

**Problem.** City-wide crime statistics are easy to find but hard to act on:
they average together very different neighbourhoods, and two areas in the
same city can feel completely different. Someone deciding where to live
needs figures for *specific places*, presented like-for-like.

**Audience.** People relocating for work - graduates moving to London are
the example I had in mind, because I am one. They need an honest,
neighbourhood-level comparison between where they live now (Bristol) and
where they are moving to (London), with the caveats stated plainly rather
than buried.

**What it shows.** For four fixed points - Bristol City Centre, Bristol
Fishponds (where I live now), the Bank/Watling Street area of London, and
Shoreditch - the dashboard shows, for the latest three months available:

- total recorded street crimes per area per month;
- the most common crime categories overall; and
- the category mix for each area in the latest month.

## How it works

```
data.police.uk API
        |
        v
src/extract.py      raw JSON per location-month  ->  data/raw/ (+ manifest.json)
        |
        v
src/transform.py    pandas flatten/clean, de-duplicate within area,
                    load to SQLite, SQL aggregation -> data/clean/
                    (crimes_tidy.csv + crime.db)
        |
        v
src/build_dashboard.py   matplotlib charts + static HTML -> output/index.html
```

Run it end to end:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
./run_all.sh          # or: make
pytest tests/         # or: make test
```

`extract.py` asks the API which months exist and always takes the latest
three, so the project stays current whenever it is re-run; it also skips
files already downloaded and retries politely on timeouts.

## Key decisions and trade-offs

- **Small scope on purpose.** Four locations, three months, one API
  endpoint. A small pipeline that runs end to end and reconciles is worth
  more than a large one that half works.
- **Raw data kept untouched.** Every API response is saved exactly as
  received (22,266 records) alongside a manifest, so anyone can re-run the
  transform from the same inputs and check my working.
- **De-duplication is per area, not global.** The two London points are
  about 1.5 km apart, so their roughly one-mile search circles overlap: a
  crime in the overlap appears in both extracts (18,440 unique crimes
  behind 22,266 area-level rows). I kept it in both areas because each
  area's number answers "what was recorded within a mile of this point" -
  the same behaviour as the police.uk website itself - and I document it
  here rather than quietly shrinking one area's total.
- **SQL does real work.** The tidy table is loaded into SQLite and the
  dashboard's summary table is produced by a SQL `GROUP BY` query, then
  cross-checked against the pandas row counts in the tests. The summary
  total (22,266) reconciles exactly with the raw record count.
- **Static HTML output.** No framework, no CDN, no server: the page and its
  three PNG charts are files that will still open in ten years.
- **Tests on the transform.** Three pytest checks: no missing categories or
  areas after cleaning; tidy rows plus dropped duplicates reconcile with
  the raw count; the months in the tidy data match the extract manifest.

## Data notes and caveats

- police.uk data is published with a lag of roughly two months; this run
  covers June-August 2026.
- Street-level locations are anonymised: each crime is snapped to a point
  on a map of anonymous locations, so "on or near" a named street does not
  mean the crime happened at an exact address there.
- These are *recorded* crimes only. Reporting and recording practices
  differ between police forces, and busy commercial areas (like Bank)
  record more crime partly because far more people pass through them.
  Treat the numbers as a comparison aid, not a safety score.

## What I'd explore next

- Add outcome data (the API's crime-outcomes endpoint) to show what share
  of crimes in each area reach an outcome, not just volumes.
- Normalise by resident population and footfall, so areas are compared on
  rates rather than raw counts.
- Add a scheduled incremental load (new month appended each release) and
  move the transform into a warehouse-style layered model - the point at
  which tools like dbt would earn their place.
- Let a user drop a pin anywhere rather than choosing from four points,
  with a small map view.

## A note on AI assistance

I used AI tools while building this project to draft boilerplate code and
help debug errors. The choices that shape the result - the dataset and
locations, the data model, the de-duplication decision, the validation
checks, and this write-up - are mine, and I reviewed and ran every part of
the pipeline before including it.
