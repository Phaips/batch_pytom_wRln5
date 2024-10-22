# Batch Submission of `pytom-match-pick` Jobs

This script allows for the batch submission of `pytom-match-pick` jobs using a tomolist—a text file containing each tomogram number you want to run template matching on (one tomogram number per line). The script will guide you through input prompts to configure the necessary parameters for running `pytom` jobs and generating corresponding SLURM submission scripts for a high-performance computing (HPC) cluster.

## Requirements

- Python 3.x
- `starfile` library for reading `.star` files
- `prompt_toolkit` for interactive user inputs
- Access to SLURM for job submission

## Usage

Run the script:

```bash
python cli.py
