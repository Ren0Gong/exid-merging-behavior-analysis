# Analysis workflow

This document describes the dependency chain, files, configuration points, and checks needed to reproduce the analysis.

## Pipeline overview

```text
exiD recording CSV files
        |
        v
01 Extract merging vehicles
        |
        v
02 Compute frame-level PCAD and vehicle-level metrics
        |
        +------------------------------+
        |                              |
        v                              v
raw temporal PCAD                 vehicle summaries
                                       |
                      03 optional combine step
                                       |
                                       v
                              04 Data cleaning
                                       |
                                       v
                              05 K-means clustering
                                  /          \
                                 v            v
                         cluster figures   clustered table

06 LLM temporal interpretation is an optional, separate branch that requires
a purpose-built long-format temporal-metric CSV.
```

## Inputs and outputs

| Step | Notebook | Main input | Main output |
|---|---|---|---|
| 1 | `01_extract_merging_vehicles.ipynb` | `data/NN_tracks.csv`, `NN_tracksMeta.csv`, `NN_recordingMeta.csv` | `results/summary/exid_merging_vehicle_summary.csv` |
| 2 | `02_compute_metrics.ipynb` | exiD CSVs and the merging-vehicle summary | `results/summary/exid_metrics_summary_all_recordings.csv`; `results/raw/exid_all_merging_vehicle_pcad_raw.csv` |
| 3 | `03_combine_recording_summaries.ipynb` | `results/summary/exid_metrics_summary_recording_NN.csv` | `results/summary/exid_metrics_summary_all_recordings.csv` |
| 4 | `04_clean_data.ipynb` | combined summary and original trajectories | cleaned summary, diagnostics, and excluded-vehicle table under `results/summary/` |
| 5 | `05_cluster_merging_behaviors.ipynb` | `exid_metrics_summary_all_recordings_cleaned.csv` | clustered CSV under `results/summary/`; plots under `figures/` |
| 6 | `06_llm_temporal_interpretation.ipynb` | `results/temporal_metrics_all_vehicles.csv` | `results/llm_interpretations_pilot.jsonl` |

Step 3 is an alternative aggregation path, not an additional transformation. Skip it after a successful full-batch Step 2 run.

## Step 1 — Merging-vehicle extraction

The extraction logic uses a fixed recording-to-merging-lanelet mapping:

| Recordings | Merging lanelet ID |
|---|---:|
| 00–18 | 1754 |
| 19–38 | 1966 |
| 39–52 | 1494 |
| 53–60 | 1408 |
| 61–72 | 1469 |
| 73–77 | 1405 |
| 78–92 | 1455 |

A vehicle is selected when its trajectory includes the location's merging lanelet and at least one other lanelet. This operational definition should be reported when using the extracted sample.

Validation checks:

- All three source files exist for every intended recording.
- Recording IDs are within `00`–`92`.
- The resulting table contains unique recording IDs and list-valued merging vehicle IDs.
- Unexpected zero-vehicle recordings are inspected rather than silently removed.

## Step 2 — Metric computation

For every selected ego vehicle and frame, the notebook:

1. reads the ego state and up to eight surrounding-position fields;
2. parses single or semicolon-separated neighbor IDs;
3. transforms ego and neighbor positions, velocities, and accelerations into a common ego-aligned coordinate frame;
4. computes PCAD for each valid ego–neighbor pair;
5. retains the highest PCAD within each positional relationship;
6. aggregates safety, speed, jerk, critical-position frequency, and position-switch indicators at maneuver level.

Important configuration:

```python
test_recording_id = None       # all recordings
test_num_vehicles = None       # all selected vehicles
save_raw_pcad = True
stop_on_error = True
```

Use a single recording during development. Restore `None` before producing the full results.

Validation checks:

- Output row count equals the total number of selected merging vehicles unless errors are explicitly recorded.
- `status` is `ok` for retained observations.
- PCAD values are finite and non-negative.
- Frame order is monotonic within each recording/vehicle pair.
- Negative longitudinal velocity and persistent heading reversals are deferred to Step 4 rather than altered silently.

## Step 3 — Optional aggregation

Use this notebook only after running Step 2 separately for multiple recordings. It selects one canonical file per recording, checks schema consistency, sorts rows, reports duplicate vehicle keys, reports missing recording IDs, and writes a combined table.

Do not combine test files containing `_firstN` suffixes with full recording summaries.

## Step 4 — Data cleaning

The cleaning notebook diagnoses two main issues:

- **Heading inconsistency:** a persistent difference of at least `150°` between motion direction and reported heading in at least `80%` of checked moving frames.
- **Likely right censoring:** a maneuver shorter than `5 s` that ends within `2` frames of the recording boundary.

Frames below `2 m/s` are excluded from heading-consistency checks because motion direction is unstable near standstill. Short duration alone does not cause exclusion.

Always retain and publish the diagnostics and excluded-vehicle tables alongside the analysis code, even when the underlying exiD trajectories cannot be redistributed.

## Step 5 — Clustering

The release notebook keeps the final K-means workflow and removes exploratory duplicate K-means/Gaussian-mixture blocks. It uses:

- median imputation and standardization for numerical features;
- one-hot encoding for `dominant_critical_position`;
- silhouette, Davies–Bouldin, and Calinski–Harabasz scores for candidate cluster counts;
- `random_state = 42` and repeated K-means initialization;
- PCA only for visualization, not for fitting the clusters.

If a fixed cluster count is required for exact thesis reproduction, set `manual_k` explicitly and document the value. Do not attach behavioral meaning to cluster numbers until the profile tables and distributions have been examined.

## Step 6 — Optional LLM interpretation

This experiment does not consume the vehicle-level clustering table. It needs a long-format table with one row per time point and columns corresponding to:

- recording and vehicle identifiers;
- time in seconds or frame number;
- frame-level PCAD;
- critical position;
- longitudinal velocity;
- longitudinal jerk;
- lateral jerk.

The notebook requires `OPENAI_API_KEY` and `OPENAI_MODEL` environment variables. It uses structured JSON output, starts with a limited pilot, and does not store responses through the API request. Record the exact model name, date, prompt, sampling/reasoning configuration, failed calls, and token usage in any reproducibility statement.

## Release checklist

Before publishing the repository:

- [ ] Confirm all notebooks run from the repository root in a fresh environment.
- [ ] Run Step 2 on one recording before the full batch.
- [ ] Remove notebook outputs that expose local paths, keys, or large tables.
- [ ] Confirm no API keys, OneDrive paths, dataset files, model binaries, caches, or generated archives are tracked.
- [ ] Add author names, thesis title, repository URL, and an approved software license.
- [ ] Add the final thesis citation or DOI when available.
- [ ] Preserve upstream attribution for `tracks_import.py` and any other reused utilities.
- [ ] Create a tagged release for the exact code used in the thesis.
