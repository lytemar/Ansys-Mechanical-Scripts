"""
Retrieve Maximum Value Over Time for Directional Velocity Results in Tree Folder.
====================================================================================================

This script reads the Maximum Value Over Time for Directional Velocity results and wrties the data to a CSV file.

"""
################### Parameters ########################
analysisNumbers = [0]       # List of analysis systems to apply this script
DIRECTIONS = ['X', 'Y', 'Z']    # List of directions to extract
RESULTS_FOLDER = 'Directional Velocity for Named Selections: Results Scoping'   # Common part of results TreeGroupingFolder
"""
The tree grouping folder for each direction is composed for "<direction>-Axis " before the common part.  For example,
X-direction results are stored in a folder called `X-Axis Directional Velocity for Named Selections: Results Scoping` 
"""
################### End Parameters ########################


import wbjn
import datetime
import csv
import mech_dpf
import Ans.DataProcessing as dpf
cmd = 'returnValue(GetUserFilesDirectory())'
user_dir = wbjn.ExecuteCommand(ExtAPI, cmd)
mech_dpf.setExtAPI(ExtAPI)

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
    
    for d in DIRECTIONS:
        # Add prefix to results folder
        RESULTS_FOLDER_DIR = d.ToUpper() + '-Axis ' + RESULTS_FOLDER
        
        # Get all results that are grouped under the folder RESULTS_FOLDER
        resGroup = getResultsGroupByName(RESULTS_FOLDER_DIR, analysis.Solution)
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
                d.ToUpper() + '-Axis Max Directional Velocity [' + lengthUnit + '/' + timeUnit + ']']
        
        data = {}
        data[cols[0]] = resIDs
        data[cols[1]] = resNames
        data[cols[2]] = resLocNames
        data[cols[3]] = resMaxValues

        x = datetime.datetime.now()
        
        file_name_body = analysis.Name + ' - ' + d.ToUpper() + '-Axis_Max_Directional_Velocity_' + x.strftime("%m") + "-" + x.strftime("%d") + "-" + x.strftime("%y")
        writeCSV(user_dir + '/' + file_name_body + ".csv", data, cols)
        
        print("[INFO] Process completed for " + analysis.Name)
        print("Open File: " + chr(34) + user_dir + chr(92) + file_name_body + ".csv" + chr(34) + '\n')