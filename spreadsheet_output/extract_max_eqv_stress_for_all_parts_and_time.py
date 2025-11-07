"""
Extract Maximum Equivalent Stress for all bodies in named selections at all analysis times.
===========================================================================================

This script extracts the maximum von Mises equivalent stress for each group of scoped bodies
within named selections for all analysis times.  The named selections that are of interest are
placed in a Tree Grouping folder called `Results Scoping`.


"""

################################## USER INPUTS ##################################
analysisNumbers = [0, 2, 3]        # LIST OF ANALYSIS SYSTEMS TO APPLY THIS SCRIPT
staticStrLastTimeOnly = 'Y'     # 'Y' = only output last time step for static structural, 'N' = output all time steps
lengthUnitStr = 'in'            # DESIRED LENGTH OUTPUT UNIT (usually 'in' or 'mm', case sensitive)
forceUnitStr = 'lbf'            # DESIRED FOURCE OUTPUT UNIT (usually 'lbf' or 'N', case sensitive)
RANDOM_VIBRATION_SIGMA = 3      # SCALE FACTOR (SIGMA) FOR RESULTS OUTPUT
ANSYS_VER = '2024 R2'           # Ansys version ('2024 R2', '2025 R1', '2025 R2')
NAMED_SEL_FOLDER = 'Results Scoping'        # Named selection folder name containing NS used for results scoping
# Set the scale factor for Random Vibration Analyses
# The last part of the Enumeration can be (Sigma1, Sigma2, Sigma3, UserDefined)
SCALE_FACTOR = Ansys.Mechanical.DataModel.Enums.ScaleFactorType.Sigma3
#################################################################################

import wbjn
import datetime
import csv
import mech_dpf
import Ans.DataProcessing as dpf
import materials
cmd = 'returnValue(GetUserFilesDirectory())'
user_dir = wbjn.ExecuteCommand(ExtAPI, cmd)
mech_dpf.setExtAPI(ExtAPI)


if lengthUnitStr.ToLower() == 'in' and forceUnitStr.ToLower() == 'lbf':
    stressUnitStr = 'psi'
elif lengthUnitStr.ToLower() == 'mm' and forceUnitStr.ToUpper() == 'N':
    stressUnitStr = 'MPa'
else:
    stressUnitStr = forceUnitStr + '*' + lengthUnitStr + '^-2'          # Desired stress output unit

#  Place units in Ansys Mechanical format for output conversion
lengthUnit = '[' + lengthUnitStr + ']'
stressUnit = '[' + stressUnitStr + ']'          # Desired stress output unit

lengthQuan = Quantity(1, lengthUnitStr)         # Desired length output unit quantity
stressQuan = Quantity(1, stressUnitStr)         # Desired stress output unit quantity


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
    meshData = analysis.MeshData
    
    # Current solver units of interest and quantities
    solLenUnitStr = analysis.CurrentConsistentUnitFromQuantityName("Length")
    solStressUnitStr = analysis.CurrentConsistentUnitFromQuantityName("Stress")
    solLenQuan = Quantity(1, solLenUnitStr)
    solStressQuan = Quantity(1, solStressUnitStr)
    
    # Result Data
    filepath = analysis.ResultFileName
    
    # Data Sources
    dataSource = dpf.DataSources()
    dataSource.SetResultFilePath(filepath)
    
    # Model and time steps
    model = dpf.Model(dataSource)
    all_times = model.TimeFreqSupport.TimeFreqs.Data
    timeUnitStr = str(model.TimeFreqSupport.TimeFreqs.Unit)               # Time stepping unit
    timeUnit = '[' + timeUnitStr + ']'
    number_sets = model.TimeFreqSupport.NumberSets      # Number of time steps
    timeIds = range(1, number_sets + 1)                 # List of time steps
    if str(analysis_type).ToLower() == 'spectrum':
        timeIds = [2]
    elif str(analysis_type).ToLower() == 'responsespectrum':
        timeIds = [1]
    elif str(analysis_type).ToLower() == 'static':
        if staticStrLastTimeOnly.ToLower() == 'y':
            timeIds = [timeIds[len(timeIds)-1]]            # Last time step
    timeSets = model.TimeFreqSupport.TimeFreqs.ScopingIds  # List of time steps
    
    # Read mesh in results file
    mesh_op = dpf.operators.mesh.mesh_provider() 
    mesh_op.inputs.data_sources.Connect(dataSource)
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
    nameSelOp.inputs.data_sources.Connect(dataSource)
    nameSelOp.inputs.requested_location.Connect('Nodal')
    
    # Create vonMises stress operator
    seqvOp = dpf.operators.result.stress_von_mises()
    seqvOp.inputs.data_sources.Connect(dataSource)
    seqvOp.inputs.time_scoping.Connect(timeScoping)
    
    # Create the min-max operator
    minMaxOp = dpf.operators.min_max.min_max_fc()
    
    # Create the unit convert operator
    unitConvOp = dpf.operators.math.unit_convert_fc()
    unitConvOp.inputs.unit_name.Connect(stressUnitStr)
    
    # Create scale operator and set the scale factor = 1 for non Random Vibration analyses
    scaleOp = dpf.operators.math.scale_fc()
    if str(analysis_type).ToLower() == 'spectrum':
        scaleFactor = RANDOM_VIBRATION_SIGMA
    else:
        scaleFactor = 1
    if ANSYS_VER.ToUpper() == '2024 R2':
        scaleOp.inputs.ponderation.Connect(scaleFactor)   # 2024 R2
    else:
        scaleOp.inputs.weights.Connect(scaleFactor)       # 2025 R2
    
    # Loop through all named selections and create a results dictionary
    res = {}
    for n in nsChildren:
        nid = n.ObjectId
        res[nid] = {}
        res[nid]['Name'] = n.Name
        res[nid]['Times'] = []
        res[nid]['Sets'] = []
        res[nid]['Max Eqv. Stress'] = []
        #Get the mesh element Ids
        solMesh = meshData.MeshRegionById(n.Location.Ids[0])
        res[nid]['Elements'] = solMesh.ElementIds
        # Scope the von Mises stress results to the element Ids
        scoping = dpf.Scoping()
        scoping.Ids = solMesh.ElementIds
        scoping.Location = dpf.locations.elemental
        # Scope von Mises stress results to active named selection
        seqvOp.inputs.mesh_scoping.Connect(scoping)
        vmStressFC = seqvOp.outputs.fields_container
        vmStress = vmStressFC.GetData()
        # Convert the von Mises stress to desired stress units
        unitConvOp.inputs.fields_container.Connect(vmStress)
        # Scale the von Mises stress
        vmStressFC = unitConvOp.outputs.fields_container
        scaleOp.inputs.fields_container.Connect(vmStressFC)
        vmStress = scaleOp.outputs.fields_container.GetData()
        # Get the maximum von Mises stress for all times
        minMaxOp.inputs.fields_container.Connect(vmStress)
        maxVmStress = minMaxOp.outputs.field_max.GetData()
        for t in range(len(timeScoping.Ids)):
            res[nid]['Times'].append(all_times[t])
            res[nid]['Sets'].append(timeScoping.Ids[t])
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
            data[cols[2]].append(res[nid]['Times'][t])
            data[cols[3]].append(res[nid]['Sets'][t])
            data[cols[4]].append(res[nid]['Max Eqv. Stress'][t])

    x = datetime.datetime.now()
    
    file_name_body = analysis.Name + ' - type=' + str(analysis_type) + ' - Max_Eqv_Stress_' + x.strftime("%m") + "-" + x.strftime("%d") + "-" + x.strftime("%y")
    writeCSV(user_dir + '/' + file_name_body + ".csv", data, cols)
    
    print("[INFO] Process completed for " + analysis.Name)
    print("Open File: " + chr(34) + user_dir + chr(92) + file_name_body + ".csv" + chr(34) + '\n')
