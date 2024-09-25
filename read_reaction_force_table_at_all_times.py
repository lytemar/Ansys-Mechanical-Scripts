"""
Retrieve Reaction Forces Values at all analysis times for Reaction Probes in Force Reactions Folder.
====================================================================================================

This script reads the Tabular Data for each force reaction probe and wrties the data to a CSV file.

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
################### End Parameters ########################


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
    
    # Get all force reaction probes
    ForceReactionCurrAnalysis = [child for child in analysis.Solution.Children if child.DataModelObjectCategory == DataModelObjectCategory.ForceReaction]
    
    # Get force unit
    force_unit = ExtAPI.DataModel.CurrentUnitFromQuantityName("Force")
    timeUnit = ExtAPI.DataModel.CurrentUnitFromQuantityName("Time")
    
    # Loop through all reaction probes and create a results dictionary
    res = {}
    for result in ForceReactionCurrAnalysis:
        result.Activate()
        rid = result.ObjectId
        res[rid] = {}
        res[rid]['Name'] = result.Name
        timeCol = [a[0] for a in getTableData(result,2)]
        res[rid]['Time'] = [float(t) for t in timeCol[1:]]
        xReaction =[a[0] for a in getTableData(result,3)]
        res[rid]['FX'] = [float(x) for x in xReaction[1:]]
        yReaction =[a[0] for a in getTableData(result,4)]
        res[rid]['FY'] = [float(y) for y in yReaction[1:]]
        zReaction =[a[0] for a in getTableData(result,5)]
        res[rid]['FZ'] = [float(z) for z in zReaction[1:]]
        totalReaction =[a[0] for a in getTableData(result,6)]
        res[rid]['F_Total'] = [float(z) for z in totalReaction[1:]]
        matrix_full = [[timeCol[i], xReaction[i], yReaction[i], zReaction[i], totalReaction[i]] for i in range(len(timeCol))]
        
    # Create data dictionary to written to output csv file
    data = {}
    # Data column names
    cols = ['Force Reaction Name',
            'Force Reaction ID',
            'Time [' + timeUnit + ']',
            'FX [' + force_unit + ']',
            'FY [' + force_unit + ']',
            'FZ [' + force_unit + ']',
            'Total Force [' + force_unit + ']']

    for c in cols:
        data[c] = []

    for rid in sorted(res.keys()):
        for t in range(len(res[rid]['Time'])):
            data[cols[0]].append(res[rid]['Name'])
            data[cols[1]].append(rid)
            data[cols[2]].append(res[rid]['Time'][t])
            data[cols[3]].append(res[rid]['FX'][t])
            data[cols[4]].append(res[rid]['FY'][t])
            data[cols[5]].append(res[rid]['FZ'][t])
            data[cols[6]].append(res[rid]['F_Total'][t])

    x = datetime.datetime.now()
    
    file_name_body = analysis.Name + ' - Force_Reactions_' + x.strftime("%m") + "-" + x.strftime("%d") + "-" + x.strftime("%y")
    writeCSV(user_dir + '/' + file_name_body + ".csv", data, cols)
    
    print("[INFO] Process completed for " + analysis.Name)
    print("Open File: " + chr(34) + user_dir + chr(92) + file_name_body + ".csv" + chr(34) + '\n')