import mech_dpf
import Ans.DataProcessing as dpf
mech_dpf.setExtAPI(ExtAPI)

# Set path to results file
analysis = ExtAPI.DataModel.Project.Model.Analyses[0]
filepath = analysis.ResultFileName

# Data Sources
dataSources = dpf.DataSources()
dataSources.SetResultFilePath(filepath)

# Scoping
scoping = dpf.Scoping()
