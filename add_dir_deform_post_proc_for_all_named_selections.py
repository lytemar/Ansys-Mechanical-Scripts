"""
Add directional deformation post-processing items for all named selections within a tree grouping.
==================================================================================================

"""
#import time
#StartTime = time.time()
import sys

################### Parameters ########################
analysisNumbers = [2, 3, 4]       # List of analysis systems to apply this script
NAMED_SEL_FOLDER = 'Results Scoping'        # Named selection folder name containing NS used for results scoping
DIRECTIONS = ['Y', 'X', 'Z']         # Direction axis:  one of 'X', 'Y', or 'Z'
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


def createDirDeformation(ns, dir):
    """
    Create a directional deformation post-processing item scoped to a named selection given by ID.
    
    Parameters
    ----------
    ns : Model.NamedSelections.Children
        The child of a named selection
    dir : str
        Axis for which the result is to be created
    
    Returns
    -------
    Ansys.ACT.Automation.Mechanical.Results.DeformationResults.DirectionalDeformation
        The newly created post processing directional deformation
    """
    # add a directional deformation
    dir_def = analysis.Solution.AddDirectionalDeformation()
    if dir.ToLower() == 'x':
        dir_def.NormalOrientation = NormalOrientationType.XAxis
    elif dir.ToLower() == 'y':
        dir_def.NormalOrientation = NormalOrientationType.YAxis
    elif dir.ToLower() == 'z':
        dir_def.NormalOrientation = NormalOrientationType.ZAxis
    else:
        print("Incorrect direction axis.  Need one of 'X', 'Y', or 'Z'.")
        sys.exit()
    
    # scope to Named Selection
    dir_def.Location = ns
    
    return dir_def


for a, d in zip(analysisNumbers, DIRECTIONS):
    analysis = Model.Analyses[a]
    
    # Get all named selections that are grouped under the folder NAMED_SEL_FOLDER
    ns = Model.NamedSelections
    nsGroup = getNamedSelectionsGroupByName(NAMED_SEL_FOLDER)
    nsChildren = [n for n in nsGroup.Children]
    
    with Transaction():             # Suppress GUI update until complete to speed the process
        # Create directional deformation post processing items and collect in a list
        total_defs = [createDirDeformation(ns, d) for ns in nsChildren]
        # Rename based on definition
    
    [e.RenameBasedOnDefinition() for e in total_defs]
    
    # Put all directional deformation items into a group folder
    group = Tree.Group(total_defs)
    group.Name = "Directional Deformation for Named Selections: " + NAMED_SEL_FOLDER
    
    analysis.Solution.EvaluateAllResults()
    
    Tree.Activate([analysis.Solution])
    
    
    