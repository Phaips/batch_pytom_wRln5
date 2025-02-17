import os
import glob
import starfile
from prompt_toolkit import prompt
from prompt_toolkit.completion import PathCompleter
import subprocess
import re

#Versioning 1-0

def confirm_prompt(message):
    while True:
        user_input = input(f"{message} ([y]es/[n]o): ").lower()
        if user_input in ['y', 'yes']:
            return True
        elif user_input in ['n', 'no']:
            return False
        else:
            print("Please enter 'yes' or 'no'.")

def get_user_input(message, default=None):
    completer = PathCompleter(expanduser=True)
    user_input = prompt(f"{message} [{default if default else ''}]: ", completer=completer)
    return user_input.strip() or default

def read_star_file(file_path):
    try:
        df = starfile.read(file_path)
        tilt_angles = df["rlnTomoNominalStageTiltAngle"].tolist()
        defocus_values = ((df["rlnDefocusU"] + df["rlnDefocusV"]) / 20000).tolist()  # Convert to micrometers
        exposures = df["rlnMicrographPreExposure"].tolist()
        return tilt_angles, defocus_values, exposures
    except Exception as e:
        print(f"Error reading STAR file {file_path}: {e}")
        return [], [], []

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

        if args.get('volume_split'):
            f.write(f"-s {args['volume_split']} \\\n")

        f.write(f"--voxel-size-angstrom {args['voxel_size_angstrom']} \\\n")

        if args.get('random_phase_correction'):
            f.write(f"-r \\\n")
            f.write(f"--rng-seed {args['rng_seed']} \\\n")

        if args.get('gpu_ids'):
            f.write(f"-g {args['gpu_ids']} \\\n")
        else:
            f.write(f"-g 0 \\\n")  # Default GPU ID

        f.write(f"--amplitude-contrast {args['amplitude_contrast']} \\\n")
        f.write(f"--spherical-aberration {args['spherical_aberration']} \\\n")
        f.write(f"--voltage {args['voltage']} \\\n")

        if args.get('z_axis_rotational_symmetry') and args['z_axis_rotational_symmetry'].strip().isdigit():
            f.write(f"--z-axis-rotational-symmetry {args['z_axis_rotational_symmetry']} \\\n")

        if args.get('per_tilt_weighting'):
            f.write(f"--per-tilt-weighting \\\n")

        if args.get('tomogram_ctf_model'):
            f.write(f"--tomogram-ctf-model {args['tomogram_ctf_model']} \\\n")

        if args.get('non_spherical_mask'):
            f.write(f"--non-spherical-mask \\\n")

        if args.get('spectral_whitening'):
            f.write(f"--spectral-whitening \\\n")

        if args.get('low_pass'):
            f.write(f"--low-pass {args['low_pass']} \\\n")

        if args.get('high_pass'):
            f.write(f"--high-pass {args['high_pass']} \\\n")

    print(f"Generated sbatch script for tomogram {tomogram_num} at {script_path}")
    return script_path

def get_pytom_flags():
    args = {}

    print("\n--- Pytom Parameters ---")
    # Required parameters
    while True:
        args['template'] = get_user_input("Enter the template file path (Required - black on white density (inverted)):")
        if args['template'] and os.path.isfile(args['template']):
            break
        else:
            print("Template file is required and must exist.")

    while True:
        args['mask'] = get_user_input("Enter the mask file path (Required):")
        if args['mask'] and os.path.isfile(args['mask']):
            break
        else:
            print("Mask file is required and must exist.")

    # Particle diameter or angular search
    args['particle_diameter'] = get_user_input("Enter particle diameter in Angstrom to estimate angular sampling based on the Crowther criterion. (Required - press ENTER to specify custom angular search value):")
    if not args['particle_diameter']:
        args['angular_search'] = get_user_input("Enter angular search value (Required if particle diameter not specified):")
        while not args['angular_search']:
            print("You must specify either particle diameter or angular search.")
            args['angular_search'] = get_user_input("Enter angular search value or file path (Required):")

    # Volume split parameters
    args['volume_split'] = get_user_input("Enter volume split parameters as 'x y z' (e.g., 2 2 1) or press ENTER empty to skip:")
    if args['volume_split']:
        # Validate the input
        if not re.match(r'^\d+\s+\d+\s+\d+$', args['volume_split']):
            print("Invalid volume split format. It should be three integers separated by spaces.")
            args['volume_split'] = None

    args['voxel_size_angstrom'] = get_user_input("Enter voxel size in Angstrom (Required):")
    args['gpu_ids'] = get_user_input("Enter GPU IDs (Required):")

    if confirm_prompt("Enable random-phase correction? (Recommended)"):
        args['random_phase_correction'] = True
        args['rng_seed'] = get_user_input("Enter random seed (default: 69):", "69")

    if confirm_prompt("Enable per-tilt-weighting?"):
        args['per_tilt_weighting'] = True

    # Ask if the tomograms are CTF corrected
    if confirm_prompt("Are the tomograms CTF corrected?"):
        # Tomograms are CTF corrected
        # Prompt if they want to apply the CTF filter
        tomogram_ctf_model = get_user_input("Do you want to apply the CTF filter? (press ENTER to accept default 'phase-flip', or type 'no' to skip)", "phase-flip")
        if tomogram_ctf_model.lower() in ['phase-flip', 'wiener']:
            args['tomogram_ctf_model'] = tomogram_ctf_model.lower()
        elif tomogram_ctf_model.lower() in ['no', 'n']:
            # User chose not to apply the CTF filter
            args['tomogram_ctf_model'] = None
        else:
            # Default to 'phase-flip'
            print("Invalid input. Defaulting to 'phase-flip'.")
            args['tomogram_ctf_model'] = 'phase-flip'
    else:
        # Tomograms are NOT CTF corrected
        # Do not add the --tomogram-ctf-model flag
        args['tomogram_ctf_model'] = None

    if confirm_prompt("Enable non-spherical mask?"):
        args['non_spherical_mask'] = True

    if confirm_prompt("Enable spectral whitening?"):
        args['spectral_whitening'] = True

    args['z_axis_rotational_symmetry'] = get_user_input("Enter z-axis rotational symmetry as integer (PRESS ENTER TO SKIP):")

    args['amplitude_contrast'] = get_user_input("Amplitude contrast (ENTER = default: 0.07):", "0.07")
    args['spherical_aberration'] = get_user_input("Spherical aberration in mm (ENTER = default: 2.7):", "2.7")
    args['voltage'] = get_user_input("Acceleration voltage in kV (ENTER = default: 300):", "300")
    args['low_pass'] = get_user_input("Low-pass filter (PRESS ENTER TO SKIP):")
    args['high_pass'] = get_user_input("High-pass filter (PRESS ENTER TO SKIP):")

    return args

def get_slurm_settings():
    slurm_defaults = {
        'partition': 'emgpu',   # Updated default partition
        'ntasks': '1',
        'nodes': '1',
        'ntasks_per_node': '1',
        'cpus_per_task': '4',
        'gres': 'gpu:1',
        'mail_type': 'none',
        'mem': '128',
        'qos': 'emgpu',       # Updated default QoS
        'time': '06:00:00'
    }

    print("\n--- SLURM Settings ---")
    print("Default SLURM settings are:")
    for key, value in slurm_defaults.items():
        print(f"{key}: {value}")

    if confirm_prompt("Do you want to use the default SLURM settings?"):
        return slurm_defaults

    slurm_args = {}
    slurm_args['partition'] = get_user_input("SLURM partition (default: rtx4090-em):", slurm_defaults['partition'])
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

def find_files_with_exact_number(directory, tomo_num, extension):
    # Primary match: Filenames with underscores
    if "_" in tomo_num:  # Handle compound numbers like "3_2"
        pattern = re.compile(rf'.*_{re.escape(tomo_num)}(_.*)?\.{extension}$')
    else:  # Handle simple numbers like "3"
        pattern = re.compile(rf'.*_{re.escape(tomo_num)}(_|\.{extension}$)')
    
    files = glob.glob(os.path.join(directory, f"*.{extension}"))
    matched_files = [f for f in files if pattern.match(os.path.basename(f))]
    
    # If no matches found, fall back to filenames without underscores
    if not matched_files:
        fallback_pattern = re.compile(rf'.*{re.escape(tomo_num)}(?=\.{extension}$)')
        matched_files = [f for f in files if fallback_pattern.match(os.path.basename(f))]
    
    return matched_files


def find_matching_files(tomo_num, star_dir, mrc_dir, bmask_dir=None, use_tomogram_mask=False):
    star_files = find_files_with_exact_number(star_dir, tomo_num, 'star')
    mrc_files = find_files_with_exact_number(mrc_dir, tomo_num, 'mrc')

    if not star_files or not mrc_files:
        raise FileNotFoundError(f"Could not find matching .star or .mrc file for tomogram {tomo_num}")

    if len(star_files) > 1 or len(mrc_files) > 1:
        print(f"Warning: Multiple files matched for tomogram {tomo_num}, using the first match.")
    
    bmask_file = None
    if use_tomogram_mask and bmask_dir:
        bmask_files = find_files_with_exact_number(bmask_dir, tomo_num, 'mrc')
        if bmask_files:
            bmask_file = bmask_files[0]  # Pick the first match
        else:
            print(f"Warning: Could not find tomogram mask for tomogram {tomo_num}")
    
    return star_files[0], mrc_files[0], bmask_file

def process_tomograms():
    print("\n--- Tomogram Selection ---")
    if confirm_prompt("Do you want to use all .mrc files in the tomogram directory?"):
        mrc_dir = get_user_input("Enter the directory path for .mrc files (tomograms folder from RELION5)")
        mrc_files = glob.glob(os.path.join(mrc_dir, "*.mrc"))
        if not mrc_files:
            print("No .mrc files found in the specified directory.")
            return

        tomo_numbers = []
        for mrc_file in mrc_files:
            filename = os.path.basename(mrc_file)
            base_name = os.path.splitext(filename)[0]
            match = re.search(r'\d+(_\d+)*$', base_name)
            if match:
                tomo_num = match.group(0)
                tomo_numbers.append(tomo_num)
        tomo_numbers = list(set(tomo_numbers))
        print(f"Found tomograms: {tomo_numbers}")
        if not confirm_prompt("Is the list of tomograms correct?"):
            return
    else:
        tomolist_file = get_user_input("Enter the path to the tomolist (a text file containing all the tomo numbers you want to run template matching on e.g. 1 or 1_2 for Tomo_1.mrc. Tomo1.mrc or Tomo_1_2.mrc)")
        if not tomolist_file or not os.path.isfile(tomolist_file):
            print("Tomolist file is required and must exist.")
            return

        with open(tomolist_file, 'r') as f:
            tomo_numbers = [line.strip() for line in f if line.strip()]
        
        print(f"Tomogram numbers: {tomo_numbers}")
        if not confirm_prompt("Is the list of tomograms correct?"):
            return

        mrc_dir = get_user_input("Enter the directory path for .mrc files (tomograms folder from RELION5)")

    star_dir = get_user_input("Enter the directory path for .star files (tiltseries folder from RELION5)")

    use_tomogram_mask = confirm_prompt("Do you want to use tomogram masks?")
    bmask_dir = None
    if use_tomogram_mask:
        bmask_dir = get_user_input("Enter the directory for tomogram masks (e.g., path/to/bmask which contains filename_[tomonumber].mrc):")

    # Validate the first tomogram for sanity check
    first_tomo_num = tomo_numbers[0]
    try:
        star_file, tomogram_file, bmask_file = find_matching_files(first_tomo_num, star_dir, mrc_dir, bmask_dir, use_tomogram_mask)
        tilt_angles, defocus_values, exposures = read_star_file(star_file)

        print("\nSanity Check for your First Tomogram checking Min and Max values")
        print(f"Tilt values: [{round(tilt_angles[0], 2)}, {round(tilt_angles[-1], 2)}]")
        print(f"Defocus values: [{round(defocus_values[0], 2)}, {round(defocus_values[-1], 2)}]")
        print(f"Exposure values: [{round(exposures[0], 2)}, {round(exposures[-1], 2)}]")
        print(f".star File: {star_file}")
        print(f".mrc File: {tomogram_file}")
        print(f"Bmask File: {bmask_file}")
        if not confirm_prompt("Are these values correct for the first tomogram from your list?"):
            return
    except Exception as e:
        print(f"Error during sanity check: {e}")
        return

    args = get_pytom_flags()
    args['use_tomogram_mask'] = use_tomogram_mask
    slurm_args = get_slurm_settings()

    for tomo_num in tomo_numbers:
        try:
            star_file, tomogram_file, bmask_file = find_matching_files(tomo_num, star_dir, mrc_dir, bmask_dir, use_tomogram_mask)
            tilt_angles, defocus_values, exposures = read_star_file(star_file)
            output_dir = os.path.join(os.getcwd(), f"submission/tomo_{tomo_num}")
            os.makedirs(output_dir, exist_ok=True)
            temp_tilt_file, temp_defocus_file, temp_exposure_file = create_temp_files(tomo_num, tilt_angles, defocus_values, exposures, output_dir)
            script_path = create_sbatch_script(tomo_num, temp_tilt_file, temp_defocus_file, temp_exposure_file, tomogram_file, bmask_file, output_dir, args, slurm_args)
            submit_sbatch(script_path)
        except Exception as e:
            print(f"Skipping tomogram {tomo_num} due to error: {e}")
            continue

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
