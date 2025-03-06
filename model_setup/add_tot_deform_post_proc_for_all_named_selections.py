"""
Add total deformation post-processing items for all named selections within a tree grouping.
============================================================================================

"""
#import time
#StartTime = time.time()

################### Parameters ########################
analysisNumbers = [0]       # List of analysis systems to apply this script
NAMED_SEL_FOLDER = 'Results Scoping'        # Named selection folder name containing NS used for results scoping
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


def createTotalDeformation(ns):
    """
    Create a total deformation post-processing item scoped to a named selection given by ID.
    
    Parameters
    ----------
    ns : Model.NamedSelections.Children
        The child of a named selection
    
    Returns
    -------
    Ansys.ACT.Automation.Mechanical.Results.DeformationResults.TotalDeformation
        The newly created post processing total deformation
    """
    # add a total deformation
    total_def = analysis.Solution.AddTotalDeformation()
    
    # scope to Named Selection
    total_def.Location = ns
    
    return total_def


for a in analysisNumbers:
    analysis = Model.Analyses[a]
    
    # Get all named selections that are grouped under the folder NAMED_SEL_FOLDER
    ns = Model.NamedSelections
    nsGroup = getNamedSelectionsGroupByName(NAMED_SEL_FOLDER)
    nsChildren = [n for n in nsGroup.Children]
    
    with Transaction():             # Suppress GUI update until complete to speed the process
        # Create total deformation post processing items and collect in a list
        total_defs = [createTotalDeformation(ns) for ns in nsChildren]
        # Rename based on definition
    
    [e.RenameBasedOnDefinition() for e in total_defs]
    
    # Put all total deformation items into a group folder
    group = Tree.Group(total_defs)
    group.Name = "Total Deformation for Named Selections: " + NAMED_SEL_FOLDER
    
    analysis.Solution.EvaluateAllResults()
    
    Tree.Activate([analysis.Solution])
    
    
    