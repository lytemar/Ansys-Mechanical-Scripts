"""
Extract Maximum Total Deformation for all bodies in named selections at all analysis times.
===========================================================================================

This script extracts the maximum total deformation for each group of scoped bodies
within named selections for all analysis times.  The named selections that are of interest are
placed in a Tree Grouping folder called `Results Scoping`.

"""
################################## USER INPUTS ##################################
analysisNumbers = [0]        # LIST OF ANALYSIS SYSTEMS TO APPLY THIS SCRIPT
staticStrLastTimeOnly = 'Y'     # 'Y' = only output last time step for static structural, 'N' = output all time steps
lengthUnitStr = 'in'            # DESIRED LENGTH OUTPUT UNIT (usually 'in' or 'mm', case sensitive)
RANDOM_VIBRATION_SIGMA = 3      # SCALE FACTOR (SIGMA) FOR RESULTS OUTPUT
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
ANSYS_VER = str(ExtAPI.DataModel.Project.ProductVersion)


#  Place units in Ansys Mechanical format for output conversion
lengthUnit = '[' + lengthUnitStr + ']'
lengthQuan = Quantity(1, lengthUnitStr)         # Desired length output unit quantity


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
    solLenQuan = Quantity(1, solLenUnitStr)

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
    
    # Create displacement operator
    dispOp = dpf.operators.result.displacement()
    dispOp.inputs.data_sources.Connect(dataSource)
    dispOp.inputs.time_scoping.Connect(timeScoping)
    
    # Create the norm operator
    nrm = dpf.operators.math.norm_fc()
    nrm2 = dpf.operators.math.norm_fc()
    
    # Create the min-max operator
    minMaxOp = dpf.operators.min_max.min_max_fc()
    minMaxOp2 = dpf.operators.min_max.min_max()
    
    # Create the unit convert operator
    unitConvOp = dpf.operators.math.unit_convert_fc()
    unitConvOp.inputs.unit_name.Connect(lengthUnitStr)
    
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
        res[nid]['Name'] = n.Name.ToUpper()
        res[nid]['Times'] = []
        res[nid]['Sets'] = []
        res[nid]['Max Total Displacement'] = []
        #res[nid]['custom FC'] = []
        
        #Get the mesh element and node Ids
        elemIds = []
        nodeIds = []
        for nlocId in n.Location.Ids:
            solMesh = meshData.MeshRegionById(nlocId)
            elemIds += solMesh.ElementIds
            nodeIds += solMesh.NodeIds
        res[nid]['NS Location'] = n.Location.Ids
        res[nid]['Elements'] = elemIds
        res[nid]['Nodes'] = nodeIds
        
        # Scope displacement results to to node Ids
        scoping = dpf.Scoping()
        scoping.Ids = nodeIds
        scoping.Location = dpf.locations.nodal
        dispOp.inputs.mesh_scoping.Connect(scoping)
        uFC = dispOp.outputs.fields_container
        u = uFC.GetData()

        # Convert the total displacement result to desired units
        unitConvOp.inputs.fields_container.Connect(u)
        
        # Scale the displacement
        uFC = unitConvOp.outputs.fields_container
        scaleOp.inputs.fields_container.Connect(uFC)
        u = scaleOp.outputs.fields_container.GetData()
        
        # Remove fields with 0 entities by creating a new fields container by adding fields
        # if they are greater than zero.
        # Create empry fields_container and set label space equal to that of the displacement FC
        fc = dpf.FieldsContainer()
        fc.Labels = list(u.GetLabelSpace(0).Keys)
        fcLblSpcLen = len(fc.Labels)
        # Get fields with more than zero entities
        for i in range(u.FieldCount):
            if u[i].ElementaryDataCount > 0:
                fc.Add(u[i],u.GetLabelSpace(i))
        
        # Take the norm of the displacement from the custom fields container
        nrm.inputs.fields_container.Connect(fc)
        nrm_field = nrm.outputs.getfields_container()
        
        # Get the maximum total displacement for all times
        minMaxOp.inputs.fields_container.Connect(nrm_field)
        # Try to remove the fileds with 0 entites by creating a new field.  Not working yet.

        maxTotalDisp = minMaxOp.outputs.field_max.GetData()
        #maxTotalDisp = minMaxOp2.outputs.field_max.GetData()
        res[nid]['custom FC'] = fc
        for t in range(len(timeScoping.Ids)):
            res[nid]['Times'].append(all_times[t])
            res[nid]['Sets'].append(timeScoping.Ids[t])
            res[nid]['Max Total Displacement'].append(maxTotalDisp.Data[t])
        
    # Create data dictionary to written to output csv file
    data = {}
    cols = ['Named Selection',
            'Named Selection ID',
            'Time ' + timeUnit,
            'Set',
            'Max Total Displacement ' + lengthUnit]
    
    for c in cols:
        data[c] = []

    for nid in sorted(res.keys()):
        for t in range(len(timeScoping.Ids)):
            data[cols[0]].append(res[nid]['Name'])
            data[cols[1]].append(nid)
            data[cols[2]].append(res[nid]['Times'][t])
            data[cols[3]].append(res[nid]['Sets'][t])
            data[cols[4]].append(res[nid]['Max Total Displacement'][t])

    x = datetime.datetime.now()
    
    file_name_body = analysis.Name + ' - type=' + str(analysis_type) + ' - Max_Total_Displacement_' + x.strftime("%m") + "-" + x.strftime("%d") + "-" + x.strftime("%y")
    writeCSV(user_dir + '/' + file_name_body + ".csv", data, cols)
    
    print("[INFO] Process completed for " + analysis.Name)
    print("Open File: " + chr(34) + user_dir + chr(92) + file_name_body + ".csv" + chr(34) + '\n')
