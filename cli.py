import os
import glob
import starfile
from prompt_toolkit import prompt
from prompt_toolkit.completion import PathCompleter
import subprocess

def confirm_prompt(message):
    while True:
        user_input = input(f"{message} ([y]es/ [n]o): ").lower()
        if user_input in ['y', 'yes']:
            return True
        elif user_input in ['n', 'no']:
            return False

def get_user_input(message, default=None):
    completer = PathCompleter(expanduser=True)
    user_input = prompt(f"{message} [{default if default else ''}]: ", completer=completer)
    return user_input.strip() or default

def read_star_file(file_path):
    df = starfile.read(file_path)
    tilt_angles = df["rlnTomoNominalStageTiltAngle"].tolist()
    defocus_values = ((df["rlnDefocusU"] + df["rlnDefocusV"]) / 20000).tolist()  # Convert defocus to micrometers and take average between DefocusU and DefocusV
    exposures = df["rlnMicrographPreExposure"].tolist()
    return tilt_angles, defocus_values, exposures

def create_temp_files(tomogram_num, tilt_angles, defocus_values, exposures, output_dir):
    temp_tilt_file = os.path.join(output_dir, f"{tomogram_num}.tlt")
    temp_defocus_file = os.path.join(output_dir, f"{tomogram_num}_defocus.txt")
    temp_exposure_file = os.path.join(output_dir, f"{tomogram_num}_exposure.txt")

    with open(temp_tilt_file, 'w') as tlt_file:
        for angle in tilt_angles:
            tlt_file.write(f"{angle}\n")
    
    with open(temp_defocus_file, 'w') as defocus_file:
        for defocus in defocus_values:
            defocus_file.write(f"{defocus}\n")
    
    with open(temp_exposure_file, 'w') as exposure_file:
        for exposure in exposures:
            exposure_file.write(f"{exposure}\n")

    return temp_tilt_file, temp_defocus_file, temp_exposure_file

def create_sbatch_script(tomogram_num, temp_tilt_file, temp_defocus_file, temp_exposure_file, tomogram_file, bmask_file, output_dir, args, slurm_args):
    script_path = os.path.join(output_dir, f"submit_{tomogram_num}.sh")
    with open(script_path, 'w') as f:
        f.write(f"""#!/bin/bash -l

#SBATCH -o pytom.out%j
#SBATCH -D ./ 
#SBATCH -J pytom_{tomogram_num}
#SBATCH --partition={slurm_args['partition']}
#SBATCH --ntasks={slurm_args['ntasks']}
#SBATCH --nodes={slurm_args['nodes']}
#SBATCH --ntasks-per-node={slurm_args['ntasks_per_node']}
#SBATCH --cpus-per-task={slurm_args['cpus_per_task']}
#SBATCH --gres={slurm_args['gres']}
#SBATCH --mail-type={slurm_args['mail_type']}
#SBATCH --mem={slurm_args['mem']}G
#SBATCH --qos={slurm_args['qos']}
#SBATCH --time={slurm_args['time']}

ml purge
ml pytom-match-pick

pytom_match_template.py \\
-v {tomogram_file} \\
-a {temp_tilt_file} \\
--dose-accumulation {temp_exposure_file} \\
--defocus {temp_defocus_file} \\
-t {args['template']} \\
-d {output_dir} \\
-m {args['mask']} \\
""")

        if args.get('particle_diameter'):
            f.write(f"--particle-diameter {args['particle_diameter']} \\\n")
        elif args.get('angular_search'):
            f.write(f"--angular-search {args['angular_search']} \\\n")

        if args.get('use_tomogram_mask') and bmask_file:
            f.write(f"--tomogram-mask {bmask_file} \\\n")

        f.write(f"--voxel-size-angstrom {args['voxel_size_angstrom']} \\\n")
        f.write(f"-r \\\n")
        f.write(f"--rng-seed {args['rng_seed']} \\\n")
        f.write(f"-g {args['gpu_ids']} \\\n")
        f.write(f"--amplitude-contrast {args['amplitude_contrast']} \\\n")
        f.write(f"--spherical-aberration {args['spherical_aberration']} \\\n")
        f.write(f"--voltage {args['voltage']} \\\n")

        if args.get('z_axis_rotational_symmetry') and args['z_axis_rotational_symmetry'].strip().isdigit():
            f.write(f"--z-axis-rotational-symmetry {args['z_axis_rotational_symmetry']} \\\n")

        if args.get('per_tilt_weighting'):
            f.write(f"--per-tilt-weighting \\\n")

    print(f"Generated sbatch script for tomogram {tomogram_num} at {script_path}")
    return script_path


def get_pytom_flags():
    args = {}
    
    print("\n--- Pytom Parameters ---")
    args['template'] = get_user_input("Enter the template file path (Required):")
    args['mask'] = get_user_input("Enter the mask file path (Required):")
    args['particle_diameter'] = get_user_input("Enter particle diameter in Angstrom or leave empty to specify angular search value (either one required):")
    args['angular_search'] = get_user_input("Enter angular search (optional):") if not args['particle_diameter'] else None
    args['voxel_size_angstrom'] = get_user_input("Enter voxel size in Angstrom (Required):")
    args['gpu_ids'] = get_user_input("Enter GPU IDs (Required):")

    if confirm_prompt("Enable random-phase correction? (recommended)"):
        args['random_phase_correction'] = True

    args['rng_seed'] = get_user_input("Enter random seed (default: 69):", "69")
    
    if confirm_prompt("Enable per-tilt-weighting?"):
        args['per_tilt_weighting'] = True

    if confirm_prompt("Enable non-spherical mask?"):
        args['non_spherical_mask'] = False
    
    if confirm_prompt("Enable spectral whitening?"):
        args['spectral_whitening'] = False

    args['z_axis_rotational_symmetry'] = get_user_input("Enter z-axis rotational symmetry as integer (PRESS ENTER TO SKIP):")
    
    
    args['amplitude_contrast'] = get_user_input("Amplitude contrast (ENTER = default: 0.07):", "0.07")
    args['spherical_aberration'] = get_user_input("Spherical aberration in mm (ENTER = default: 2.7):", "2.7")
    args['voltage'] = get_user_input("Acceleration voltage in kV (ENTER = default: 300):", "300")
    args['low_pass'] = get_user_input("Low-pass filter (PRESS ENTER TO SKIP):")
    args['high_pass'] = get_user_input("High-pass filter (PRESS ENTER TO SKIP):")
    args['phase_shift'] = get_user_input("Phase shift (PRESS ENTER TO SKIP):")

    return args


def get_slurm_settings():
    slurm_defaults = {
        'partition': 'rtx3090-em',
        'ntasks': '1',
        'nodes': '1',
        'ntasks_per_node': '1',
        'cpus_per_task': '4',
        'gres': 'gpu:1',
        'mail_type': 'none',
        'mem': '128',
        'qos': 'emgpu',
        'time': '06:00:00'
    }

    print("\n--- SLURM Settings ---")
    print("Default SLURM settings are:")
    for key, value in slurm_defaults.items():
        print(f"{key}: {value}")

    if confirm_prompt("Do you want to use the default SLURM settings?"):
        return slurm_defaults

    slurm_args = {}
    slurm_args['partition'] = get_user_input("SLURM partition (default: rtx3090-em):", slurm_defaults['partition'])
    slurm_args['ntasks'] = get_user_input("Number of tasks (default: 1):", slurm_defaults['ntasks'])
    slurm_args['nodes'] = get_user_input("Number of nodes (default: 1):", slurm_defaults['nodes'])
    slurm_args['ntasks_per_node'] = get_user_input("Tasks per node (default: 1):", slurm_defaults['ntasks_per_node'])
    slurm_args['cpus_per_task'] = get_user_input("CPUs per task (default: 4):", slurm_defaults['cpus_per_task'])
    slurm_args['gres'] = get_user_input("GPU resources (default: gpu:1):", slurm_defaults['gres'])
    slurm_args['mail_type'] = get_user_input("Mail type for SLURM (default: none):", slurm_defaults['mail_type'])
    slurm_args['mem'] = get_user_input("Memory allocation in GB (default: 128):", slurm_defaults['mem'])
    slurm_args['qos'] = get_user_input("QoS for SLURM (default: emgpu):", slurm_defaults['qos'])
    slurm_args['time'] = get_user_input("Time limit (default: 06:00:00):", slurm_defaults['time'])

    return slurm_args

def find_matching_files(tomo_num, star_dir, mrc_dir, bmask_dir=None, use_tomogram_mask=False):
    """
    Search for .star, .mrc, and optionally bmask_*.mrc files in the directories that match the given tomogram number.
    """
    star_pattern = os.path.join(star_dir, f"*{tomo_num}.star")
    mrc_pattern = os.path.join(mrc_dir, f"*{tomo_num}.mrc")
    
    star_files = glob.glob(star_pattern)
    mrc_files = glob.glob(mrc_pattern)
    
    if not star_files or not mrc_files:
        raise FileNotFoundError(f"Could not find matching .star or .mrc file for tomogram {tomo_num}")

    if len(star_files) > 1 or len(mrc_files) > 1:
        print(f"Warning: Multiple files matched for tomogram {tomo_num}, using the first match.")
    
    bmask_file = None
    if use_tomogram_mask and bmask_dir:
        bmask_pattern = os.path.join(bmask_dir, f"*{tomo_num}.mrc")
        bmask_files = glob.glob(bmask_pattern)
        if bmask_files:
            bmask_file = bmask_files[0]  # Pick the first match
        else:
            print(f"Warning: Could not find tomogram mask for tomogram {tomo_num}")
    
    return star_files[0], mrc_files[0], bmask_file


def process_tomograms():
    tomolist_file = get_user_input("Enter the path to the tomolist file")
    with open(tomolist_file, 'r') as f:
        tomo_numbers = [line.strip() for line in f if line.strip().isdigit()]
    
    print(f"Tomogram numbers: {tomo_numbers}")
    if not confirm_prompt("Is the list of tomograms correct?"):
        return

    star_dir = get_user_input("Enter the directory path for .star files")
    mrc_dir = get_user_input("Enter the directory path for .mrc files")

    use_tomogram_mask = confirm_prompt("Do you want to use tomogram masks?")
    bmask_dir = None
    if use_tomogram_mask:
        bmask_dir = get_user_input("Enter the directory for tomogram masks (e.g. path/to/bmask_*.mrc):")

    first_tomo_num = tomo_numbers[0]
    star_file, tomogram_file, bmask_file = find_matching_files(first_tomo_num, star_dir, mrc_dir, bmask_dir, use_tomogram_mask)

    tilt_angles, defocus_values, exposures = read_star_file(star_file)

    print("\nSanity Check for your First Tomogram checking Min and Max values")
    print(f"Tilt values: [{round(tilt_angles[0], 2)}, {round(tilt_angles[-1], 2)}]")
    print(f"Defocus values: [{round(defocus_values[0], 2)}, {round(defocus_values[-1], 2)}]")
    print(f"Exposure values: [{round(exposures[0], 2)}, {round(exposures[-1], 2)}]")
    print(f".star File: {star_file}")
    print(f".mrc File: {tomogram_file}")
    if not confirm_prompt("Are these values correct for the first tomogram?"):
        return

    args = get_pytom_flags()
    slurm_args = get_slurm_settings()

    for tomo_num in tomo_numbers:
        try:
            star_file, tomogram_file, bmask_file = find_matching_files(tomo_num, star_dir, mrc_dir, bmask_dir, use_tomogram_mask)
        except FileNotFoundError as e:
            print(f"Skipping tomogram {tomo_num}: {str(e)}")
            continue

        tilt_angles, defocus_values, exposures = read_star_file(star_file)

        output_dir = os.path.join(os.getcwd(), f"submission/tomo_{tomo_num}")
        os.makedirs(output_dir, exist_ok=True)
        temp_tilt_file, temp_defocus_file, temp_exposure_file = create_temp_files(tomo_num, tilt_angles, defocus_values, exposures, output_dir)

        script_path = create_sbatch_script(tomo_num, temp_tilt_file, temp_defocus_file, temp_exposure_file, tomogram_file, bmask_file, output_dir, args, slurm_args)

        submit_sbatch(script_path)

    print("All specified tomograms have been processed, sbatch scripts have been generated and submitted.")


def submit_sbatch(script_path):
    try:
        result = subprocess.run(['sbatch', script_path], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Submission successful for {script_path}: {result.stdout}")
        else:
            print(f"Error submitting {script_path}: {result.stderr}")
    except Exception as e:
        print(f"Exception occurred while submitting {script_path}: {str(e)}")

if __name__ == "__main__":
    process_tomograms()