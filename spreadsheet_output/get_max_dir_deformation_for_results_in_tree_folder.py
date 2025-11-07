"""
Retrieve Maximum Value Over Time for Directional Deformation Results in Tree Folder.
====================================================================================================

This script reads the Maximum Value Over Time for Directional Deformation results and wrties the data to a CSV file.

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
analysisNumbers = [0]       # List of analysis systems to apply this script
RESULTS_FOLDER = 'Directional Deformation for Named Selections: Results Scoping'   # Name of results TreeGroupingFolder
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
    

def getResultsGroupByName(name, type):
    """
    Get the Equivalent Stress grouping folder by name
    
    Parameters
    ----------
    name : str
        Name of the Stress Results grouping folder
    type : Ansys.ACT.Automation.Mechanical.Model type
    
    Returns
    -------
    Ansys.ACT.Automation.Mechanical.TreeGroupingFolder
    """
    groups = findTreeGroupingFolders(type)
    for group in groups:
        if group.Name.ToLower() == name.ToLower():
            return group


def writeCSV(filename, data, cols):
    """
    Function to write python data to a csv file.
    
    Parameters
    ----------
    filename : str
        Filepath for the output file
    data : dict
        Data dictionary
    cols : list of str
        Column header names
    
    Returns
    -------
    None
    """
    with open(filename, 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(cols)
        writer.writerows(zip(*[data[col] for col in cols]))


for a in analysisNumbers:
    analysis = Model.Analyses[a]
    solver_data = analysis.Solution.SolverData
    
    # Get the current units
    force_unit = ExtAPI.DataModel.CurrentUnitFromQuantityName("Force")
    timeUnit = ExtAPI.DataModel.CurrentUnitFromQuantityName("Time")
    lengthUnit = ExtAPI.DataModel.CurrentUnitFromQuantityName("Length")
    stressUnit = ExtAPI.DataModel.CurrentUnitFromQuantityName("Stress")
       
    # Get all results that are grouped under the folder RESULTS_FOLDER
    resGroup = getResultsGroupByName(RESULTS_FOLDER, analysis.Solution)
    resChildren = [r for r in resGroup.Children]
    resNames = [r.Name for r in resChildren]
    resIDs = [r.ObjectId for r in resChildren]
    resLocNames = [r.Location.Name for r in resChildren]
    resMaxValues = [r.MaximumOfMaximumOverTime.Value for r in resChildren]
    
    # Create data dictionary to written to output csv file
    data = {}
    # Data column names
    cols = ['Result ID',
            'Result Name',
            'Scope Name',
            'Max Directional Deformation [' + lengthUnit + ']']
    
    data = {}
    data[cols[0]] = resIDs
    data[cols[1]] = resNames
    data[cols[2]] = resLocNames
    data[cols[3]] = resMaxValues

    x = datetime.datetime.now()
    
    file_name_body = analysis.Name + ' - Max_Directional_Deformation_' + x.strftime("%m") + "-" + x.strftime("%d") + "-" + x.strftime("%y")
    writeCSV(user_dir + '/' + file_name_body + ".csv", data, cols)
    
    print("[INFO] Process completed for " + analysis.Name)
    print("Open File: " + chr(34) + user_dir + chr(92) + file_name_body + ".csv" + chr(34) + '\n')