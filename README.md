# Batch Submission of `pytom-match-pick` from RELION5 jobs

This script automates the batch submission of [pytom-match-pick](https://github.com/SBC-Utrecht/pytom-match-pick) jobs on an HPC cluster using SLURM. It reads [RELION5](https://github.com/3dem/relion/tree/ver5.0) tomogram reconstruction metadata (tilt angles, defocus, exposures) directly from `.star` files and uses these for template matching the respective tomograms. Enabling per-tilt weighting and CTF phase-flip models by default. You can run a dry‑run without actual submission to check the bash scripts and limit processing to a subset of tomograms via a `tomolist`.

## Features

- **Automatic SLURM script generation** to run template matching on each tomogram
- **Reads tilt, defocus, and exposure** values from RELION5 `.star` files

## Usage

Provide the RELION5 tomogram and `.star` directories plus the usual PyTom flags (template, mask, etc.), and the script will batch‑submit jobs:

```bash
python batch_pytom.py \
  --mrc-dir /path/to/Tomograms/jobXXX/tomograms \
  --star-dir /path/to/Tomograms/jobXXX/ \
  -t /path/to/template.mrc \
  -m /path/to/mask.mrc \
  [--particle-diameter 140 | --angular-search 7] \ # either or
  -s 2 2 1 \
  --voxel-size 9.68 \
  -g 0 \
  --random-phase-correction \
  --rng-seed 69 \
  --per-tilt-weighting \
  --non-spherical-mask \
  --tomogram-ctf-model phase-flip \
  [--dry-run]
```

- **`--dry-run`**: generate SLURM scripts without submitting
- **`--tomolist`**: file listing tomogram IDs (one per line)
- **SLURM options** (partition, ntasks, cpus, mem, time) can be customized via flags

### Example terminal output

```
Processing tomograms: ['3', '5', '5_2', '2', '1', '4']

Validation for First Tomogram:
  Tilt   : [-53.6, 54.39]
  Defocus: [4.14, 4.36]
  Exposure: [0.0, 108.0]
  STAR    : Position_3.star
  MRC     : tomograms/rec_Position_3.mrc
  Mask    : None

Generated sbatch script for 3 at submission/tomo_3/submit_3.sh
Submitted submission/tomo_3/submit_3.sh: Submitted batch job 41548312
... (and so on for each tomogram)
```

#### Example of one of the generated submission script

```bash
#!/bin/bash -l

#SBATCH -o pytom.out%j
#SBATCH -D ./
#SBATCH -J pytom_1
#SBATCH --partition=emgpu
#SBATCH --ntasks=1
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mail-type=none
#SBATCH --mem=128G
#SBATCH --qos=emgpu
#SBATCH --time=05:00:00

ml purge
ml pytom-match-pick

pytom_match_template.py \
  -v ../../../rln5/Tomograms/job017/tomograms/rec_Position_1.mrc \
  -a submission/tomo_1/1.tlt \
  --dose-accumulation submission/tomo_1/1_exposure.txt \
  --defocus submission/tomo_1/1_defocus.txt \
  -t ../tmpl.mrc \
  -d submission/tomo_1 \
  -m ../mask.mrc \
  --angular-search 7 \
  -s 2 2 1 \
  --voxel-size-angstrom 9.68 \
  -r \
  --rng-seed 69 \
  -g 0 \
  --amplitude-contrast 0.07 \
  --spherical-aberration 2.7 \
  --voltage 300 \
  --z-axis-rotational-symmetry 4 \
  --per-tilt-weighting \
  --tomogram-ctf-model phase-flip \
  --non-spherical-mask
```

## Full help output

Usage and options (run `python batch_pytom.py -h` to see defaults and descriptions):

```
usage: batch_pytom.py [-h] --mrc-dir MRC_DIR --star-dir STAR_DIR [--bmask-dir BMASK_DIR] [--tomolist TOMOLIST]
              [--output-dir OUTPUT_DIR] [--dry-run] [--no-tomogram-mask] [--validate-only]
              -t TEMPLATE -m MASK [--particle-diameter PARTICLE_DIAMETER] [--angular-search ANGULAR_SEARCH]
              [-s X Y Z] --voxel-size VOXEL_SIZE [-g GPU_IDS [GPU_IDS ...]] [--random-phase-correction]
              [--rng-seed RNG_SEED] [--per-tilt-weighting] [--non-spherical-mask] [--spectral-whitening]
              [--tomogram-ctf-model {phase-flip,wiener}]
              [--z-axis-rotational-symmetry Z_AXIS_ROTATIONAL_SYMMETRY] [--amplitude-contrast AMPLITUDE_CONTRAST]
              [--spherical-aberration SPHERICAL_ABERRATION] [--voltage VOLTAGE] [--low-pass LOW_PASS]
              [--high-pass HIGH_PASS] [--partition PARTITION] [--ntasks NTASKS] [--nodes NODES]
              [--ntasks-per-node NTASKS_PER_NODE] [--cpus-per-task CPUS_PER_TASK] [--gres GRES]
              [--mail-type MAIL_TYPE] [--mem MEM] [--qos QOS] [--time TIME]

Batch-submit PyTom template-matching for RELION5 tomograms

options:
  -h, --help            show this help message and exit
  --mrc-dir MRC_DIR     Directory for .mrc tomograms
  --star-dir STAR_DIR   Directory for .star metadata
  --bmask-dir BMASK_DIR
                        Directory for tomogram masks (default: none)
  --tomolist TOMOLIST   File listing tomogram IDs, one per line (default: use all in --mrc-dir)
  --output-dir OUTPUT_DIR
                        Where to write scripts/results (default: submission)
  --dry-run             Only generate scripts, do not submit
  --no-tomogram-mask    Ignore masks even if provided
  --validate-only       Validate first tomogram and exit
  -t TEMPLATE, --template TEMPLATE
                        Template MRC file (default: none)
  -m MASK, --mask MASK  Mask MRC file (default: none)
  --particle-diameter PARTICLE_DIAMETER
                        Particle diameter in Å for angular sampling (default: none)
  --angular-search ANGULAR_SEARCH
                        Override angular search (float or .txt; default: none)
  -s X Y Z, --volume-split X Y Z
                        Split volume into X Y Z blocks (default: none)
  --voxel-size VOXEL_SIZE
                        Voxel size in Å (default: none)
  -g GPU_IDS [GPU_IDS ...], --gpu-ids GPU_IDS [GPU_IDS ...]
                        GPU IDs to use (e.g. 0 1; default: ['0'])
  --random-phase-correction
                        Enable random phase correction
  --rng-seed RNG_SEED   Random seed for phase-correction (default: 69)
  --per-tilt-weighting  Enable per-tilt weighting
  --non-spherical-mask   Enable non‑spherical mask
  --spectral-whitening   Enable spectral whitening
  --tomogram-ctf-model {phase-flip,wiener}
                        CTF model (default: none)
  --z-axis-rotational-symmetry Z_AXIS_ROTATIONAL_SYMMETRY
                        Z‑axis symmetry (integer; default: none)
  --amplitude-contrast AMPLITUDE_CONTRAST
                        Amplitude contrast fraction (default: 0.07)
  --spherical-aberration SPHERICAL_ABERRATION
                        Spherical aberration in mm (default: 2.7)
  --voltage VOLTAGE     Voltage in kV (default: 300)
  --low-pass LOW_PASS   Low-pass filter Å (default: none)
  --high-pass HIGH_PASS
                        High-pass filter Å (default: none)
  --partition PARTITION
                        SLURM partition (default: emgpu)
  --ntasks NTASKS       SLURM ntasks (default: 1)
  --nodes NODES         SLURM nodes (default: 1)
  --ntasks-per-node NTASKS_PER_NODE
                        SLURM tasks/node (default: 1)
  --cpus-per-task CPUS_PER_TASK
                        SLURM cpus/task (default: 4)
  --gres GRES           SLURM gres (default: gpu:1)
  --mail-type MAIL_TYPE
                        SLURM mail-type (default: none)
  --mem MEM             SLURM memory in GB (default: 128)
  --qos QOS             SLURM QoS (default: emgpu)
  --time TIME           SLURM time limit (hh:mm:ss; default: 05:00:00)
```

