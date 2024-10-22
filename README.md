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
````

## Example

````
> python cli.py

Enter the path to the tomolist file []: **tomolist.txt**

Tomogram numbers: ['1', '2', '6', '8', '9', '10', '13', '15', '17']

Is the list of tomograms correct? ([y]es/[n]o): **y**

Enter the directory path for RELION5 `.star` files []: **../Tomograms/No_halfset_tomo_aretomo/tilt_series**

Enter the directory path for RELION5 tomogram files (.mrc) []: **../Tomograms/No_halfset_tomo_aretomo/tomograms**

Do you want to use tomogram masks? ([y]es/[n]o): **y**

Enter the directory for tomogram masks (e.g., path/to/bmask_*.mrc): []: **../bmask**

*Sanity Check for your First Tomogram checking Min and Max values*

*Tilt values: [-40.01, 57.99]*

*Defocus values: [1.36, 2.03]*

*Exposure values: [100.0, 96.0]*

*.star File: ../Tomograms/No_halfset_tomo_aretomo/tilt_series/Position_1.star*

*.mrc File: ../Tomograms/No_halfset_tomo_aretomo/tomograms/rec_Position_1.mrc*

Are these values correct for the first tomogram? ([y]es/[n]o): **y**

--- Pytom Parameters ---

Enter the template file path (Required): []: **tmpl.mrc**

Enter the mask file path (Required): []: **mask.mrc**

Enter particle diameter in Angstrom (Required if not specifying angular search): []: **140**

Enter voxel size in Angstrom (Required): []: **7.92**

Enter GPU IDs (Required): []: **0**

Enable random-phase correction? (recommended) ([y]es/[n]o): **y**

Enter random seed (default: 69): [69]: **69**

Enable per-tilt-weighting? ([y]es/[n]o): **y**

Enable non-spherical mask? ([y]es/[n]o): **n**

Enable spectral whitening? ([y]es/[n]o): **n**

Enter z-axis rotational symmetry as integer (PRESS ENTER TO SKIP): []: **4**

Amplitude contrast (ENTER = default: 0.07): [0.07]: **0.07**

Spherical aberration in mm (ENTER = default: 2.7): [2.7]: **2.7**

Acceleration voltage in kV (ENTER = default: 300): [300]: **300**

Low-pass filter (PRESS ENTER TO SKIP): []:

High-pass filter (PRESS ENTER TO SKIP): []:

--- SLURM Settings ---

Default SLURM settings are:

- partition: rtx4090
- ntasks: 1
- nodes: 1
- ntasks_per_node: 1
- cpus_per_task: 4
- gres: gpu:1
- mail_type: none
- mem: 128
- qos: gpu6hours
- time: 06:00:00

Do you want to use the default SLURM settings? ([y]es/[n]o): **y**
