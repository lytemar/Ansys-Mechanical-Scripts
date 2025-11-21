"""
Retrieve Nodal Force Reactions for all Nodes Within a Named Selection.
=====================================================================================

This has been tested on 2025 R2.


"""
################################## USER INPUTS ##################################
analysisNumbers = [0]        # LIST OF ANALYSIS SYSTEMS TO APPLY THIS SCRIPT
staticStrLastTimeOnly = 'N'     # 'Y' = only output last time step for static structural, 'N' = output all time steps
lengthUnitStr = 'in'            # DESIRED LENGTH OUTPUT UNIT (usually 'in' or 'mm', case sensitive)
forceUnitStr = 'lbf'            # DESIRED FOURCE OUTPUT UNIT (usually 'lbf' or 'N', case sensitive)
RANDOM_VIBRATION_SIGMA = 3      # SCALE FACTOR (SIGMA) FOR RESULTS OUTPUT
NAMED_SEL_FOLDER = 'Reaction Force Faces'        # Named selection folder name containing NS used for results scoping
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
forceUnit = '[' + forceUnitStr + ']'
momentUnitStr = forceUnitStr + '*' + lengthUnitStr              # Desired moment/torque output unit
momentUnit = '[' + momentUnitStr + ']'

lengthQuan = Quantity(1, lengthUnitStr)                         # Desired length output unit quantity
forceQuan = Quantity(1, forceUnitStr)                           # Desired Force output unit quantity
momentQuan = Quantity(1, momentUnitStr)                         # Desired moment output unit quantity

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
        

def removeFieldsWithZeroEntities(fc):
    """
    Remove fields with 0 entities by creating a new fields container
    
    Parameters
    ----------
    fc : FieldsContainer
        Source FieldsContainer that may contain 0 entity fields
    
    Returns
    -------
    FieldsContainer
    """
    # Remove fields with 0 entities by creating a new fields container by adding fields if they are greater than zero.
    # Create empry fields_container and set label space equal to that of the source FC
    result = dpf.FieldsContainer()
    result.Labels = list(fc.GetLabelSpace(0).Keys)
    resultLblSpcLen = len(result.Labels)
    # Get fields with more than zero entities
    for i in range(fc.FieldCount):
        if fc[i].ElementaryDataCount > 0:
            result.Add(fc[i],fc.GetLabelSpace(i))
    return result
    

def createRestrictedNodalScopingFieldsContainer(fc, nodalScoping):
    """
    Create a new fields container by restricting a source fields container to restricted nodal scoping
    
    Parameters
    ----------
    fc : FieldsContainer
        source FieldsContainer that is to be reduced in scope
    nodalScoping : dpf.Scoping
        Desired nodal scoping
    
    Returns
    -------
    FieldsContainer
    """
    result = dpf.FieldsContainer()
    result.Labels = list(fc.GetLabelSpace(0).Keys)
    
    return result


desiredReactions = ["X", "Y", "Z"]   # List of reaction force directions (may be one of ("X", "Y", "Z")

for a in analysisNumbers:
    analysis = Model.Analyses[a]
    solver_data = analysis.Solution.SolverData
    analysis_type = analysis.AnalysisType
    meshData = analysis.MeshData
    
    # Current solver units of interest and quantities
    solLenUnitStr = analysis.CurrentConsistentUnitFromQuantityName("Length")
    solForceUnitStr = analysis.CurrentConsistentUnitFromQuantityName("Force")
    solMomentUnitStr = analysis.CurrentConsistentUnitFromQuantityName("Moment")
    solLenQuan = Quantity(1, solLenUnitStr)
    solForceQuan = Quantity(1, solForceUnitStr)
    solMomentQuan = Quantity(1, solMomentUnitStr)
    
    # Result Data
    filepath = analysis.ResultFileName
    
    # Data Sources
    dataSource = dpf.DataSources()
    dataSource.SetResultFilePath(filepath)
    
    # Model, mesh and time steps
    model = dpf.Model(dataSource)
    mesh = model.Mesh
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
    
    # Nodal coordinates operator (about the global coordinate system)
    ndCoordsOp = dpf.operators.mesh.node_coordinates()
    ndUnitConvOp = dpf.operators.math.unit_convert()
    ndUnitConvOp.inputs.unit_name.Connect(lengthUnitStr)
    ndCoordsOp.inputs.mesh.Connect(mesh)
    nodeCoords = ndCoordsOp.outputs.getcoordinates_as_field()
    ndUnitConvOp.inputs.entity_to_convert.Connect(nodeCoords)
    nodeCoords = ndUnitConvOp.outputs.getconverted_entity_as_field()
    nodePosUnits = nodeCoords.Unit
    nodePosQuan = Quantity(1, nodePosUnits)
    
    """
    # Global element nodal forces for debugging purposes
    # Elemental nodal forces operator
    globalScopingOp = dpf.operators.scoping.from_mesh()
    globalScopingOp.inputs.mesh.Connect(mesh)
    globalScopingOp.inputs.requested_location.Connect('Nodal')
    myScoping = globalScopingOp.outputs.scoping.GetData()
    elemGlobalNFOp = dpf.operators.result.element_nodal_forces()
    elemGlobalNFOp.inputs.data_sources.Connect(dataSource)
    elemGlobalNFOp.inputs.time_scoping.Connect(timeScoping)
    elemGlobalNFOp.inputs.mesh_scoping.Connect(myScoping)
    elemGlobalNFOp.inputs.requested_location.Connect('Nodal')
    elemGlobalNodeForcesFC = elemGlobalNFOp.outputs.fields_container
    elemGlobalNodeForces = elemGlobalNodeForcesFC.GetData()
    
    # Remove fields with 0 entities by creating a new fields container
    elemGlobalNodeForcesFC = removeFieldsWithZeroEntities(elemGlobalNodeForces)
    
    # Create component selector operators
    compSelFcOp = dpf.operators.logic.component_selector_fc()

    # Convert the reaction force to desired force units
    unitConvOp = dpf.operators.math.unit_convert_fc()
    unitConvOp.inputs.unit_name.Connect(forceUnitStr)
    unitConvOp.inputs.fields_container.Connect(elemGlobalNodeForcesFC)
    
    # Scale the reaction force
    elemGlobalNodeForcesFC = unitConvOp.outputs.fields_container
    scaleOp.inputs.fields_container.Connect(elemGlobalNodeForcesFC)
    elemGlobalNodeForcesFC = scaleOp.outputs.fields_container
    elemGlobalNodeForces = elemGlobalNodeForcesFC.GetData()
    elemGlobalNodeForceUnits = elemGlobalNodeForces[0].Unit
    elemGlobalNodeForceQuan = Quantity(1, elemGlobalNodeForceUnits)
    """
    
    # Create scale operator and set the scale factor = -1 for non Random Vibration analyses
    # Negative scaling since the reaction force is the negative of the nodal forces
    scaleOp = dpf.operators.math.scale_fc()
    if str(analysis_type).ToLower() == 'spectrum':
        scaleFactor = -RANDOM_VIBRATION_SIGMA
    else:
        scaleFactor = -1
    if ANSYS_VER.ToUpper() == '2024 R2' or ANSYS_VER.ToUpper() == '2025 R1':
        scaleOp.inputs.ponderation.Connect(scaleFactor)   # 2024 R2 or 2025 R1
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
        res[nid]['FX'] = []
        res[nid]['FY'] = []
        res[nid]['FZ'] = []
        res[nid]['MX'] = []
        res[nid]['MY'] = []
        res[nid]['MZ'] = []
        res[nid]['Total Reaction Force'] = []
        res[nid]['Total Reaction Moment'] = []
        
        #Get the mesh element and node Ids
        elemIds = []
        nodeIds = []
        for nlocId in n.Location.Ids:
            solMesh = meshData.MeshRegionById(nlocId)
            elemIds += solMesh.ElementIds
            nodeIds += solMesh.NodeIds
        nodeIds = list(set(nodeIds))
        elemIds = list(set(elemIds))
        res[nid]['Elements'] = elemIds
        res[nid]['Nodes'] = nodeIds
        res[nid]['Num Nodes'] = len(nodeIds)
        
        # Scope the results to the element Ids
        scoping = dpf.Scoping()
        scoping.Ids = nodeIds
        scoping.Location = dpf.locations.nodal
        
        # Elemental nodal forces operator
        elemNFOp = dpf.operators.result.element_nodal_forces()
        elemNFOp.inputs.data_sources.Connect(dataSource)
        elemNFOp.inputs.time_scoping.Connect(timeScoping)
        elemNFOp.inputs.mesh_scoping.Connect(scoping)
        elemNFOp.inputs.requested_location.Connect('Nodal')
        elemNodeForcesFC = elemNFOp.outputs.fields_container
        elemNodeForces = elemNodeForcesFC.GetData()
        
        # Remove fields with 0 entities by creating a new fields container
        #elemNodeForcesFC = removeFieldsWithZeroEntities(elemNodeForces)
        
        # Create component selector operators
        compSelFcOp = dpf.operators.logic.component_selector_fc()
    
        # Convert the reaction force to desired force units
        unitConvOp = dpf.operators.math.unit_convert_fc()
        unitConvOp.inputs.unit_name.Connect(forceUnitStr)
        unitConvOp.inputs.fields_container.Connect(elemNodeForcesFC)
        
        # Scale the reaction force
        elemNodeForcesFC = unitConvOp.outputs.fields_container
        scaleOp.inputs.fields_container.Connect(elemNodeForcesFC)
        elemNodeForcesFC = scaleOp.outputs.fields_container
        elemNodeForces = elemNodeForcesFC.GetData()
        elemNodeForceUnits = elemNodeForces[0].Unit
        elemNodeForceQuan = Quantity(1, elemNodeForceUnits)
        #print("Element nodal force units: " + elemNodeForceUnits)
        
        # Compute the total force of all force components at all times
        sumFcOp = dpf.operators.math.accumulate_fc()
        sumFcOp.inputs.time_scoping.Connect(timeScoping)
        sumFcOp.inputs.fields_container.Connect(elemNodeForcesFC)
        fsumFC = sumFcOp.outputs.fields_container.GetData()         # Net force vector
        normFcOp = dpf.operators.math.norm_fc()
        normFcOp.inputs.fields_container.Connect(fsumFC)
        totalForce = normFcOp.outputs.fields_container.GetData()    # Force magnitude
        compSelFcOp.inputs.fields_container.Connect(fsumFC)
        
        # Create a field rescricted to the nodes in the scoping
        #nodeCoordsScop = dpf.Field()
        #nodeCoordsScop.Location = 'Nodal'
        #nodeCoordsScop.Unit = nodePosUnits
        #[nodeCoordsScop.Add(node, nodeCoords.GetEntityDataById(node)) for node in nodeIds]
        #print("Nodal coordinates units: " + nodeCoords.Unit)
        
        # Conversion factors
        forceConvFac = elemNodeForceQuan/forceQuan
        momentConvFac = (elemNodeForceQuan * nodePosQuan)/momentQuan

        for tid, t in enumerate(timeIds):
            res[nid]['Times'].append(all_times[t-1])
            res[nid]['Sets'].append(t)
            
            # Create cross product operator
            crossProdOp = dpf.operators.math.cross_product()
            #crossProdOp.inputs.fieldA.Connect(nodeCoordsScop)
            crossProdOp.inputs.fieldA.Connect(nodeCoords)
            crossProdOp.inputs.fieldB.Connect(elemNodeForces[tid])
            
            # Compute the moment field
            momReacts = crossProdOp.outputs.field.GetData()
            sumOp = dpf.operators.math.accumulate()
            sumOp.inputs.time_scoping.Connect(timeScoping)
            sumOp.inputs.fieldA.Connect(momReacts)
            momSum = sumOp.outputs.field.GetData()                  # Net moment vector
            normOp = dpf.operators.math.norm()
            normOp.inputs.field.Connect(momSum)
            totalMoment = normOp.outputs.field.GetData()            # Moment magnitude
            compSelFieldOp = dpf.operators.logic.component_selector()
            compSelFieldOp.inputs.field.Connect(momSum)
            
            for j,d in enumerate(desiredReactions):
                compSelFcOp.inputs.component_number.Connect(j)
                compSelFieldOp.inputs.component_number.Connect(j)
                res[nid]['F' + d].append(compSelFcOp.outputs.fields_container.GetData()[tid].Data[0])
                res[nid]['M' + d].append(compSelFieldOp.outputs.field.GetData().Data[0])
            res[nid]['Total Reaction Force'].append(totalForce[tid].Data[0])
            res[nid]['Total Reaction Moment'].append(totalMoment.Data[0])


    # Create data dictionary to written to output csv file
    data = {}
    cols = ['Named Selection',
            'Named Selection ID',
            'Number of Nodes',
            'Time ' + timeUnit,
            'Set',
            'FX ' + forceUnit,
            'FY ' + forceUnit,
            'FZ ' + forceUnit,
            'F_Total ' + forceUnit,
            'MX ' + momentUnit,
            'MY ' + momentUnit,
            'MZ ' + momentUnit,
            'M_Total ' + momentUnit]
    
    for c in cols:
        data[c] = []

    for nid in sorted(res.keys()):
        for t in range(len(timeIds)):
            data[cols[0]].append(res[nid]['Name'])
            data[cols[1]].append(nid)
            data[cols[2]].append(res[nid]['Num Nodes'])
            data[cols[3]].append(res[nid]['Times'][t])
            data[cols[4]].append(res[nid]['Sets'][t])
            data[cols[5]].append(res[nid]['FX'][t])
            data[cols[6]].append(res[nid]['FY'][t])
            data[cols[7]].append(res[nid]['FZ'][t])
            data[cols[8]].append(res[nid]['Total Reaction Force'][t])
            data[cols[9]].append(res[nid]['MX'][t])
            data[cols[10]].append(res[nid]['MY'][t])
            data[cols[11]].append(res[nid]['MZ'][t])
            data[cols[12]].append(res[nid]['Total Reaction Moment'][t])

    x = datetime.datetime.now()
    
    file_name_body = analysis.Name + ' - type=' + str(analysis_type) + ' - Surface_Reaction_Forces_' + x.strftime("%m") + "-" + x.strftime("%d") + "-" + x.strftime("%y")
    writeCSV(user_dir + '/' + file_name_body + ".csv", data, cols)
    
    print("[INFO] Process completed for " + analysis.Name)
    print("Open File: " + chr(34) + user_dir + chr(92) + file_name_body + ".csv" + chr(34) + '\n')



