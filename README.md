Batch submission of pytom-match-pick jobs using a tomolist. This is a text file contain each tomo number per line which should be used for the TM job.
After running the python script the user is prompted for this file as well as RELION5 directories containing tomograms_*.mrc and tilt-series.star files.
Where * is the tomo number. The user then proceeds to provide the usual pytom flags as input. Finally, a slurm submission batch script will be generated.
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
> Enter the directory path for RELION5 tilt-series.star files []: **../chlorella/Tomograms/No_halfset_tomo_aretomo/til
t_series**
> 
> Enter the identifier (file base name) for tilt-series.star files (default: Position_): []:
> 
> Enter the directory path for RELION5 tomogram files (.mrc) []: **../chlorella/Tomograms/No_halfset_tomo_aretomo/tomo
grams**
> 
> Enter the identifier (file base name) for tomogram files (default: rec_Position_): []:
>
>Sanity Check for your First Tomogram checking Min and Max values
> 
> Tilt values: [-40.01, 57.99]
> 
> Defocus values: [1.36, 2.03]
> 
> Exposure values: [100.0, 96.0]
> 
> .star File: ../chlorella/Tomograms/No_halfset_tomo_aretomo/tilt_series/Position_1.star
> 
> .mrc File: ../chlorella/Tomograms/No_halfset_tomo_aretomo/tomograms/rec_Position_1.mrc
> 
> Are these values correct for the first tomogram? ([y]es/ [n]o): **y**
>
> 
>--- Pytom Parameters ---
> 
> Enter the template file path (Required): []:

Empty = ENTER
