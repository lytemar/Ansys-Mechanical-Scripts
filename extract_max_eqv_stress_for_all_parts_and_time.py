"""
Extract Maximum Equivalent Stress for all bodies in named selections at all analysis times.
===========================================================================================

This script extracts the maximum von Mises equivalent stress for each group of scoped bodies
within named selections for all analysis times.  The named selections that are of interest are
placed in a Tree Grouping folder called `Results Scoping`.


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

NAMED_SEL_FOLDER = 'Results Scoping'        # Named selection folder name containing NS used for results scoping

#  Place units in Ansys Mechanical format for output conversion
lengthUnitStr = 'in'            # Desired length output unit
forceUnitStr = 'lbf'            # Desired force output unit
if forceUnitStr.ToLower() == 'lbf' and lengthUnitStr.ToLower() == 'in':
    stressUnitStr = 'psi'
elif forceUnitStr.ToUpper() == 'N' and lengthUnitStr.ToLower() == 'mm':
    stressUnitStr = 'MPa'
else:
    stressUnitStr = forceUnitStr + '*' + lengthUnitStr + '^-2'         # Desired stress output unit

lengthUnit = '[' + lengthUnitStr + ']'
forceUnit = '[' + forceUnitStr + ']'
stressUnit = '[' + stressUnitStr + ']'          # Desired stress output unit
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
    analysis_type = analysis.AnalysisType
    
    # Current solver units of interest and quantities
    solLenUnitStr = analysis.CurrentConsistentUnitFromQuantityName("Length")
    solAreaUnitStr = analysis.CurrentConsistentUnitFromQuantityName("Area")
    solForceUnitStr = analysis.CurrentConsistentUnitFromQuantityName("Force")
    solStressUnitStr = analysis.CurrentConsistentUnitFromQuantityName("Stress")
    solMomentUnitStr = analysis.CurrentConsistentUnitFromQuantityName("Moment")
    solStiffnessUnitStr = analysis.CurrentConsistentUnitFromQuantityName("Stiffness")
    solLenQuan = Quantity(1, solLenUnitStr)
    solAreaQuan = Quantity(1, solAreaUnitStr)
    solForceQuan = Quantity(1, solForceUnitStr)
    solStressQuan = Quantity(1, solStressUnitStr)
    solMomentQuan = Quantity(1, solMomentUnitStr)
    solStiffnessQuan = Quantity(1, solStiffnessUnitStr)
    
    # Result Data
    filepath = analysis.ResultFileName
    
    # Data Sources
    dataSources = dpf.DataSources()
    dataSources.SetResultFilePath(filepath)
    
    # Model and time steps
    model = dpf.Model(dataSources)
    all_times = model.TimeFreqSupport.TimeFreqs.Data
    timeUnitStr = str(model.TimeFreqSupport.TimeFreqs.Unit)               # Time stepping unit
    timeUnit = '[' + timeUnitStr + ']'
    number_sets = model.TimeFreqSupport.NumberSets      # Number of time steps
    timeIds = range(1, number_sets + 1)                 # List of time steps
    timeSets = model.TimeFreqSupport.TimeFreqs.ScopingIds  # List of time steps
    
    # Read mesh in results file
    mesh_op = dpf.operators.mesh.mesh_provider() 
    mesh_op.inputs.data_sources.Connect(dataSources)
    my_mesh = mesh_op.outputs.mesh.GetData()
    
    # Time scoping
    timeScoping = dpf.Scoping()
    timeScoping.Ids = timeIds
    timeScoping.Location = 'Time'
    
    # Get all named selections that are grouped under the folder NAMED_SEL_FOLDER
    ns = Model.NamedSelections
    nsGroup = getNamedSelectionsGroupByName(NAMED_SEL_FOLDER)
    nsChildren = [n for n in nsGroup.Children]
    nsNames = [n.Name for n in nsChildren]
    nsIDs = [n.ObjectId for n in nsChildren]
    nsEntities = [n.Entities for n in nsChildren]
    
    # Create Named Selection operator
    nameSelOp = dpf.operators.scoping.on_named_selection()
    nameSelOp.inputs.data_sources.Connect(dataSources)
    nameSelOp.inputs.requested_location.Connect('Nodal')
    
    # Create vonMises stress operator
    seqvOp = dpf.operators.result.stress_von_mises()
    seqvOp.inputs.data_sources.Connect(dataSources)
    seqvOp.inputs.time_scoping.Connect(timeScoping)
    
    # Create the min-max operator
    minMaxOp = dpf.operators.min_max.min_max_fc()
    
    # Loop through all named selections and create a results dictionary
    res = {}
    for n in nsChildren:
        nid = n.ObjectId
        res[nid] = {}
        res[nid]['Name'] = n.Name.ToUpper()
        res[nid]['Time'] = []
        res[nid]['Set'] = []
        res[nid]['Max Eqv. Stress'] = []
        # Scope von Mises stress results to active named selection
        nameSelOp.inputs.named_selection_name.Connect(n.Name.ToUpper())
        meshScoping = nameSelOp.outputs.mesh_scoping.GetData()
        seqvOp.inputs.mesh_scoping.Connect(meshScoping)
        vmStress = seqvOp.outputs.fields_container.GetData()
        # Convert the von Mises stress to desired stress units
        unitConvOp = dpf.operators.math.unit_convert_fc()
        unitConvOp.inputs.fields_container.Connect(vmStress)
        unitConvOp.inputs.unit_name.Connect(stressUnitStr)
        vmStress = unitConvOp.outputs.fields_container.GetData()
        # Get the maximum von Mises stress for all times
        minMaxOp.inputs.fields_container.Connect(vmStress)
        maxVmStress = minMaxOp.outputs.field_max.GetData()
        for t in range(len(timeScoping.Ids)):
            res[nid]['Time'].append(all_times[t])
            res[nid]['Set'].append(t+1)
            res[nid]['Max Eqv. Stress'].append(maxVmStress.Data[t])
        
    # Create data dictionary to written to output csv file
    data = {}
    cols = ['Named Selection',
            'Named Selection ID',
            'Time ' + timeUnit,
            'Set',
            'Max Eqv. Stress ' + stressUnit]
    
    for c in cols:
        data[c] = []

    for nid in sorted(res.keys()):
        for t in range(len(timeScoping.Ids)):
            data[cols[0]].append(res[nid]['Name'])
            data[cols[1]].append(nid)
            data[cols[2]].append(res[nid]['Time'][t])
            data[cols[3]].append(t+1)
            data[cols[4]].append(res[nid]['Max Eqv. Stress'][t])

    x = datetime.datetime.now()
    
    file_name_body = analysis.Name + ' - type=' + str(analysis_type) + ' - Max_Eqv_Stress_' + x.strftime("%m") + "-" + x.strftime("%d") + "-" + x.strftime("%y")
    writeCSV(user_dir + '/' + file_name_body + ".csv", data, cols)
    
    print("[INFO] Process completed for " + analysis.Name)
    print("Open File: " + chr(34) + user_dir + chr(92) + file_name_body + ".csv" + chr(34) + '\n')
