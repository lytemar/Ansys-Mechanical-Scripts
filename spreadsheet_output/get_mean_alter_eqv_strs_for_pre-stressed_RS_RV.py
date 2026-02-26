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
static_str_analysis_num = 0     # Analysis numbers for the static structural analysis (susally = 0)
child_analysis_nums = [2, 3]          # LIST OF CHILD ANALYSIS SYSTEMS TO APPLY THIS SCRIPT
len_unit_str = 'in'            # DESIRED LENGTH OUTPUT UNIT (usually 'in' or 'mm', case sensitive)
force_unit_str = 'lbf'            # DESIRED FOURCE OUTPUT UNIT (usually 'lbf' or 'N', case sensitive)
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


if len_unit_str.ToLower() == 'in' and force_unit_str.ToLower() == 'lbf':
    stress_unit_str = 'psi'
elif len_unit_str.ToLower() == 'mm' and force_unit_str.ToUpper() == 'N':
    stress_unit_str = 'MPa'
else:
    stress_unit_str = force_unit_str + '*' + len_unit_str + '^-2'          # Desired stress output unit
moment_unit_str = force_unit_str + '*' + len_unit_str                      # Desired moment/torque output unit
stiffness_unit_str = force_unit_str + '*' + len_unit_str + '^-1'           # Desired stiffness output unit


#  Place units in Ansys Mechanical format for output conversion
len_unit = '[' + len_unit_str + ']'
force_unit = '[' + force_unit_str + ']'            # Desired force output unit
stress_unit = '[' + stress_unit_str + ']'          # Desired stress output unit

len_quan = Quantity(1, len_unit_str)         # Desired length output unit quantity
force_quan = Quantity(1, force_unit_str)           # Desired force output unit quantity
moment_quan = Quantity(1, moment_unit_str)         # Desired moment output unit quantity
stress_quan = Quantity(1, stress_unit_str)         # Desired stress output unit quantity

def write_csv(filename, data, cols):
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


def find_tree_grouping_folders(item):
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
    

def get_named_sels_group_by_name(name):
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
    groups = find_tree_grouping_folders(Model.NamedSelections)
    for group in groups:
        if group.Name == name:
            return group


def get_node_at_max(fc):
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
ss_analysis = ExtAPI.DataModel.Project.Model.Analyses[static_str_analysis_num]
ss_res_file = ss_analysis.ResultFileName
data_source = dpf.DataSources()
data_source.SetResultFilePath(ss_res_file)
mesh_data = ss_analysis.MeshData

# Static Structural model and time steps
ss_model = dpf.Model(data_source)
mesh = ss_model.Mesh
ss_all_times = ss_model.TimeFreqSupport.TimeFreqs.Data
ss_time_unit_str = str(ss_model.TimeFreqSupport.TimeFreqs.Unit)               # Time stepping unit
ss_time_unit = '[' + ss_time_unit_str + ']'
ss_num_sets = ss_model.TimeFreqSupport.NumberSets      # Number of time steps
ss_time_ids = range(1, ss_num_sets + 1)                 # List of time steps
ss_time_sets = ss_model.TimeFreqSupport.TimeFreqs.ScopingIds  # List of time steps
ss_active_times = [ss_all_times[t-1] for t in ss_time_ids]       # Solution times corresponding to available ss_time_ids

# Read mesh in results file
mesh_op = dpf.operators.mesh.mesh_provider() 
mesh_op.inputs.data_sources.Connect(data_source)
my_mesh = mesh_op.outputs.mesh.GetData()

# Time scoping
time_scoping = dpf.Scoping()
time_scoping.Ids = [ss_time_ids[len(ss_time_ids)-1]]       # Last time step
#time_scoping.Ids = ss_time_ids   # all times
time_scoping.Location = 'Time'

# Get all named selections that are grouped under the folder NAMED_SEL_FOLDER
ns_group = get_named_sels_group_by_name(NAMED_SEL_FOLDER)
ns = [n for n in ns_group.Children]
ns_names = [n.Name for n in ns]
ns_ids = [n.ObjectId for n in ns]
ns_entities = [n.Entities for n in ns]

 # Create Named Selection operator
name_sel_op = dpf.operators.scoping.on_named_selection()
name_sel_op.inputs.data_sources.Connect(data_source)
name_sel_op.inputs.requested_location.Connect('Nodal')
    
# Create vonMises stress operator
seqv_op = dpf.operators.result.stress_von_mises()
seqv_op.inputs.data_sources.Connect(data_source)
seqv_op.inputs.time_scoping.Connect(time_scoping)
seqv_op.inputs.requested_location.Connect('Nodal')
    
# Create the min-max operator
#min_max_op = dpf.operators.min_max.min_max_fc()
min_max_op = dpf.operators.min_max.min_max()

# Create the unit convert operator
unit_conv_op = dpf.operators.math.unit_convert_fc()
unit_conv_op.inputs.unit_name.Connect(stress_unit_str)

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
    elem_ids = []
    node_ids = []
    for nlocId in n.Location.Ids:
        sol_mesh = mesh_data.MeshRegionById(nlocId)
        elem_ids += sol_mesh.ElementIds
        node_ids += sol_mesh.NodeIds
    res[nid]['Elements'] = elem_ids
    res[nid]['Nodes'] = node_ids
    
    # Scope the von Mises stress results to the element Ids
    scoping = dpf.Scoping()
    scoping.Ids = elem_ids
    scoping.Location = dpf.locations.elemental
    seqv_op.inputs.mesh_scoping.Connect(scoping)
    vm_stress_fc = seqv_op.outputs.fields_container
    vm_stress = vm_stress_fc.GetData()
    
    # Remove fields with 0 entities by creating a new fields container by adding fields
    # if they are greater than zero.
    # Create empry fields_container and set label space equal to that of the stress FC
    fc = dpf.FieldsContainer()
    fc.Labels = list(vm_stress.GetLabelSpace(0).Keys)
    fc_lbl_spc_len = len(fc.Labels)
    # Get fields with more than zero entities
    j = 1
    for i in range(vm_stress.FieldCount):
        if vm_stress[i].ElementaryDataCount > 0:
            fc.Add(vm_stress[i],vm_stress.GetLabelSpace(i))
            j = j + 1
    
    # Convert the von Mises stress to desired stress units
    unit_conv_op.inputs.fields_container.Connect(fc)
    vm_stress = unit_conv_op.outputs.fields_container.GetData()

    # Add values of stress for all times in time scoping
    for t in range(len(time_scoping.Ids)):
        min_max_op.inputs.field.Connect(vm_stress[t])
        max_vm_stress = min_max_op.outputs.getfield_max()
        res[nid]['SS Times'].append(ss_all_times[t])
        res[nid]['SS Sets'].append(time_scoping.Ids[t])
        res[nid]['SS Eqv Stress'].append(vm_stress[t].Data[0])
        res[nid]['SS Eqv Stress FC Before Unit Conv'] = vm_stress_fc.GetData()
        res[nid]['SS Eqv Stress FC'] = vm_stress
        res[nid]['SS Node with Max Stress'] = get_node_at_max(vm_stress[t])
        res[nid]['SS Max Eqv Stress'] = max_vm_stress.Data[0]


# Create data dictionary to be written to output csv file
data = {}
cols = ['Named Selection',
        'Named Selection ID',
        'Stat Str Time ' + ss_time_unit,
        'Stat Str Set',
        'Stat Str Max Eqv Stress ' + stress_unit,
        'Node of Max']

for c in cols:
    data[c] = []

for nid in sorted(res.keys()):
    for t in range(len(time_scoping.Ids)):
        data[cols[0]].append(res[nid]['Name'])
        data[cols[1]].append(nid)
        data[cols[2]].append(res[nid]['SS Times'][t])
        data[cols[3]].append(time_scoping.Ids[t])
        data[cols[4]].append(res[nid]['SS Max Eqv Stress'])
        data[cols[5]].append(res[nid]['SS Node with Max Stress'])
        
####################### GATHER RESULTS FROM CHILD ANALYSES ##################################
"""
For each named selection, write out the equivalent stress at the node that has the maximum
equivalent stress value in the Static Structural system.
"""

if len(child_analysis_nums) > 0:
    for a in child_analysis_nums:
        analysis = ExtAPI.DataModel.Project.Model.Analyses[a]
        solver_data = analysis.Solution.SolverData
        analysis_type = analysis.AnalysisType
        analysis_settings = analysis.AnalysisSettings
        analysis_name = analysis.Name
      
        # Set the scale factor = 1 for non Random Vibration analyses
        if str(analysis_type).ToLower() == 'spectrum':
            scale_fac = RANDOM_VIBRATION_SIGMA
        else:
            scale_fac = 1
        
        # Result Data
        file_path = analysis.ResultFileName
        
        # Data Source
        data_source = dpf.DataSources()
        data_source.SetResultFilePath(file_path)
        
        # Model and time steps
        model = dpf.Model(data_source)
        all_times = model.TimeFreqSupport.TimeFreqs.Data
        time_unit_str = str(model.TimeFreqSupport.TimeFreqs.Unit)               # Time stepping unit
        time_unit = '[' + time_unit_str + ']'
        number_sets = model.TimeFreqSupport.NumberSets      # Number of time steps
        time_ids = range(1, number_sets + 1)                 # List of time steps
        if str(analysis_type).ToLower() == 'spectrum':
            time_ids = [2]
        elif str(analysis_type).ToLower() == 'responsespectrum':
            time_ids = [1]
        time_sets = model.TimeFreqSupport.TimeFreqs.ScopingIds  # List of time steps
        active_times = [ss_all_times[t-1] for t in time_ids]       # Solution times corresponding to available ss_time_ids
        
        # Read mesh in results file
        mesh_op.inputs.data_sources.Connect(data_source)
        my_mesh = mesh_op.outputs.mesh.GetData()
        
        # Time scoping
        time_scoping.Ids = time_ids
        
        # Create von Mises stress operator
        seqv_op.inputs.data_sources.Connect(data_source)
        seqv_op.inputs.time_scoping.Connect(time_scoping)
       
        # Create scale operator
        scale_op = dpf.operators.math.scale_fc()
        if ANSYS_VER.ToUpper() == '2024 R2':
            scale_op.inputs.ponderation.Connect(scale_fac)   # 2024 R2
        else:
            scale_op.inputs.weights.Connect(scale_fac)       # 2025 R2
        
        # Get the von Mises stress at the corresponding node of the static structural analysis.  This is an 
        # "alternating stress" component of the analysis.
        for n in ns:
            nid = n.ObjectId
            node = res[nid]['SS Node with Max Stress']
            scoping = dpf.Scoping()
            scoping.Ids = res[nid]['Elements']
            scoping.Location = dpf.locations.elemental
            seqv_op.inputs.mesh_scoping.Connect(scoping)
            vm_stress = seqv_op.outputs.fields_container.GetData()
            
            # Remove fields with 0 entities by creating a new fields container by adding fields
            # if they are greater than zero.
            # Create empry fields_container and set label space equal to that of the stress FC
            fc = dpf.FieldsContainer()
            fc.Labels = list(vm_stress.GetLabelSpace(0).Keys)
            fc_lbl_spc_len = len(fc.Labels)
            # Get fields with more than zero entities
            j = 1
            for i in range(vm_stress.FieldCount):
                if vm_stress[i].ElementaryDataCount > 0:
                    fc.Add(vm_stress[i],vm_stress.GetLabelSpace(i))
                    j = j + 1
            
            # Convert the von Mises stress to desired stress units
            unit_conv_op.inputs.fields_container.Connect(fc)
            # Scale the von Mises stress
            vm_stress_fc = unit_conv_op.outputs.fields_container
            scale_op.inputs.fields_container.Connect(vm_stress_fc)
            vm_stress = scale_op.outputs.fields_container.GetData()
            res[nid][analysis_name + ' vm_scldFC'] = vm_stress
            res[nid][analysis_name + ' Eqv Stress at Max SS Node'] = max(vm_stress[0].GetEntityDataById(node))
            
        # Add max stress column to data dictionary
        cols.append(analysis_name + ' Eqv Stress at Max SS Node ' + stress_unit)
        data[analysis_name + ' Eqv Stress at Max SS Node ' + stress_unit] = []
        for nid in sorted(res.keys()):
            data[analysis_name + ' Eqv Stress at Max SS Node ' + stress_unit].append(res[nid][analysis_name + ' Eqv Stress at Max SS Node'])


x = datetime.datetime.now()
    
file_name_body = 'Max_Eqv_stress_summary_' + x.strftime("%m") + "-" + x.strftime("%d") + "-" + x.strftime("%y")
write_csv(user_dir + '/' + file_name_body + ".csv", data, cols)
    
print("[INFO] Process completed for Max Eqv Stress results")
print("Open File: " + chr(34) + user_dir + chr(92) + file_name_body + ".csv" + chr(34))


