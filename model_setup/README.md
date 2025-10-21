# Python Scripts to Automate Model Setup

These scripts are run as Scripting objects from the Automation tab to automate repetative model setup tasks

## Table of Contents

- ### add_beam_probe_for_all_beam_connections.py
  Add beam probes to the solution branch for all circular beam connections.
  
- ### add_bolt_tool_for_all_bolt_pretensions.py
  Add bolts tools to the solution branch for all bolt pretension loads.
  
- ### add_contact_tool_for_all_contacts.py
  Add grouped Contact Tool for each contact for all load steps in the Solution Branch.

- ### add_contact_trackers_for_all_nonlinear_contacts.py
  For each nonlinear contact, add a grouped set of contact trackers to the Solution Information branch of an analysis.
  
- ### add_dir_deform_post_proc_for_all_named_selections.py
  Add directional deformation post-processing items for all named selections within a tree grouping.
  Use `create_named_sels_for_all_bodies.py` first to create grouped Named Selections and rename the `Auto-generated` folder to `Results Scoping`.
  
- ### add_dir_vel_post_proc_for_all_named_selections.py
  Add directional velocity post-processing items for all named selections within a tree grouping.
  Use `create_named_sels_for_all_bodies.py` first to create grouped Named Selections and rename the `Auto-generated` folder to `Results Scoping`.
  
- ### add_eqv_stress_post_proc_for_all_named_selections.py
  Add equivalent stress post-processing items for all named selections within a tree grouping.
  Use `create_named_sels_for_all_bodies.py` first to create grouped Named Selections and rename the `Auto-generated` folder to `Results Scoping`.
  
- ### add_fatigue_tool_post_proc_for_all_named_selections.py
  Add fatigue tool post-processing items for all named selections within a tree grouping.
  Use `create_named_sels_for_all_bodies.py` first to create grouped Named Selections and rename the `Auto-generated` folder to `Results Scoping`.
  
- ### add_force_conv_cont_trkrs_for_all_nonlin_contacts.py
  Add force convergence contact trackers to Solution Information for all nonlinear contacts grouped together in one folder.
  
- ### add_tot_deform_post_proc_for_all_named_selections.py
  Add total deformation post-processing items for all named selections within a tree grouping.
  Use `create_named_sels_for_all_bodies.py` first to create grouped Named Selections and rename the `Auto-generated` folder to `Results Scoping`.
  
- ### create_named_sels_for_all_bodies.py
  Create a named selection for each body or multi-body part in the Geometry branch according to APDL naming rules.

- ### remove_suffix_from_part_names.py
  Remove the suffix for part or body names after the `\` in the Geometry Branch, e.g. `Box\Solid` becomes `Box`.
  
- ### save_all_figures_to_file.py
  Export all figures as PNG images to an `images[<analysis name and date>` subdirectory of the `user_files` directory.
  