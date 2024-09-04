"""
Add beam probes to the solution branch for all circular beam connections
========================================================================

"""

analysisNumber = 0
analysis = Model.Analyses[analysisNumber]
analysis_settings = analysis.AnalysisSettings
n = analysis_settings.NumberOfSteps             # number of time steps
# List of display times for future use
DISP_TIMES = [analysis_settings.GetStepEndTime(i) for i in range(1, n+1, 1)]

# Get all cicular beam connection boundary conditions
conns = Model.Connections.GetChildren(DataModelObjectCategory.Beam, True)

# Create beam probes if beam connections exist
if len(conns) > 0:
    # Beam connection names and IDs
    # connNames = [i.Name for i in conns]
    # connIDs = [i.ObjectId for i in conns]
    
    # Create Beam Probes for the end time
    probes = []
    with Transaction(True):     # Suppress GUI update until completion to speed the process
        for c in conns:
            
            # add a beam probe, scope to the beam connection and rename based on definition
            _ = analysis.Solution.AddBeamProbe()
            _.BoundaryConditionSelection = c
            probes.append(_)
    
    # Rename the probes by definition
    [p.RenameBasedOnDefinition() for p in probes]
    
    # Put all beam probes into a group folder
    group = Tree.Group(probes)
    group.Name = "Beam Probes"
    
    Tree.Activate([analysis.Solution])
else:
    print('No beam connections exist so no beam probes created.')
        