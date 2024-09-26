"""
Read and Write-Out Total Deformation Results Object Table at all analysis times for items in TreeGrouping Folder.
=================================================================================================================

This script reads the Tabular Data for each total deformation result object and writes the data to a CSV file.

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
RESULTS_FOLDER = 'Total Deformation for Named Selections: Results Scoping'   # Name of results TreeGroupingFolder
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
        if group.Name == name:
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


def getTableData(t0,colNum):
    t0.Activate()
    tempTable = []
    paneTabular=ExtAPI.UserInterface.GetPane(MechanicalPanelEnum.TabularData)
    control = paneTabular.ControlUnknown
    for row in range(1,control.RowsCount+1):
        tempRow = []
        for col in range(colNum,colNum+1):
            cellText= control.cell(row ,col ).Text
            tempRow.append(cellText)
        tempTable.append(tempRow)
    return tempTable


for a in analysisNumbers:
    analysis = Model.Analyses[a]
    solver_data = analysis.Solution.SolverData
    
    # Get all results ovjects
    resGroup = getResultsGroupByName(RESULTS_FOLDER, analysis.Solution)
    resChildren = [r for r in resGroup.Children]
    resLocNames = [r.Location.Name for r in resChildren]
       
    # Get the current units
    force_unit = ExtAPI.DataModel.CurrentUnitFromQuantityName("Force")
    timeUnit = ExtAPI.DataModel.CurrentUnitFromQuantityName("Time")
    lengthUnit = ExtAPI.DataModel.CurrentUnitFromQuantityName("Length")
    stressUnit = ExtAPI.DataModel.CurrentUnitFromQuantityName("Stress")
    
    # Loop through all reaction probes and create a results dictionary
    res = {}
    for result in resChildren:
        result.Activate()
        rid = result.ObjectId
        res[rid] = {}
        res[rid]['Name'] = result.Name
        res[rid]['Location Name'] = result.Location.Name
        timeCol = [a[0] for a in getTableData(result,2)]
        res[rid]['Time'] = [float(t) for t in timeCol[1:]]
        resMin =[a[0] for a in getTableData(result,3)]
        res[rid]['Minimum'] = [float(x) for x in resMin[1:]]
        resMax =[a[0] for a in getTableData(result,4)]
        res[rid]['Maximum'] = [float(y) for y in resMax[1:]]
        resAvg =[a[0] for a in getTableData(result,5)]
        res[rid]['Average'] = [float(z) for z in resAvg[1:]]

        
    # Create data dictionary to written to output csv file
    data = {}
    # Data column names
    cols = ['Result Name',
            'Result ID',
            'Location Name',
            'Time [' + timeUnit + ']',
            'Minimum Total Deformation [' + lengthUnit + ']',
            'Maximum Total Deformation [' + lengthUnit + ']',
            'Average Total Deformation [' + lengthUnit + ']']

    for c in cols:
        data[c] = []

    for rid in sorted(res.keys()):
        for t in range(len(res[rid]['Time'])):
            data[cols[0]].append(res[rid]['Name'])
            data[cols[1]].append(rid)
            data[cols[2]].append(res[rid]['Location Name'])
            data[cols[3]].append(res[rid]['Time'][t])
            data[cols[4]].append(res[rid]['Minimum'][t])
            data[cols[5]].append(res[rid]['Maximum'][t])
            data[cols[6]].append(res[rid]['Average'][t])

    x = datetime.datetime.now()
    
    file_name_body = analysis.Name + ' - Total_Deformations_All_Times_' + x.strftime("%m") + "-" + x.strftime("%d") + "-" + x.strftime("%y")
    writeCSV(user_dir + '/' + file_name_body + ".csv", data, cols)
    
    print("[INFO] Process completed for " + analysis.Name)
    print("Open File: " + chr(34) + user_dir + chr(92) + file_name_body + ".csv" + chr(34) + '\n')