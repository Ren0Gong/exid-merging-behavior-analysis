# Curated results

This directory contains a publication-safe subset of the thesis results. It is intentionally limited to aggregate statistics and textual research artifacts that do not reproduce the underlying exiD trajectory data.

## Included

- `cluster_profile_summary.csv` — cluster-level means and sample standard deviations, plus the modal critical-vehicle position. It contains no recording, lanelet, track, or frame identifiers.
- `case_study_prompt.txt` and `cluster_interpretation_prompt.txt` — prompts used for the reported qualitative interpretation.
- `*_case_*.md` and `clustering_*.txt` — model-generated and manual interpretations retained as research artifacts.
- Selected case-study visualizations are stored in `../figures/`. They are abstract figures rather than source trajectories or tabular vehicle records.

## Why the other result files are not uploaded

The complete local results directory is about 352 MB. Most of that size is the `raw/` directory (about 333 MB), which contains frame-level PCAD values and links between recordings, tracks, neighbouring vehicles, and critical vehicles. The omitted summary and diagnostic tables also contain per-recording or per-vehicle rows.

Those files are not included for two reasons:

1. The exiD licence does not permit redistribution of the dataset or modified versions from which the underlying data could be recovered. Only sufficiently abstract derivative results are suitable for publication.
2. Raw and intermediate outputs would make the repository unnecessarily large. The notebooks in this repository regenerate them locally for authorised exiD users.

Accordingly, this repository does **not** include the original exiD dataset, frame-level outputs, per-recording tables, per-vehicle tables, temporary files, or caches. The complete outputs remain in the local research workspace and can be reproduced by running the documented workflow with a separately obtained exiD copy.

## Source and citation

The source dataset is the [exiD dataset](https://levelxdata.com/). Users must obtain it separately and comply with its licence. When using this work, also cite the exiD paper:

> Moers, T., Vater, L., Krajewski, R., Bock, J., Zlocki, A., & Eckstein, L. (2022). The exiD Dataset: A Real-World Trajectory Dataset of Highly Interactive Highway Scenarios in Germany. *2022 IEEE Intelligent Vehicles Symposium (IV)*. https://doi.org/10.1109/IV51971.2022.9827305
