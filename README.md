Batch submission of pytom-match-pick jobs using a tomolist. This is a text file contain each tomogram number per line which you want to run template matching on.
After running the python script the user is prompted for this file as well as RELION5 directories containing `*.mrc` and `*.star` files.
Where `*` is the tomo number. Tilt values, defocus, and exposure values will be read from each `.star` file. 
The user then proceeds to provide the usual pytom flags as input. Finally, a slurm submission batch script will be generated.
The #SBATCH values can be adjusted accordingly for your HPC slurm configuration.

Example: 

> python cli.py
> 
> Enter the path to the tomolist file []: **tomolist.txt**
> 
> Tomogram numbers: ['1', '2', '6', '8', '9', '10', '13', '15', '17']
> 
> Is the list of tomograms correct? ([y]es/ [n]o): **y**
> 
> Enter the directory path for RELION5 tilt-series.star files []: **../chlorella/Tomograms/No_halfset_tomo_aretomo/tilt_series**
> 
> Enter the directory path for RELION5 tomogram files (.mrc) []: **../chlorella/Tomograms/No_halfset_tomo_aretomo/tomograms**
>
> Do you want to use tomogram masks? ([y]es/ [n]o): **y**
>
> Enter the directory for tomogram masks (e.g. path/to/bmask_*.mrc): []: **../bmask**
>
> _Sanity Check for your First Tomogram checking Min and Max values_
> 
> _Tilt values: [-40.01, 57.99]_
> 
> _Defocus values: [1.36, 2.03]_
> 
> _Exposure values: [100.0, 96.0]_
> 
> _.star File: ../chlorella/Tomograms/No_halfset_tomo_aretomo/tilt_series/Position_1.star_
> 
> _.mrc File: ../chlorella/Tomograms/No_halfset_tomo_aretomo/tomograms/rec_Position_1.mrc_
> 
> Are these values correct for the first tomogram? ([y]es/ [n]o): **y**
>
> 
>--- Pytom Parameters ---
> 
> Enter the template file path (Required): []: **tmpl.mrc**
>
> Enter the mask file path (Required): []: **mask.mrc**
>
> Enter particle diameter in Angstrom or leave empty to specify angular search value (either one required): []: **140**
>
> Enter voxel size in Angstrom (Required): []: **7.92**
>
> Enter GPU IDs (Required): []: **0**
>
> Enable random-phase correction? (recommended) ([y]es/ [n]o): **y**
>
> Enter random seed (default: 69): [69]:
>
> Enable per-tilt-weighting? ([y]es/ [n]o): **y**
>
> Enable non-spherical mask? ([y]es/ [n]o): **n**
>
> Enable spectral whitening? ([y]es/ [n]o): **n**
>
> Enter z-axis rotational symmetry as integer (PRESS ENTER TO SKIP): []: **4**
>
> Amplitude contrast (ENTER = default: 0.07): [0.07]:
>
> Spherical aberration in mm (ENTER = default: 2.7): [2.7]:
>
> Acceleration voltage in kV (ENTER = default: 300): [300]:
>
> Low-pass filter (PRESS ENTER TO SKIP): []:
>
> High-pass filter (PRESS ENTER TO SKIP): []:
>
> Phase shift (PRESS ENTER TO SKIP): []:
>
> 
> _--- SLURM Settings ---_
> 
> _Default SLURM settings are:_
> 
> _partition: rtx3090-em_
> 
> _ntasks: 1_
> 
> _nodes: 1_
> 
> _ntasks_per_node: 1_
>
> _cpus_per_task: 4_
> 
> _gres: gpu:1_
> 
> _mail_type: none_
> 
> _mem: 128_
> 
> _qos: emgpu_
>
> _time: 06:00:00_
> 
> Do you want to use the default SLURM settings? (No = provide custom inputs). ([y]es/ [n]o): **y**


Bold = Inputs

Empty = ENTER (default)
