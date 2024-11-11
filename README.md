
# Batch Submission of `pytom-match-pick` Jobs

This script facilitates the batch submission of [pytom-match-pick](https://github.com/SBC-Utrecht/pytom-match-pick) jobs on a high-performance computing (HPC) cluster using SLURM. It reads [RELION5](https://github.com/3dem/relion/tree/ver5.0) reconstruction metadata for template matching. The script guides you through input prompts to configure necessary parameters and generate corresponding SLURM submission scripts.

## Features

- Automated SLURM job script generation for each tomogram
- Interactive prompts to gather all necessary input paths and parameters
- Sanity check for tilt, defocus, and exposure values on the first tomogram
- Optional tomogram mask usage for template matching
- Parameter validation and SLURM submission tracking

## Requirements

- Python 3.x
- `starfile` library for reading `.star` files
- `prompt_toolkit` for interactive prompts
- Access to SLURM for job submission

## Installation

Ensure you have the required libraries installed:
```bash
pip install starfile prompt_toolkit os glob subprocess re
```

## Usage

To execute the script, use:
```bash
python cli.py
```

### Example Workflow

1. **Starting the Script**
   ```bash
   python cli.py
   ```

2. **Following the Prompts**

   Example session:
   ```text
   Enter the path to the tomolist file []: tomolist.txt

   Tomogram numbers: ['1', '2', '6', '8', '9', '10', '13', '15', '17']
   Is the list of tomograms correct? ([y]es/[n]o): y

   Enter the directory path for RELION5 `.star` files []: ../Tomograms/No_halfset_tomo_aretomo/tilt_series

   Enter the directory path for RELION5 tomogram files (.mrc) []: ../Tomograms/No_halfset_tomo_aretomo/tomograms

   Do you want to use tomogram masks? ([y]es/[n]o): y

   Enter the directory for tomogram masks (e.g., path/to/bmask_*.mrc): ../bmask

   *Sanity Check for your First Tomogram checking Min and Max values*

   *Tilt values: [-40.01, 57.99]*
   *Defocus values: [1.36, 2.03]*
   *Exposure values: [100.0, 96.0]*
   *.star File: ../Tomograms/No_halfset_tomo_aretomo/tilt_series/Position_1.star*
   *.mrc File: ../Tomograms/No_halfset_tomo_aretomo/tomograms/rec_Position_1.mrc*

   Are these values correct for the first tomogram? ([y]es/[n]o): y

   --- Pytom Parameters ---

   Enter the template file path (Required): tmpl.mrc

   Enter the mask file path (Required): mask.mrc

   Enter particle diameter in Angstrom (Required if not specifying angular search): 140

   Enter voxel size in Angstrom (Required): 7.92

   Enter GPU IDs (Required): 0

   Enable random-phase correction? (recommended) ([y]es/[n]o): y

   Enter random seed (default: 69): 69

   Enable per-tilt-weighting? ([y]es/[n]o): y

   Enable non-spherical mask? ([y]es/[n]o): n

   Enable spectral whitening? ([y]es/[n]o): n

   Enter z-axis rotational symmetry as integer (PRESS ENTER TO SKIP): 4

   Amplitude contrast (ENTER = default: 0.07): 0.07

   Spherical aberration in mm (ENTER = default: 2.7): 2.7

   Acceleration voltage in kV (ENTER = default: 300): 300

   Low-pass filter (PRESS ENTER TO SKIP): 

   High-pass filter (PRESS ENTER TO SKIP): 

   --- SLURM Settings ---

   Default SLURM settings are:
   - partition: rtx4090-em
   - ntasks: 1
   - nodes: 1
   - ntasks_per_node: 1
   - cpus_per_task: 4
   - gres: gpu:1
   - mail_type: none
   - mem: 128
   - qos: emgpu
   - time: 06:00:00

   Do you want to use the default SLURM settings? ([y]es/[n]o): y
   ```

## Parameter Details

### Script Parameters

| Parameter | Description |
| --------- | ----------- |
| **Template File** | Path to the template file (required). |
| **Mask File** | Path to the mask file (required). |
| **Particle Diameter** | Particle diameter in Angstroms. If not specified, angular search value is required. |
| **Voxel Size** | Voxel size in Angstroms (required). |
| **GPU IDs** | IDs of GPUs to use (required). |
| **Random-Phase Correction** | Enable random-phase correction (recommended). |
| **Per-Tilt Weighting** | Enable weighting per tilt. |
| **Non-Spherical Mask** | Enable non-spherical mask usage. |
| **Spectral Whitening** | Enable spectral whitening of data. |
| **Z-Axis Rotational Symmetry** | Z-axis rotational symmetry as an integer. |
| **Amplitude Contrast** | Amplitude contrast (default: 0.07). |
| **Spherical Aberration** | Spherical aberration in mm (default: 2.7). |
| **Acceleration Voltage** | Acceleration voltage in kV (default: 300). |
| **Low-Pass Filter** | Optional low-pass filter. |
| **High-Pass Filter** | Optional high-pass filter. |

### SLURM Parameters

| Parameter | Default Value | Description |
| --------- | ------------- | ----------- |
| **partition** | rtx4090-em | SLURM partition. |
| **ntasks** | 1 | Number of tasks. |
| **nodes** | 1 | Number of nodes. |
| **ntasks_per_node** | 1 | Tasks per node. |
| **cpus_per_task** | 4 | CPUs per task. |
| **gres** | gpu:1 | GPU resources. |
| **mail_type** | none | Email notification type. |
| **mem** | 128 | Memory allocation in GB. |
| **qos** | emgpu | Quality of Service. |
| **time** | 06:00:00 | Time limit for the job. |

Once all parameters are set, the script will generate and submit SLURM scripts for each tomogram in the list.
