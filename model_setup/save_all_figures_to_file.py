"""
Export all result figures to PNG image files.
============================================

This has been tested on 2024 R2 and 2025 R1.
"""

analysisNumbers = [0, 2, 3]       # LIST OF ANALYSIS SYSTEMS TO APPLY THIS SCRIPT

import wbjn
import datetime
import os
import mech_dpf
import Ans.DataProcessing as dpf
import re
cmd = 'returnValue(GetUserFilesDirectory())'
user_dir = wbjn.ExecuteCommand(ExtAPI, cmd)
mech_dpf.setExtAPI(ExtAPI)

# Export Settings
export = Ansys.Mechanical.Graphics.GraphicsImageExportSettings()
export.Resolution = GraphicsResolutionType.HighResolution
export.Height = 1200
export.Width = 2000

def add_spaces_at_capital_letters(s):
    """
    Function to split a string at capital letters and then recombine.
    
    Parameters
    ----------
    s : str
        String to split

    Returns
    -------
    string
    """
    # Split the name of the figure's parent at capital letters
    split_str = re.findall('[A-Z][^A-Z]*', s)
    # Check if there are any length 1 list elements and combine them since they are probably an acronym
    result =''
    for x in split_str:
        if len(x) == 1:
            result += x
        else:
            result += x + ' '
    return result.rstrip()      # Remove spaces at the end of the string
    

for a in analysisNumbers:
    analysis = Model.Analyses[a]
    solver_data = analysis.Solution.SolverData
    analysis_type = analysis.AnalysisType
    
    x = datetime.datetime.now()
    EXPORT_DIR = user_dir + '/images/' + analysis.Name + '_' + x.strftime("%m") + "-" + x.strftime("%d") + "-" + x.strftime("%y") + '/'
    
    #Save Figures
    all_figures = analysis.GetChildren(DataModelObjectCategory.Figure, True)
    for figure in all_figures:
        Tree.Activate(figure)
        fig_par = figure.Parent
        fig_par_name = fig_par.GetType().Name
        #form the subdirectory from spliiting the figure's parent name at the capital letters
        subdir = add_spaces_at_capital_letters(fig_par_name)
        # Add directional prefix for directional results
        if fig_par_name.Contains('Directional'):
            if fig_par.NormalOrientation == Ansys.Mechanical.DataModel.Enums.NormalOrientationType.XAxis:
                subdir_prefix = 'X-Axis '
            elif fig_par.NormalOrientation == Ansys.Mechanical.DataModel.Enums.NormalOrientationType.YAxis:
                subdir_prefix = 'Y-Axis '
            else:
                subdir_prefix = 'Z-Axis '
            subdir = subdir_prefix + subdir
        
        export.CurrentGraphicsDisplay = False
        EXPORT_DIR = user_dir + '/images/' + analysis.Name + '_' + x.strftime("%m") + "-" + x.strftime("%d") + "-" + x.strftime("%y") + '/' + subdir + '/'
        export_name = os.path.join(EXPORT_DIR, figure.Name)
        ExtAPI.Graphics.ExportImage(export_name +".png", GraphicsImageExportFormat.PNG, export)
    

