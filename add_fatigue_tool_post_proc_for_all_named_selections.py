"""
Add fatigue tool post-processing items for all named selections within a tree grouping.
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


def createFatigueTool(ns):
    """
    Create a fatigue tool post-processing item scoped to a named selection given by ID.
    
    Parameters
    ----------
    ns : Model.NamedSelections.Children
        The child of a named selection
    
    Returns
    -------
    Ansys.ACT.Automation.Mechanical.FatigueTool
        The newly created post processing equivalent stress
    """
    # add a fatigue tool
    fat_tool = analysis.Solution.AddFatigueTool()
    fat_tool.Name = 'Fatigue Tool - ' + ns.Name
    
    # add Life, Damage, Safety Factor and Biaxiality
    life = fat_tool.AddLife()
    life.Location = ns
    damage = fat_tool.AddDamage()
    damage.Location = ns
    fs = fat_tool.AddSafetyFactor()
    fs.Location = ns
    biax = fat_tool.AddBiaxialityIndication()
    biax.Location = ns
    
    return fat_tool


for a in analysisNumbers:
    analysis = Model.Analyses[a]
    
    # Get all named selections that are grouped under the folder NAMED_SEL_FOLDER
    ns = Model.NamedSelections
    nsGroup = getNamedSelectionsGroupByName(NAMED_SEL_FOLDER)
    nsChildren = [n for n in nsGroup.Children]
    
    with Transaction():             # Suppress GUI update until complete to speed the process
        # Create fatigue tool post processing items and collect in a list
        fat_tools = [createFatigueTool(ns) for ns in nsChildren]
        # Rename based on definition
    
    # Put all fatigue tools into a group folder
    group = Tree.Group(fat_tools)
    group.Name = "Fatigue Tools for Named Selections: " + NAMED_SEL_FOLDER
    
    analysis.Solution.EvaluateAllResults()
    
    Tree.Activate([analysis.Solution])
    
    
    