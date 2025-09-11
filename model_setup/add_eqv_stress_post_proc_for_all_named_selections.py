"""
Add equivalent stress post-processing items for all named selections within a tree grouping.
============================================================================================


"""

#import time
#StartTime = time.time()

################### Parameters ########################
analysisNumbers = [3]       # List of analysis systems to apply this script
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


def createEqvStress(ns):
    """
    Create an equivalent stress post-processing item scoped to a named selection given by ID.
    
    Parameters
    ----------
    ns : Model.NamedSelections.Children
        The child of a named selection
    
    Returns
    -------
    Ansys.ACT.Automation.Mechanical.Results.StressResults.EquivalentStress
        The newly created post processing equivalent stress
    """
    # add an equivalent stress
    if str(analysis_type).ToLower() == "spectrum":
        eqv_stress = analysis.Solution.AddEquivalentStressPSD()
    elif str(analysis_type).ToLower() == 'responsespectrum':
        eqv_stress = analysis.Solution.AddEquivalentStressRS()
    else:
        eqv_stress = analysis.Solution.AddEquivalentStress()
    
    # scope to Named Selection
    eqv_stress.Location = ns
    
    return eqv_stress


for a in analysisNumbers:
    analysis = Model.Analyses[a]
    analysis_type = analysis.AnalysisType
    
    # Get all named selections that are grouped under the folder NAMED_SEL_FOLDER
    ns = Model.NamedSelections
    nsGroup = getNamedSelectionsGroupByName(NAMED_SEL_FOLDER)
    nsChildren = [n for n in nsGroup.Children]
    
    with Transaction():             # Suppress GUI update until complete to speed the process
        # Create equivalent stress post processing items and collect in a list
        eqv_stresses = [createEqvStress(ns) for ns in nsChildren]
        # Rename based on definition
    
    [e.RenameBasedOnDefinition() for e in eqv_stresses]
    
    # Put all equivalent stress items into a group folder
    group = Tree.Group(eqv_stresses)
    group.Name = "Eqv Stresses for Named Selections: " + NAMED_SEL_FOLDER
    
    analysis.Solution.EvaluateAllResults()
    
    Tree.Activate([analysis.Solution])
    
    
    
