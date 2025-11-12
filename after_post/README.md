# Python Code Results Objects with *After Post* Target Callback

These scripts are inserted as Python Code results objects with *Target Callback = After Post*.

## Table of Contents

- ### compute_stress_resultants_for_beam_conns.py
  Calculate stress resultants for all beam connections using results from results file, tested  in 2024 R2 and 2025 R1
  on Static Structural, Random Vibration and Response Spectrum Analyses.

- ### get_force_reactions_for_joints.py
  Retrieve the force and moment resultants for all joints using results for results file, tested in 2025 R1 on Static
  Structural, Random Vibration and Response Spectrum Analyses.
  
- ### get_max_dir_acceleration_for_results_in_tree_folder.py
  Retrieve Maximum Value Over Time for Directional Acceleration Results in Tree Folder.
  
- ### get_max_dir_deformation_for_results_in_tree_folder.py
  Retrieve Maximum Value Over Time for Directional Deformation Results in Tree Folder.

- ### get_max_eqv_stress_for_all_bodies_in_NS_and_time.py
  This script extracts the maximum von Mises equivalent stress for each group of scoped bodies within named selections
  for all analysis times.  The named selections that are of interest are placed in a Tree Grouping folder called
  `Results Scoping`.
  