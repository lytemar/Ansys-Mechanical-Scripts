"""
Get node and value of max eqv stress from a static structural.  Then get corresponding eqv stress in linear dynamics child analyses.
====================================================================================================================================

This script extracts the maximum von Mises equivalent stress for each group of scoped bodies within named selections
for specified analysis times for a static structural analysis that is a prestress analysis for linear dynamics analyses.
Then, using the node of max stress from the static structural, the corresponding equivalent stress is obtained for the
downstream linear dynamics analyses.  The named selections that are of interest are placed in a Tree Grouping folder
called `Results Scoping`.


This has been tested on 2024 R2 and 2025 R1.


"""

################################## USER INPUTS ##################################
StaticStrAnalysisNumber = 0     # Analysis numbers for the static structural analysis (susally = 0)
childAnalysisNumbers = [2, 3]          # LIST OF CHILD ANALYSIS SYSTEMS TO APPLY THIS SCRIPT
lengthUnitStr = 'in'            # DESIRED LENGTH OUTPUT UNIT (usually 'in' or 'mm', case sensitive)
forceUnitStr = 'lbf'            # DESIRED FOURCE OUTPUT UNIT (usually 'lbf' or 'N', case sensitive)
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


if lengthUnitStr.ToLower() == 'in' and forceUnitStr.ToLower() == 'lbf':
    stressUnitStr = 'psi'
elif lengthUnitStr.ToLower() == 'mm' and forceUnitStr.ToUpper() == 'N':
    stressUnitStr = 'MPa'
else:
    stressUnitStr = forceUnitStr + '*' + lengthUnitStr + '^-2'          # Desired stress output unit
momentUnitStr = forceUnitStr + '*' + lengthUnitStr                      # Desired moment/torque output unit
stiffnessUnitStr = forceUnitStr + '*' + lengthUnitStr + '^-1'           # Desired stiffness output unit


#  Place units in Ansys Mechanical format for output conversion
lengthUnit = '[' + lengthUnitStr + ']'
forceUnit = '[' + forceUnitStr + ']'            # Desired force output unit
stressUnit = '[' + stressUnitStr + ']'          # Desired stress output unit

lengthQuan = Quantity(1, lengthUnitStr)         # Desired length output unit quantity
forceQuan = Quantity(1, forceUnitStr)           # Desired force output unit quantity
momentQuan = Quantity(1, momentUnitStr)         # Desired moment output unit quantity
stressQuan = Quantity(1, stressUnitStr)         # Desired stress output unit quantity

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


def getNodeAtMax(fc):
    """
    Get node ID at the location of max value from a fields container
    
    Parameters
    ----------
    fc : fields container
        Nodal stress results

    Returns
    -------
    Integer node ID
    """
    max_val = 0.0
    result = 0
    values = fc.Data
    nodes = fc.ScopingIds
    for n in nodes:
        v = max(fc.GetEntityDataById(n))
        if v >= max_val:
            max_val = v
            result = n
    return result


##################### GET RESULTS FROM THE BASE STATIC STRUCTURAL ANALYSIS #########################
# Get the data source from the Static Structural Analysis
ssAnalysis = ExtAPI.DataModel.Project.Model.Analyses[StaticStrAnalysisNumber]
ssResultsFile = ssAnalysis.ResultFileName
dataSource = dpf.DataSources()
dataSource.SetResultFilePath(ssResultsFile)
meshData = ssAnalysis.MeshData

# Static Structural model and time steps
ssModel = dpf.Model(dataSource)
mesh = ssModel.Mesh
ssAllTimes = ssModel.TimeFreqSupport.TimeFreqs.Data
ssTimeUnitStr = str(ssModel.TimeFreqSupport.TimeFreqs.Unit)               # Time stepping unit
ssTimeUnit = '[' + ssTimeUnitStr + ']'
ssNumberSets = ssModel.TimeFreqSupport.NumberSets      # Number of time steps
ssTimeIds = range(1, ssNumberSets + 1)                 # List of time steps
ssTimeSets = ssModel.TimeFreqSupport.TimeFreqs.ScopingIds  # List of time steps

# Read mesh in results file
meshOp = dpf.operators.mesh.mesh_provider() 
meshOp.inputs.data_sources.Connect(dataSource)
my_mesh = meshOp.outputs.mesh.GetData()

# Time scoping
timeScoping = dpf.Scoping()
timeScoping.Ids = [ssTimeIds[len(ssTimeIds)-1]]       # Last time step
#timeScoping.Ids = ssTimeIds   # all times
timeScoping.Location = 'Time'

# Get all named selections that are grouped under the folder NAMED_SEL_FOLDER
nsGroup = getNamedSelectionsGroupByName(NAMED_SEL_FOLDER)
ns = [n for n in nsGroup.Children]
nsNames = [n.Name for n in ns]
nsIds = [n.ObjectId for n in ns]
nsEntities = [n.Entities for n in ns]

 # Create Named Selection operator
nameSelOp = dpf.operators.scoping.on_named_selection()
nameSelOp.inputs.data_sources.Connect(dataSource)
nameSelOp.inputs.requested_location.Connect('Nodal')
    
# Create vonMises stress operator
seqvOp = dpf.operators.result.stress_von_mises()
seqvOp.inputs.data_sources.Connect(dataSource)
seqvOp.inputs.time_scoping.Connect(timeScoping)
seqvOp.inputs.requested_location.Connect('Nodal')
    
# Create the min-max operator
#minMaxOp = dpf.operators.min_max.min_max_fc()
minMaxOp = dpf.operators.min_max.min_max()

# Create the unit convert operator
unitConvOp = dpf.operators.math.unit_convert_fc()
unitConvOp.inputs.unit_name.Connect(stressUnitStr)

# For each named delection, get the element Ids, Node Ids, and store them in a dictionary
res = {}
for n in ns:
    nid = n.ObjectId
    res[nid] = {}
    res[nid]['Name'] = n.Name
    res[nid]['SS Eqv Stress'] = []
    res[nid]['SS Times'] = []
    res[nid]['SS Sets'] = []
    res[nid]['SS Max Eqv Stress'] = []
    
    #Get the mesh element and node Ids
    elemIds = []
    nodeIds = []
    for nlocId in n.Location.Ids:
        solMesh = meshData.MeshRegionById(nlocId)
        elemIds += solMesh.ElementIds
        nodeIds += solMesh.NodeIds
    res[nid]['Elements'] = elemIds
    res[nid]['Nodes'] = nodeIds
    
    # Scope the von Mises stress results to the element Ids
    scoping = dpf.Scoping()
    scoping.Ids = elemIds
    scoping.Location = dpf.locations.elemental
    seqvOp.inputs.mesh_scoping.Connect(scoping)
    vmStressFC = seqvOp.outputs.fields_container
    vmStress = vmStressFC.GetData()
    
    # Remove fields with 0 entities by creating a new fields container by adding fields
    # if they are greater than zero.
    # Create empry fields_container and set label space equal to that of the stress FC
    fc = dpf.FieldsContainer()
    fc.Labels = list(vmStress.GetLabelSpace(0).Keys)
    fcLblSpcLen = len(fc.Labels)
    # Get fields with more than zero entities
    j = 1
    for i in range(vmStress.FieldCount):
        if vmStress[i].ElementaryDataCount > 0:
            fc.Add(vmStress[i],vmStress.GetLabelSpace(i))
            j = j + 1
    
    # Convert the von Mises stress to desired stress units
    unitConvOp.inputs.fields_container.Connect(fc)
    vmStress = unitConvOp.outputs.fields_container.GetData()

    # Add values of stress for all times in time scoping
    for t in range(len(timeScoping.Ids)):
        minMaxOp.inputs.field.Connect(vmStress[t])
        maxVmStress = minMaxOp.outputs.getfield_max()
        res[nid]['SS Times'].append(ssAllTimes[t])
        res[nid]['SS Sets'].append(timeScoping.Ids[t])
        res[nid]['SS Eqv Stress'].append(vmStress[t].Data[0])
        res[nid]['SS Eqv Stress FC Before Unit Conv'] = vmStressFC.GetData()
        res[nid]['SS Eqv Stress FC'] = vmStress
        res[nid]['SS Node with Max Stress'] = getNodeAtMax(vmStress[t])
        res[nid]['SS Max Eqv Stress'] = maxVmStress.Data[0]


# Create data dictionary to be written to output csv file
data = {}
cols = ['Named Selection',
        'Named Selection ID',
        'Stat Str Time ' + ssTimeUnit,
        'Stat Str Set',
        'Stat Str Max Eqv Stress ' + stressUnit,
        'Node of Max']

for c in cols:
    data[c] = []

for nid in sorted(res.keys()):
    for t in range(len(timeScoping.Ids)):
        data[cols[0]].append(res[nid]['Name'])
        data[cols[1]].append(nid)
        data[cols[2]].append(res[nid]['SS Times'][t])
        data[cols[3]].append(timeScoping.Ids[t])
        data[cols[4]].append(res[nid]['SS Max Eqv Stress'])
        data[cols[5]].append(res[nid]['SS Node with Max Stress'])
        
####################### GATHER RESULTS FROM CHILD ANALYSES ##################################
"""
For each named selection, write out the equivalent stress at the node that has the maximum
equivalent stress value in the Static Structural system.
"""

if len(childAnalysisNumbers) > 0:
    for a in childAnalysisNumbers:
        analysis = ExtAPI.DataModel.Project.Model.Analyses[a]
        solver_data = analysis.Solution.SolverData
        analysis_type = analysis.AnalysisType
        analysis_settings = analysis.AnalysisSettings
        analysis_name = analysis.Name
      
        # Set the scale factor = 1 for non Random Vibration analyses
        if str(analysis_type).ToLower() == 'spectrum':
            scaleFactor = RANDOM_VIBRATION_SIGMA
        else:
            scaleFactor = 1
        
        # Result Data
        filepath = analysis.ResultFileName
        
        # Data Source
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
        timeSets = model.TimeFreqSupport.TimeFreqs.ScopingIds  # List of time steps
        
        # Read mesh in results file
        meshOp.inputs.data_sources.Connect(dataSource)
        my_mesh = meshOp.outputs.mesh.GetData()
        
        # Time scoping
        timeScoping.Ids = timeIds
        
        # Create von Mises stress operator
        seqvOp.inputs.data_sources.Connect(dataSource)
        seqvOp.inputs.time_scoping.Connect(timeScoping)
       
        # Create scale operator
        scaleOp = dpf.operators.math.scale_fc()
        if ANSYS_VER.ToUpper() == '2024 R2':
            scaleOp.inputs.ponderation.Connect(scaleFactor)   # 2024 R2
        else:
            scaleOp.inputs.weights.Connect(scaleFactor)       # 2025 R2
        
        # Get the von Mises stress at the corresponding node of the static structural analysis.  This is an 
        # "alternating stress" component of the analysis.
        for n in ns:
            nid = n.ObjectId
            node = res[nid]['SS Node with Max Stress']
            scoping = dpf.Scoping()
            scoping.Ids = res[nid]['Elements']
            scoping.Location = dpf.locations.elemental
            seqvOp.inputs.mesh_scoping.Connect(scoping)
            vmStress = seqvOp.outputs.fields_container.GetData()
            
            # Remove fields with 0 entities by creating a new fields container by adding fields
            # if they are greater than zero.
            # Create empry fields_container and set label space equal to that of the stress FC
            fc = dpf.FieldsContainer()
            fc.Labels = list(vmStress.GetLabelSpace(0).Keys)
            fcLblSpcLen = len(fc.Labels)
            # Get fields with more than zero entities
            j = 1
            for i in range(vmStress.FieldCount):
                if vmStress[i].ElementaryDataCount > 0:
                    fc.Add(vmStress[i],vmStress.GetLabelSpace(i))
                    j = j + 1
            
            # Convert the von Mises stress to desired stress units
            unitConvOp.inputs.fields_container.Connect(fc)
            # Scale the von Mises stress
            vmStressFC = unitConvOp.outputs.fields_container
            scaleOp.inputs.fields_container.Connect(vmStressFC)
            vmStress = scaleOp.outputs.fields_container.GetData()
            res[nid][analysis_name + ' vm_scldFC'] = vmStress
            res[nid][analysis_name + ' Eqv Stress at Max SS Node'] = max(vmStress[0].GetEntityDataById(node))
            
        # Add max stress column to data dictionary
        cols.append(analysis_name + ' Eqv Stress at Max SS Node ' + stressUnit)
        data[analysis_name + ' Eqv Stress at Max SS Node ' + stressUnit] = []
        for nid in sorted(res.keys()):
            data[analysis_name + ' Eqv Stress at Max SS Node ' + stressUnit].append(res[nid][analysis_name + ' Eqv Stress at Max SS Node'])


x = datetime.datetime.now()
    
file_name_body = 'Max_Eqv_stress_summary_' + x.strftime("%m") + "-" + x.strftime("%d") + "-" + x.strftime("%y")
writeCSV(user_dir + '/' + file_name_body + ".csv", data, cols)
    
print("[INFO] Process completed for Max Eqv Stress results")
print("Open File: " + chr(34) + user_dir + chr(92) + file_name_body + ".csv" + chr(34))


