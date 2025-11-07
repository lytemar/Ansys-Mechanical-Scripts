# Python Scripts to Automate Model Setup

These scripts are run as Scripting objects from the Automation tab to export desired results in spreadsheet format

## Table of Contents

- ### compute_stress_resultants_for_beam_conns.py
  - Read SMISC results, compute stress resultants and export to spreadsheet for all circular beam connections in static
    structural, transient structural, random vibration and response spectrum analyses.
  - WORKS FOR **2024 R1** AND POSSIBLY EARLIER.

- ### compute_stress_resultants_for_beam_conns_2024R2.py
  - Read SMISC results, compute stress resultants and export to spreadsheet for all circular beam connections in static
    structural, transient structural, random vibration and response spectrum analyses.
  - WORKS FOR **2024 R2** AND LATER.

- ### extract_max_eqv_stress_for_all_bodies_in_NS_and_time.py
  - This script extracts the maximum von Mises equivalent stress for each group of scoped bodies within named selections
    for all analysis times, or the last time only.  The named selections that are of interest are placed in a Tree
	Grouping folder called `Results Scoping`.
  
- ### get_mean_alter_eqv_strs_for_pre-stressed_RS_RV.py
  For prestressed random vibration (RV)/response spectrum (RS) analyses, find the node with maximum equivalent stress in the
  static structural analysis, call that the mean stress, and find the associated equivalent stress in the downstream
  RS/RV analyses, call that an alternating stress, and export summary to spreadsheet.
  
