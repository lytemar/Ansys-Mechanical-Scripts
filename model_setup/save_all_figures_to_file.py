"""
Export all result figures to PNG image files.
=====================================================================================

This has been tested on 2024 R2 and 2025 R1.
** It doesn't work for prestressed Response Spectrum Analysis as this time**



"""
"""
Export all result figures to PNG image files.
=====================================================================================

This has been tested on 2024 R2 and 2025 R1.
"""

analysisNumbers = [0, 2, 3]       # LIST OF ANALYSIS SYSTEMS TO APPLY THIS SCRIPT

import wbjn
import datetime
import os
import mech_dpf
import Ans.DataProcessing as dpf
cmd = 'returnValue(GetUserFilesDirectory())'
user_dir = wbjn.ExecuteCommand(ExtAPI, cmd)
mech_dpf.setExtAPI(ExtAPI)

# Export Settings
export = Ansys.Mechanical.Graphics.GraphicsImageExportSettings()
export.Resolution = GraphicsResolutionType.HighResolution
export.Height = 1200
export.Width = 2000

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
        export.CurrentGraphicsDisplay = False
        export_name = os.path.join(EXPORT_DIR, figure.Name)
        ExtAPI.Graphics.ExportImage(export_name +".png", GraphicsImageExportFormat.PNG, export)
    

