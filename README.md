# exiD On-Ramp Merging Behavior Analysis

A reproducible notebook workflow for identifying on-ramp merging vehicles in the exiD trajectory dataset and analyzing their behavior from three perspectives:

- **Safety:** Potential Collision Avoidance Difficulty (PCAD) and critical surrounding-vehicle positions.
- **Efficiency:** longitudinal speed during the merging maneuver.
- **Comfort:** longitudinal and lateral jerk.

The workflow also supports unsupervised behavior clustering and an optional experiment for LLM-based interpretation of time-series metrics.

> This repository contains analysis code only. The exiD dataset is not redistributed and must be obtained separately under its own terms of use.

## Repository structure

```text
.
├── .github/workflows/validate.yml
├── data/                         # Local exiD CSV files; ignored by Git
├── figures/                      # Generated figures; ignored by Git
├── results/                      # Generated tables and models; ignored by Git
├── workflow/
│   ├── 01_extract_merging_vehicles.ipynb
│   ├── 02_compute_metrics.ipynb
│   ├── 03_combine_recording_summaries.ipynb
│   ├── 04_clean_data.ipynb
│   ├── 05_cluster_merging_behaviors.ipynb
│   ├── 06_llm_temporal_interpretation.ipynb
│   ├── pcad_python.py
│   └── tracks_import.py
├── WORKFLOW.md
└── requirements.txt
```

## Data preparation

Download exiD v2.1 separately and place the extracted CSV files in `data/`. The workflow expects the original recording names:

```text
data/
├── 00_tracks.csv
├── 00_tracksMeta.csv
├── 00_recordingMeta.csv
├── ...
├── 92_tracks.csv
├── 92_tracksMeta.csv
└── 92_recordingMeta.csv
```

Do not commit the dataset to GitHub. The included `.gitignore` excludes `data/` contents and generated results.

## Installation

Python 3.10 or 3.11 is recommended.

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
jupyter lab
```

On macOS or Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
jupyter lab
```

Start Jupyter from the repository root so that all relative paths resolve consistently.

## Running the analysis

Run the notebooks in numerical order, with one exception: notebook 03 is only needed when recording-level files were produced separately.

1. `01_extract_merging_vehicles.ipynb` identifies vehicles that traverse the location-specific merging lanelet and at least one additional lanelet.
2. `02_compute_metrics.ipynb` transforms ego–neighbor states into an ego-aligned frame, computes frame-level PCAD, and summarizes safety, efficiency, and comfort indicators.
3. `03_combine_recording_summaries.ipynb` is an optional recovery/parallel-processing utility that combines separately generated recording summaries.
4. `04_clean_data.ipynb` detects persistent heading inconsistencies and likely right-censored short trajectories.
5. `05_cluster_merging_behaviors.ipynb` standardizes selected features, evaluates candidate cluster counts, fits K-means, and creates behavior-profile figures.
6. `06_llm_temporal_interpretation.ipynb` is optional and requires a separately prepared long-format temporal-metric table plus an OpenAI API key.

See [WORKFLOW.md](WORKFLOW.md) for exact inputs, outputs, configuration points, and validation checks.

## Full-batch and test runs

Notebook 02 is configured for a full run with:

```python
test_recording_id = None
test_num_vehicles = None
```

For a quick check, set `test_recording_id` to one recording number, such as `58`, and optionally set `test_num_vehicles` to a small integer. When processing recordings separately, use notebook 03 to create the combined summary before continuing to data cleaning.

PCAD is computationally expensive because it performs nested coarse, intermediate, and fine searches for every valid ego–neighbor state. A complete run can therefore take substantial time.

## Optional LLM experiment

Notebook 06 is intentionally separate from the main clustering pipeline. Before running it, provide:

```powershell
$env:OPENAI_API_KEY="your-key"
$env:OPENAI_MODEL="a-model-available-to-your-API-account"
```

The notebook expects `results/temporal_metrics_all_vehicles.csv` with vehicle identity, time or frame, PCAD, longitudinal velocity, longitudinal jerk, and lateral jerk columns. API usage may incur cost. Review the table before transmission and do not include confidential or personally identifying information.

## Reproducibility notes

- K-means uses a fixed random seed (`42`).
- Frame rate is read from recording metadata, with `25 Hz` used as a fallback.
- The lanelet mapping is specific to exiD recordings `00`–`92`.
- Cluster identifiers are arbitrary labels and should be interpreted from their feature profiles, not their numeric order.
- The GitHub Actions workflow validates notebook structure and Python imports without downloading or executing the exiD dataset.

## Data and code attribution

If this repository is used in academic work, cite the exiD dataset paper and follow the dataset provider's citation and licensing requirements:

> Moers, T., Vater, L., Krajewski, R., Bock, J., Zlocki, A., & Eckstein, L. (2022). The exiD Dataset: A Real-World Trajectory Dataset of Highly Interactive Highway Scenarios in Germany. *2022 IEEE Intelligent Vehicles Symposium (IV)*, 958–964. https://doi.org/10.1109/IV51971.2022.9827305

The data-loading utilities originated from the exiD/drone-dataset-tools ecosystem and should retain any applicable upstream attribution and license notices.

## License

No license is assigned in this preparation package. Before publishing, add a license only after confirming compatibility with the upstream drone-dataset-tools license, the exiD terms of use, and any university requirements.

## Published results

A curated, publication-safe subset is available in [`results/`](results/) and [`figures/`](figures/). It includes cluster-level aggregate statistics, selected case-study figures, and the prompts and interpretations used in the qualitative analysis.

Raw frame-level PCAD outputs and per-recording or per-vehicle tables are not uploaded because the exiD licence prohibits redistribution of the dataset or recoverable modified data. Keeping those large intermediate files out of GitHub also keeps the repository practical to clone. See [`results/README.md`](results/README.md) for the complete inclusion and exclusion policy.
