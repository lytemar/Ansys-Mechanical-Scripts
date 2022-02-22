"""
Add bolts tools to the solution branch for all bolt pretension loads
====================================================================

Functions
---------
createBoltTool
    Create a bolt tool for a single bolt prension load for a list of times
"""

#import time
#StartTime = time.time()

model = ExtAPI.DataModel.Project.Model
analysis = model.Analyses[0]
analysis_settings = analysis.AnalysisSettings
n = analysis_settings.NumberOfSteps             # number of time steps
DISP_TIMES = [analysis_settings.GetStepEndTime(i) for i in range(1, n+1, 1)]

# Get all bolt pretension loads
bolt_pretensions = analysis.GetChildren(DataModelObjectCategory.BoltPretension, True)
bolt_pretensions = [b for b in bolt_pretensions if not b.Suppressed]

# Bolt pretension names and IDs
boltPretensionNames = [i.Name for i in bolt_pretensions]
boltPretensionIDs = [i.ObjectId for i in bolt_pretensions]

# Create bolt tool for each bolt pretension load

def createBoltTool(boltPretensionID, lstboltPretensionID, boltPretensionName, dispTimes):
    """
    Create a bolt tool for a single bolt prension load for a list of times
    
    Parameters
    ----------
    boltPretensionID : int
        The ID of the bolt pretension load for which to create the tool
    lstboltPretensionID : list of ints
        list of bolt pretension load IDs for all bolt pretension loads in the model
    boltPretensionName : string
        The name of the bolt pretension load for which the tool is created
    dispTimes : list of Quantities
        list of analysis times for which to display bolt tools
        
    Returns
    -------
    Ansys.ACT.Automation.Mechanical.Results.BoltToolResults.BoltTool
        The newly created post processing bolt tool
    """
    
    # add a bolt tool
    bolt_tool = analysis.Solution.AddBoltTool()
    
    # scope only to single bolt pretension ID
    # These lines are unsupported beta features
    #bolt_tool.InternalObject.AddScopedContact(contIDs[130])
    [bolt_tool.InternalObject.RemoveScopedBolt(i) for i in lstboltPretensionID if i != boltPretensionID]
    
    # rename the contact tool
    bolt_tool.Name = "Bolt Tool - " + boltPretensionName
    
    # Create bolt adjustment and working load for each time in dispTimes
    for idx, time in enumerate(dispTimes):
        # adjustment
        if idx == 0:
            adjustment = bolt_tool.GetChildren(DataModelObjectCategory.BoltAdjustment, True)[0]
        else:
            adjustment = bolt_tool.AddAdjustment()
        adjustment.DisplayTime = time
        adjustment.Name = "Adjustment - " + str(time)
        
        # Working load
        working_load = bolt_tool.AddWorkingLoad()
        working_load.DisplayTime = time
        working_load.Name = "Working Load - " + str(time)

    return bolt_tool

with Transaction():         # Suppress GUI update until complete to speed the process
    # Create new bolt tools and collect in a list
    bolt_tools = [createBoltTool(id, boltPretensionIDs, name, DISP_TIMES) for id, name in zip(boltPretensionIDs, boltPretensionNames)]
    
# IDs for the bolt tools
# bolt_tool_IDs = [i.ObjectId for i in bolt_tools]

# All folders in the Solution branch
# sol_folders = analysis.GetChildren(DataModelObjectCategory.TreeGroupingFolder, True)
# sol_folders_names = [i.Name for i in sol_folders]


#print(str(time.time() - StartTime))
