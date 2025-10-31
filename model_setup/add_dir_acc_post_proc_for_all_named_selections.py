"""
Add directional acceleration post-processing items for all named selections within a tree grouping.
===================================================================================================

"""
#import time
#StartTime = time.time()
import sys

################### Parameters ########################
analysisNumbers = [2, 3, 4]       # List of analysis systems to apply this script
NAMED_SEL_FOLDER = 'Results Scoping'        # Named selection folder name containing NS used for results scoping
DIRECTIONS = ['X', 'Y', 'Z']         # Direction axis:  one of 'X', 'Y', or 'Z'
# Set the scale factor for Random Vibration Analyses
# The last part of the Enumeration can be (Sigma1, Sigma2, Sigma3, UserDefined)
SCALE_FACTOR = Ansys.Mechanical.DataModel.Enums.ScaleFactorType.Sigma3
################### End Parameters ########################

def findTreeGroupingFolders(item):
    """
    Return a list of Tree Grouping Folders for a Model item containder (e.g., Named Selections)
    
    Parameters
    ----------
    item : ExtAPI.DataModel.Project.Model item
        Model tree item that would contain one or more Tree Grouping Folders
    
    Returns
    -------
    List
    """
    TreeGroupingFolderList = []
    for child in item.Children:
        if child.GetType() == Ansys.ACT.Automation.Mechanical.TreeGroupingFolder:
            TreeGroupingFolderList.append(child)
    return TreeGroupingFolderList
    

def getNamedSelectionsGroupByName(name):
    """
    Get the Named Selections grouping folder by name
    
    Parameters
    ----------
    name : str
        Name of the Named Selections grouping folder
    
    Returns
    -------
    Ansys.ACT.Automation.Mechanical.TreeGroupingFolder
    """
    groups = findTreeGroupingFolders(Model.NamedSelections)
    for group in groups:
        if group.Name == name:
            return group


def createDirAcceleration(ns, dir):
    """
    Create a directional acceleration post-processing item scoped to a named selection given by ID.
    
    Parameters
    ----------
    ns : Model.NamedSelections.Children
        The child of a named selection
    dir : str
        Axis for which the result is to be created
    
    Returns
    -------
    Ansys.ACT.Automation.Mechanical.Results.DeformationResults.DirectionalAcceleration
        The newly created post processing directional velocity
    """
    # add a total deformation
    if str(analysis_type).ToLower() == "spectrum":
        dir_acc = analysis.Solution.AddDirectionalAccelerationPSD()
        dir_acc.ScaleFactor = SCALE_FACTOR
    elif str(analysis_type).ToLower() == "responsespectrum":
        dir_acc = analysis.Solution.AddDirectionalAccelerationRS()
    else:
        dir_acc = analysis.Solution.AddDirectionalAcceleration()
    if dir.ToLower() == 'x':
        dir_acc.NormalOrientation = NormalOrientationType.XAxis
    elif dir.ToLower() == 'y':
        dir_acc.NormalOrientation = NormalOrientationType.YAxis
    elif dir.ToLower() == 'z':
        dir_acc.NormalOrientation = NormalOrientationType.ZAxis
    else:
        print("Incorrect direction axis.  Need one of 'X', 'Y', or 'Z'.")
        sys.exit()
    
    # scope to Named Selection
    dir_acc.Location = ns
    
    return dir_acc


for a in analysisNumbers:
    analysis = Model.Analyses[a]
    analysis_type = analysis.AnalysisType
    
    for d in DIRECTIONS:
    
        # Get all named selections that are grouped under the folder NAMED_SEL_FOLDER
        ns = Model.NamedSelections
        nsGroup = getNamedSelectionsGroupByName(NAMED_SEL_FOLDER)
        nsChildren = [n for n in nsGroup.Children]
        
        with Transaction():             # Suppress GUI update until complete to speed the process
            # Create directional acceleration post processing items and collect in a list
            dir_accs = [createDirAcceleration(ns, d) for ns in nsChildren]
            # Rename based on definition
        
        [e.RenameBasedOnDefinition() for e in dir_accs]
        for e in dir_accs:
            fig = e.AddFigure()
            fig.Name = e.Name
            fig.Text = e.Name
        
        # Put all directional acceleration items into a group folder
        group = Tree.Group(dir_accs)
        group.Name = d + "-Axis Directional Acceleration for Named Selections: " + NAMED_SEL_FOLDER
    
    analysis.Solution.EvaluateAllResults()
    
    Tree.Activate([analysis.Solution])
    
    
    