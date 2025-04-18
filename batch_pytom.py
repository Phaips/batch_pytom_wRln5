#!/usr/bin/env python3
import os
import glob
import starfile
import argparse
import subprocess
from pathlib import Path

def parse_id_from_filename(filename):
    """Parses the numeric ID portion from the filename, removing recognized prefixes."""
    base = os.path.splitext(os.path.basename(filename))[0]
    for prefix in ['rec_Position_', 'Position_']:
        if base.startswith(prefix):
            return base[len(prefix):]
    return base

def find_files_with_exact_number(directory, tomo_num, extension):
    """Find files that match the exact tomogram number after removing prefixes."""
    files = glob.glob(os.path.join(directory, f"*.{extension}"))
    matched_files = []
    for f in files:
        parsed_id = parse_id_from_filename(os.path.basename(f))
        if parsed_id == tomo_num:
            matched_files.append(f)
    return matched_files

def find_matching_files(tomo_num, star_dir, mrc_dir, bmask_dir=None):
    """Find matching star, mrc and optional bmask files for a tomogram number."""
    star_files = find_files_with_exact_number(star_dir, tomo_num, 'star')
    mrc_files  = find_files_with_exact_number(mrc_dir, tomo_num, 'mrc')

    if not star_files or not mrc_files:
        raise FileNotFoundError(f"No .star or .mrc for {tomo_num}")
    if len(star_files)>1 or len(mrc_files)>1:
        print(f"Warning: multiple matches for {tomo_num}, using first")

    bmask_file = None
    if bmask_dir:
        bmask_files = find_files_with_exact_number(bmask_dir, tomo_num, 'mrc')
        if bmask_files:
            bmask_file = bmask_files[0]
        else:
            print(f"Warning: no mask for {tomo_num}")

    return star_files[0], mrc_files[0], bmask_file

def read_star_file(file_path):
    """Extract tilt angles, defocus values, and exposures from a star file."""
    try:
        df = starfile.read(file_path)
        tilt_angles   = df["rlnTomoNominalStageTiltAngle"].tolist()
        defocus_vals  = ((df["rlnDefocusU"] + df["rlnDefocusV"]) / 20000).tolist()
        exposures     = df["rlnMicrographPreExposure"].tolist()
        return tilt_angles, defocus_vals, exposures
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return [], [], []

def create_temp_files(tomogram_num, tilt_angles, defocus_values, exposures, output_dir):
    """Create temporary tilt, defocus, and exposure files for PyTom input."""
    tlt = os.path.join(output_dir, f"{tomogram_num}.tlt")
    dfx = os.path.join(output_dir, f"{tomogram_num}_defocus.txt")
    exp = os.path.join(output_dir, f"{tomogram_num}_exposure.txt")

    with open(tlt, 'w') as f:
        for a in tilt_angles: f.write(f"{a}\n")
    with open(dfx, 'w') as f:
        for d in defocus_values: f.write(f"{d}\n")
    with open(exp, 'w') as f:
        for e in exposures: f.write(f"{e}\n")

    return tlt, dfx, exp

def create_sbatch_script(tomo, tlt, dfx, exp, tomo_file, bmask, outdir, args):
    """Generate an SBATCH script for PyTom template matching."""
    script = os.path.join(outdir, f"submit_{tomo}.sh")
    with open(script, 'w') as f:
        f.write(f"""#!/bin/bash -l

#SBATCH -o pytom.out%j
#SBATCH -D ./
#SBATCH -J pytom_{tomo}
#SBATCH --partition={args.partition}
#SBATCH --ntasks={args.ntasks}
#SBATCH --nodes={args.nodes}
#SBATCH --ntasks-per-node={args.ntasks_per_node}
#SBATCH --cpus-per-task={args.cpus_per_task}
#SBATCH --gres={args.gres}
#SBATCH --mail-type={args.mail_type}
#SBATCH --mem={args.mem}G
#SBATCH --qos={args.qos}
#SBATCH --time={args.time}

ml purge
ml pytom-match-pick

pytom_match_template.py \\
-v {tomo_file} \\
-a {tlt} \\
--dose-accumulation {exp} \\
--defocus {dfx} \\
-t {args.template} \\
-d {outdir} \\
-m {args.mask} \\
""")

        if args.particle_diameter:
            f.write(f"--particle-diameter {args.particle_diameter} \\\n")
        elif args.angular_search:
            f.write(f"--angular-search {args.angular_search} \\\n")

        if bmask and not args.no_tomogram_mask:
            f.write(f"--tomogram-mask {bmask} \\\n")

        if args.volume_split:
            x, y, z = args.volume_split
            f.write(f"-s {x} {y} {z} \\\n")

        f.write(f"--voxel-size-angstrom {args.voxel_size} \\\n")

        if args.random_phase_correction:
            f.write("-r \\\n")
            f.write(f"--rng-seed {args.rng_seed} \\\n")

        gpu_str = ' '.join(args.gpu_ids)
        f.write(f"-g {gpu_str} \\\n")

        f.write(f"--amplitude-contrast {args.amplitude_contrast} \\\n")
        f.write(f"--spherical-aberration {args.spherical_aberration} \\\n")
        f.write(f"--voltage {args.voltage} \\\n")

        if args.z_axis_rotational_symmetry:
            f.write(f"--z-axis-rotational-symmetry {args.z_axis_rotational_symmetry} \\\n")
        if args.per_tilt_weighting:
            f.write("--per-tilt-weighting \\\n")
        if args.tomogram_ctf_model:
            f.write(f"--tomogram-ctf-model {args.tomogram_ctf_model} \\\n")
        if args.non_spherical_mask:
            f.write("--non-spherical-mask \\\n")
        if args.spectral_whitening:
            f.write("--spectral-whitening \\\n")
        if args.low_pass:
            f.write(f"--low-pass {args.low_pass} \\\n")
        if args.high_pass:
            f.write(f"--high-pass {args.high_pass} \\\n")

    print(f"Generated sbatch script for {tomo} at {script}")
    return script

def submit_sbatch(script_path, dry_run=False):
    """Submit an SBATCH script or just print the command in dry-run mode."""
    if dry_run:
        print(f"Would submit: sbatch {script_path}")
        return
    try:
        result = subprocess.run(['sbatch', script_path], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Submitted {script_path}: {result.stdout.strip()}")
        else:
            print(f"Error submitting {script_path}: {result.stderr.strip()}")
    except Exception as e:
        print(f"Submission exception: {e}")

def get_tomogram_numbers(args):
    """Get list of tomogram numbers from either tomolist file or directory scan."""
    if args.tomolist:
        with open(args.tomolist) as f:
            nums = [l.strip() for l in f if l.strip()]
    else:
        mrcs = glob.glob(os.path.join(args.mrc_dir, "*.mrc"))
        nums = {parse_id_from_filename(os.path.basename(m)) for m in mrcs}
    return list(nums)

def validate_first_tomogram(tomo, star_dir, mrc_dir, bmask_dir, use_mask):
    """Validate the first tomogram to ensure all data can be accessed properly."""
    try:
        star, tomo_file, bmask = find_matching_files(
            tomo, star_dir, mrc_dir, bmask_dir if use_mask else None
        )
        tilts, defs, exps = read_star_file(star)
        if not (tilts and defs and exps):
            print("Error: missing tilt/defocus/exposure data")
            return False
        print("\nValidation for First Tomogram:")
        print(f"  Tilt  : [{round(min(tilts),2)}, {round(max(tilts),2)}]")
        print(f"  Defocus: [{round(min(defs),2)}, {round(max(defs),2)}]")
        print(f"  Exposure: [{round(min(exps),2)}, {round(max(exps),2)}]")
        print(f"  STAR : {star}")
        print(f"  MRC  : {tomo_file}")
        print(f"  Mask : {bmask}")
        return True
    except Exception as e:
        print(f"Validation error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Batch-submit PyTom template-matching for RELION5 tomograms'
    )

    # Paths
    parser.add_argument(
        '--mrc-dir',
        required=True,
        help='Directory for .mrc tomograms'
    )
    parser.add_argument(
        '--star-dir',
        required=True,
        help='Directory for .star metadata'
    )
    parser.add_argument(
        '--bmask-dir',
        help='Directory for tomogram masks (default: none)'
    )
    parser.add_argument(
        '--tomolist',
        help='File listing tomogram IDs, one per line (default: use all in --mrc-dir)'
    )
    parser.add_argument(
        '--output-dir',
        default='submission',
        help='Where to write scripts/results (default: %(default)s)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Only generate scripts, do not submit'
    )
    parser.add_argument(
        '--no-tomogram-mask',
        action='store_true',
        help='Ignore masks even if provided'
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Validate first tomogram and exit'
    )

    # PyTom params
    parser.add_argument(
        '-t', '--template',
        required=True,
        help='Template MRC file (default: none)'
    )
    parser.add_argument(
        '-m', '--mask',
        required=True,
        help='Mask MRC file (default: none)'
    )
    parser.add_argument(
        '--particle-diameter',
        type=float,
        help='Particle diameter in Å for angular sampling (default: none)'
    )
    parser.add_argument(
        '--angular-search',
        help='Override angular search (float or .txt; default: none)'
    )
    parser.add_argument(
        '-s', '--volume-split',
        nargs=3,
        metavar=('X','Y','Z'),
        type=int,
        default=None,
        help='Split volume into X Y Z blocks (default: none)'
    )
    parser.add_argument(
        '--voxel-size',
        type=float,
        required=True,
        help='Voxel size in Å (default: none)'
    )
    parser.add_argument(
        '-g', '--gpu-ids',
        nargs='+',
        default=['0'],
        help='GPU IDs to use (e.g. 0 1; default: %(default)s)'
    )
    parser.add_argument(
        '--random-phase-correction',
        action='store_true',
        help='Enable random phase correction'
    )
    parser.add_argument(
        '--rng-seed',
        default='69',
        help='Random seed for phase-correction (default: %(default)s)'
    )
    parser.add_argument(
        '--per-tilt-weighting',
        action='store_true',
        help='Enable per-tilt weighting'
    )
    parser.add_argument(
        '--non-spherical-mask',
        action='store_true',
        help='Enable non‑spherical mask'
    )
    parser.add_argument(
        '--spectral-whitening',
        action='store_true',
        help='Enable spectral whitening'
    )
    parser.add_argument(
        '--tomogram-ctf-model',
        choices=['phase-flip','wiener'],
        help='CTF model (default: none)'
    )
    parser.add_argument(
        '--z-axis-rotational-symmetry',
        help='Z‑axis symmetry (integer; default: none)'
    )
    parser.add_argument(
        '--amplitude-contrast',
        default='0.07',
        help='Amplitude contrast fraction (default: %(default)s)'
    )
    parser.add_argument(
        '--spherical-aberration',
        default='2.7',
        help='Spherical aberration in mm (default: %(default)s)'
    )
    parser.add_argument(
        '--voltage',
        default='300',
        help='Voltage in kV (default: %(default)s)'
    )
    parser.add_argument(
        '--low-pass',
        help='Low-pass filter Å (default: none)'
    )
    parser.add_argument(
        '--high-pass',
        help='High-pass filter Å (default: none)'
    )

    # SLURM settings
    parser.add_argument(
        '--partition',
        default='emgpu',
        help='SLURM partition (default: %(default)s)'
    )
    parser.add_argument(
        '--ntasks',
        default='1',
        help='SLURM ntasks (default: %(default)s)'
    )
    parser.add_argument(
        '--nodes',
        default='1',
        help='SLURM nodes (default: %(default)s)'
    )
    parser.add_argument(
        '--ntasks-per-node',
        default='1',
        help='SLURM tasks/node (default: %(default)s)'
    )
    parser.add_argument(
        '--cpus-per-task',
        default='4',
        help='SLURM cpus/task (default: %(default)s)'
    )
    parser.add_argument(
        '--gres',
        default='gpu:1',
        help='SLURM gres (default: %(default)s)'
    )
    parser.add_argument(
        '--mail-type',
        default='none',
        help='SLURM mail-type (default: %(default)s)'
    )
    parser.add_argument(
        '--mem',
        default='128',
        help='SLURM memory in GB (default: %(default)s)'
    )
    parser.add_argument(
        '--qos',
        default='emgpu',
        help='SLURM QoS (default: %(default)s)'
    )
    parser.add_argument(
        '--time',
        default='05:00:00',
        help='SLURM time limit (hh:mm:ss; default: %(default)s)'
    )

    args = parser.parse_args()

    # Validate inputs
    for d in [args.mrc_dir, args.star_dir]:
        if not os.path.isdir(d):
            print(f"Error: {d} not found"); return
    if args.bmask_dir and not os.path.isdir(args.bmask_dir):
        print(f"Warning: {args.bmask_dir} not found")
    for f in [args.template, args.mask]:
        if not os.path.isfile(f):
            print(f"Error: {f} not found"); return
    if args.tomolist and not os.path.isfile(args.tomolist):
        print(f"Error: {args.tomolist} not found"); return

    tomos = get_tomogram_numbers(args)
    if not tomos:
        print("Error: no tomograms found"); return
    print(f"Processing tomograms: {tomos}")

    if not validate_first_tomogram(
        tomos[0], args.star_dir, args.mrc_dir, args.bmask_dir, not args.no_tomogram_mask
    ):
        print("Validation failed"); return
    if args.validate_only:
        print("Validation OK — exiting"); return

    for tomo in tomos:
        try:
            star, tomo_file, bmask = find_matching_files(
                tomo, args.star_dir, args.mrc_dir,
                args.bmask_dir if not args.no_tomogram_mask else None
            )
            tilts, defs, exps = read_star_file(star)
            outdir = os.path.join(args.output_dir, f"tomo_{tomo}")
            os.makedirs(outdir, exist_ok=True)
            tlt, dfx, exp = create_temp_files(tomo, tilts, defs, exps, outdir)
            script = create_sbatch_script(
                tomo, tlt, dfx, exp, tomo_file, bmask, outdir, args
            )
            submit_sbatch(script, args.dry_run)
        except Exception as e:
            print(f"Error on {tomo}: {e}")
    print("Done.")

if __name__ == "__main__":
    main()
