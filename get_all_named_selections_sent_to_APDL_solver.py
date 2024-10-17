"""
Get a list of all named selections sent to the APDL solver.
===========================================================================================



"""
import wbjn
import datetime
import csv
import mech_dpf
import Ans.DataProcessing as dpf
cmd = 'returnValue(GetUserFilesDirectory())'
user_dir = wbjn.ExecuteCommand(ExtAPI, cmd)
mech_dpf.setExtAPI(ExtAPI)

################### Parameters ########################
analysisNumbers = [0,2]       # List of analysis systems to apply this script

named_sels = {}

for a in analysisNumbers:
    analysis = Model.Analyses[a]
    solver_data = analysis.Solution.SolverData
    analysis_type = analysis.AnalysisType
       
    # Result Data
    filepath = analysis.ResultFileName
    
    # Data Sources
    dataSources = dpf.DataSources()
    dataSources.SetResultFilePath(filepath)
    
    # Model 
    model = dpf.Model(dataSources)
    named_sels[analysis.Name] = model.AvailableNamedSelections
    
