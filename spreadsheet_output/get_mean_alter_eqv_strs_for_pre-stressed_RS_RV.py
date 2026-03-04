"""
Get node and value of max eqv stress from a static structural.  Then get corresponding eqv stress in linear dynamics child analyses.
====================================================================================================================================

This script extracts the maximum von Mises equivalent stress for each group of scoped bodies within named selections
for specified analysis times for a static structural analysis that is a prestress analysis for linear dynamics analyses.
Then, the corresponding equivalent stress from the child analysis is calculated and exported as Alternating stress.
The named selections that are of interest are placed in a Tree Grouping folder called `Results Scoping`.

This has been tested on 2024 R2 and 2025 R1.

"""

################################## USER INPUTS ##################################
STATIC_STR_ANALYSIS_NUM = 0     # Analysis numbers for the static structural analysis (susally = 0)
STATIC_STR_LAST_TIME_ONLY = 'y'     # 'Y' = only output last time step for static structural, 'N' = output all time steps
CHILD_ANALYSIS_NUMS = [2, 3]          # LIST OF CHILD ANALYSIS SYSTEMS TO APPLY THIS SCRIPT
ASSESS_FATIGUE = 'y'        # Flag to assess fatigue using Soderberg, Goodman, ASME, etc.
FATIGUE_LINE_TYPE = 'Ger'     # Fatigue line type: one of {'G': Goodman, 'S': Soderberg, 'Ger': Gerber, 'ASME': ASME-elliptic}
                              # Requires S-N curve and strength parameters for material in Engineering Data
COMPUTE_DAMAGE = 'n'        # Flag to use Miner's rule to compute damage (requires S-N curve for material in Engineering Data)
LEN_UNIT_STR = 'in'            # DESIRED LENGTH OUTPUT UNIT (usually 'in' or 'mm', case sensitive)
FORCE_UNIT_STR = 'lbf'            # DESIRED FOURCE OUTPUT UNIT (usually 'lbf' or 'N', case sensitive)
NAMED_SEL_FOLDER = 'Results Scoping'        # Named selection folder name containing NS used for results scoping
#################################################################################

import wbjn
import datetime
import csv
import mech_dpf
import Ans.DataProcessing as dpf
import materials
import sys
cmd = 'returnValue(GetUserFilesDirectory())'
user_dir = wbjn.ExecuteCommand(ExtAPI, cmd)
mech_dpf.setExtAPI(ExtAPI)
ANSYS_VER = str(ExtAPI.DataModel.Project.ProductVersion)

if LEN_UNIT_STR.ToLower() == 'in' and FORCE_UNIT_STR.ToLower() == 'lbf':
    stress_unit_str = 'psi'
elif LEN_UNIT_STR.ToLower() == 'mm' and FORCE_UNIT_STR.ToUpper() == 'N':
    stress_unit_str = 'MPa'
else:
    stress_unit_str = FORCE_UNIT_STR + '*' + LEN_UNIT_STR + '^-2'          # Desired stress output unit
stiffness_unit_str = FORCE_UNIT_STR + '*' + LEN_UNIT_STR + '^-1'           # Desired stiffness output unit

#  Place units in Ansys Mechanical format for output conversion
len_unit = '[' + LEN_UNIT_STR + ']'
force_unit = '[' + FORCE_UNIT_STR + ']'            # Desired force output unit
stress_unit = '[' + stress_unit_str + ']'          # Desired stress output unit

len_quan = Quantity(1, LEN_UNIT_STR)         # Desired length output unit quantity
force_quan = Quantity(1, FORCE_UNIT_STR)           # Desired force output unit quantity
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


def remove_fields_with_zero_entities(fc):
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
    result_lbl_spc_len = len(result.Labels)
    # Get fields with more than zero entities
    for i in range(fc.FieldCount):
        if fc[i].ElementaryDataCount > 0:
            result.Add(fc[i],fc.GetLabelSpace(i))
    return result


##################### GET RESULTS FROM THE BASE STATIC STRUCTURAL ANALYSIS #########################

"""
##### Get the data source and mesh from the Static Structural Analysis
"""
ss_analysis = ExtAPI.DataModel.Project.Model.Analyses[STATIC_STR_ANALYSIS_NUM]
ss_res_file = ss_analysis.ResultFileName
data_source = dpf.DataSources()
data_source.SetResultFilePath(ss_res_file)
mesh_data = ss_analysis.MeshData
ss_model = dpf.Model(data_source)
mesh = ss_model.Mesh
bodies = ExtAPI.DataModel.Project.Model.GetChildren(DataModelObjectCategory.Body, True) # create list with all bodies in the Mechanical tree

"""
##### Static Structural time scoping
"""
ss_all_times = ss_model.TimeFreqSupport.TimeFreqs.Data
ss_time_unit_str = str(ss_model.TimeFreqSupport.TimeFreqs.Unit)               # Time stepping unit
ss_time_unit = '[' + ss_time_unit_str + ']'
ss_num_sets = ss_model.TimeFreqSupport.NumberSets               # Number of time steps
ss_time_ids = range(1, ss_num_sets + 1)                         # List of time steps
if STATIC_STR_LAST_TIME_ONLY.ToLower() == 'y':
    ss_time_ids = [ss_time_ids[len(ss_time_ids)-1]]             # Last time step
ss_active_times = [ss_all_times[t-1] for t in ss_time_ids]      # Solution times corresponding to available ss_time_ids
time_scoping = dpf.Scoping()
time_scoping.Ids = ss_time_ids
time_scoping.Location = 'Time'

"""
##### Create material fatigue properties dictionary if need to assess fatigue
"""
if ASSESS_FATIGUE.ToLower() == 'y':
    mats = {}
    mat_list = ExtAPI.DataModel.Project.Model.Materials.Children
    mat_names = [m.Name for m in mat_list]
    mat_eng_data = [m.GetEngineeringDataMaterial() for m in mat_list]
    mat_props = [materials.GetListMaterialProperties(ed) for ed in mat_eng_data]
    # Get the appropriate strength coefficients depending on type of fatigue line and convert units
    for n, ed, p in zip(mat_names, mat_eng_data, mat_props):
        mats[n] = {}
        if 'S-N Curve' in p:
            sn_crv = materials.GetMaterialPropertyByName(ed, "S-N Curve")
            mats[n]['S-N Curve'] = sn_crv
            alt_strs = sn_crv['Alternating Stress']
            mats[n]['str_units'] = alt_strs[0]
            if 'R-Ratio' in sn_crv:
                if -1 in sn_crv['R-Ratio']:
                    # Get the index of the last -1 in the R-Ratio list and call that the location of the endurance limit
                    index_r_rat_neg_1 = len(sn_crv['R-Ratio']) - 1 - sn_crv['R-Ratio'][::-1].index(-1)
                    mats[n]['S_e'] = alt_strs[index_r_rat_neg_1]
                else:
                    print('S-N curve with R-Ratio = -1 or Mean Stress = 0 needed for material: ' + n)
                    sys_exit()
            else:
                mats[n]['S_e'] = alt_strs[len(alt_strs)-1]      # if only one S-N curve is defined
            mats[n]['S_e'] = (mats[n]['S_e'] * Quantity(1, alt_strs[0]) / stress_quan).Value
        else:
            print('S-N Curve needed in Engineering Data defintion for material: ' + n)
            sys_exit()
        if FATIGUE_LINE_TYPE.ToLower() == 's' or FATIGUE_LINE_TYPE.ToLower() == 'asme':      # Soderberg or ASME elliptic
            if 'Tensile Yield Strength' in p:
                s_y = materials.GetMaterialPropertyByName(ed, "Tensile Yield Strength")
                mats[n]['S_y'] = (s_y['Tensile Yield Strength'][1] * Quantity(1, s_y['Tensile Yield Strength'][0]) / stress_quan).Value
            else:
                print('Tensile Yield Strength needed in Engineering Data defintion for material: ' + n)
                sys_exit()
        elif FATIGUE_LINE_TYPE.ToLower() == 'g' or FATIGUE_LINE_TYPE.ToLower() == 'ger':      # Modified Goodman or Gerber
            if 'Tensile Ultimate Strength' in p:
                s_ut = materials.GetMaterialPropertyByName(ed, "Tensile Ultimate Strength")
                mats[n]['S_ut'] = (s_ut['Tensile Ultimate Strength'][1] * Quantity(1, s_ut['Tensile Ultimate Strength'][0]) / stress_quan).Value
            else:
                print('Tensile Ultimate Strength needed in Engineering Data defintion for material: ' + n)
                sys_exit()
        else:
            print("Invalid fatigue line type selected.")
            sys_exit()

"""
##### Get all named selections that are grouped under the folder NAMED_SEL_FOLDER
"""
ns_group = get_named_sels_group_by_name(NAMED_SEL_FOLDER)
ns = [n for n in ns_group.Children]     # List of named selections
ns_names = [n.Name for n in ns]
ns_ids = [n.ObjectId for n in ns]
ns_entities = [n.Entities for n in ns]

"""
##### Create von Mises stress operator
"""
seqv_op = dpf.operators.result.stress_von_mises()
seqv_op.inputs.data_sources.Connect(data_source)
seqv_op.inputs.time_scoping.Connect(time_scoping)
seqv_op.inputs.requested_location.Connect('Nodal')
    
"""
##### Create unit conversion operators
"""
unit_conv_fc_op = dpf.operators.math.unit_convert_fc()
unit_conv_fc_op.inputs.unit_name.Connect(stress_unit_str)
unit_conv_field_op = dpf.operators.math.unit_convert()
unit_conv_field_op.inputs.unit_name.Connect(stress_unit_str)

"""
# Create data dictionary and static structural columns to be written to output csv file
"""
data = {}
cols = ['Named Selection',
        'Named Selection ID',
        'Node',
        'Stat Str Time ' + ss_time_unit,
        'Stat Str Set',
        'Mean Eqv Stress ' + stress_unit
        ]

cols_ss = cols[:]           # Copy the cols list for future use
for c in cols:
    data[c] = []

"""
For each named selection (NS):
1.  Obtain the nodes and elements in total for all bodies in the NS.
2.  Create a von Mises stress fields container for the static structural analysis, known as the mean stress.
3.  Depending on the need to assess fatigue, obtain the material for each node along with the necessary strength
    parameters, creating fields for each strength parameter.
4.  Collect mean stress for all nodes in the data dictionary for future writing to CSV file.
5.  For each RV/RS analysis system:
  5.1  Create a von Mises stress fields container called alternating stress.
  5.2  If fatigue assessment is desired, compute factor of safety in fatigue based on fatigue line type.
  5.3  If damage computation by Miner's rule is desired, compute it and add to data dictionary.
6.  Write a CSV file for each NS and RV/RS analysis system.   
For each named selection, get the element Ids, Node Ids, and store them in the data dictionary.
If fatigue is to be assessed, create Fields that contain fatigue parameters with nodal location. 
"""
res = {}
for n in ns:
    nid = n.ObjectId            # Named selection ID
    ns_name = n.Name            # Named selection Name
    res[nid] = {}

    """
    1. Get the mesh element and node Ids
    """
    elem_ids = []
    node_ids = []
    for nlocId in n.Location.Ids:
        sol_mesh = mesh_data.MeshRegionById(nlocId)
        elem_ids += sol_mesh.ElementIds
        node_ids += sol_mesh.NodeIds
    res[nid]['Elements'] = elem_ids
    res[nid]['Nodes'] = node_ids
    
    """
    2. Create a von Mises stress fields container for the static structural analysis, known as the mean stress.
    """
    # Scope the von Mises stress results to the element Ids
    mesh_scoping = dpf.Scoping()
    mesh_scoping.Ids = elem_ids
    mesh_scoping.Location = dpf.locations.elemental
    seqv_op.inputs.mesh_scoping.Connect(mesh_scoping)
    mean_stress_fc = seqv_op.outputs.fields_container
    mean_stress = mean_stress_fc.GetData()
    
    # Remove fields with 0 entities by creating a new fields container
    mean_stress_fc = remove_fields_with_zero_entities(mean_stress)

    # Convert the von Mises stress to desired stress units
    unit_conv_fc_op.inputs.fields_container.Connect(mean_stress_fc)
    mean_stress = unit_conv_fc_op.outputs.fields_container.GetData()

    """
    3.  Depending on the need to assess fatigue, obtain the material for each node along with the necessary strength
        parameters, creating fields for each strength parameter.
    """   
    if ASSESS_FATIGUE.ToLower() == 'y':
        nodes = mean_stress[0].ScopingIds
        S_e = dpf.FieldsFactory.CreateScalarField(numEntities=len(nodes), location='Nodal')
        S_e.Unit = stress_unit_str
        if FATIGUE_LINE_TYPE.ToLower() == 's' or FATIGUE_LINE_TYPE.ToLower() == 'asme':      # Soderberg or ASME elliptic
            S_y = dpf.FieldsFactory.CreateScalarField(numEntities=len(nodes), location='Nodal')
            S_y.Unit = stress_unit_str
        elif FATIGUE_LINE_TYPE.ToLower() == 'g' or FATIGUE_LINE_TYPE.ToLower() == 'ger':      # Modified Goodman or Gerber
            S_ut = dpf.FieldsFactory.CreateScalarField(numEntities=len(nodes), location='Nodal')
            S_ut.Unit = stress_unit_str
        else:
            pass
        # Loop through each node, get the material and then place strengths in fields
        for nd in nodes:
            my_node = mesh_data.NodeById(nd)
            body_id = my_node.BodyIds[0]
            body = ExtAPI.DataModel.GeoData.GeoEntityById(body_id)
            treebody=ExtAPI.DataModel.Project.Model.Geometry.GetBody(body)
            nid_mat = treebody.Material
            S_e.Add(nd, [mats[nid_mat]['S_e']])
            res[nid]['S_e field'] = S_e
            if FATIGUE_LINE_TYPE.ToLower() == 's' or FATIGUE_LINE_TYPE.ToLower() == 'asme':      # Soderberg or ASME elliptic
                S_y.Add(nd, [mats[nid_mat]['S_y']])
                res[nid]['S_y field'] = S_y
            elif FATIGUE_LINE_TYPE.ToLower() == 'g' or FATIGUE_LINE_TYPE.ToLower() == 'ger':      # Modified Goodman or Gerber
                S_ut.Add(nd, [mats[nid_mat]['S_ut']])
                res[nid]['S_ut field'] = S_ut
                
    """
    4.  Collect mean stress for all nodes in the data dictionary for future writing to CSV file.
    """
    res[nid]['scoping_ids'] = mean_stress[0].ScopingIds   # mesh_scoping should not change
    res[nid]['mean_stress_fc'] = {}
    for i, t in enumerate(ss_active_times):
        for nd in mean_stress[i].ScopingIds:
            res[nid]['mean_stress_fc'][t] = mean_stress[i]
            data[cols[0]].append(ns_name)
            data[cols[1]].append(nid)
            data[cols[2]].append(nd)
            data[cols[3]].append(t)
            data[cols[4]].append(time_scoping.Ids[i])
            data[cols[5]].append(mean_stress[i].GetEntityDataById(nd)[0])
    
    """
    5. For each named selection, obtain the alternating stress and write to CSV file for each RS/RV system.
    """
    if len(CHILD_ANALYSIS_NUMS) > 0:
        for a in CHILD_ANALYSIS_NUMS:
            cols = cols_ss[:]   # Reset the columns to those from the static structural analysis
            analysis = ExtAPI.DataModel.Project.Model.Analyses[a]
            solver_data = analysis.Solution.SolverData
            analysis_type = analysis.AnalysisType
            analysis_settings = analysis.AnalysisSettings
            analysis_name = analysis.Name
                   
            # Result Data
            file_path = analysis.ResultFileName
            
            # Data Source
            data_source = dpf.DataSources()
            data_source.SetResultFilePath(file_path)
            
            # Model and time scoping
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
            active_times = [all_times[t-1] for t in time_ids]       # Solution times corresponding to available ss_time_ids
            time_scoping.Ids = time_ids
            
            """
            5.1  Create a von Mises stress fields container called alternating stress.
            """
            # Create von Mises stress operator
            seqv_op.inputs.data_sources.Connect(data_source)
            seqv_op.inputs.time_scoping.Connect(time_scoping)
            
            # Get the (unscaled) alternating (equivalent) stress
            if str(analysis_type).ToLower() == 'responsespectrum':
                col_name = 'Alt Eqv Stress ' + stress_unit
            elif str(analysis_type).ToLower() == 'spectrum':
                col_name = '1-sigma Alt Eqv Stress ' + stress_unit
            cols.append(col_name)
            data[col_name] = []
            
            mesh_scoping = dpf.Scoping()
            mesh_scoping.Ids = elem_ids
            mesh_scoping.Location = dpf.locations.elemental
            seqv_op.inputs.mesh_scoping.Connect(mesh_scoping)
            alt_stress = seqv_op.outputs.fields_container.GetData()
            # Remove fields with 0 entities by creating a new fields container
            alt_stress_fc = remove_fields_with_zero_entities(alt_stress)
            # Convert the alternating stress to desired stress units
            unit_conv_fc_op.inputs.fields_container.Connect(alt_stress_fc)
            # Scale the alternating (von Mises) stress
            alt_stress_fc = unit_conv_fc_op.outputs.fields_container
            alt_stress = alt_stress_fc.GetData()
            for i, t in enumerate(ss_active_times):
                for nd in mean_stress[0].ScopingIds:
                    data[col_name].append(alt_stress[0].GetEntityDataById(nd)[0])
            
            """
            for n in ns:
                nid = n.ObjectId
                mesh_scoping = dpf.Scoping()
                mesh_scoping.Ids = res[nid]['Elements']
                mesh_scoping.Location = dpf.locations.elemental
                seqv_op.inputs.mesh_scoping.Connect(mesh_scoping)
                vm_stress = seqv_op.outputs.fields_container.GetData()
                # Remove fields with 0 entities by creating a new fields container
                vm_stress_fc = remove_fields_with_zero_entities(vm_stress)
                # Convert the von Mises stress to desired stress units
                unit_conv_fc_op.inputs.fields_container.Connect(vm_stress_fc)
                # Scale the von Mises stress
                vm_stress_fc = unit_conv_fc_op.outputs.fields_container
                vm_stress = vm_stress_fc.GetData()
                res[nid]['alt_stress_fc'] = vm_stress_fc
                # Add to data dictionary
                for i, t in enumerate(ss_active_times):
                    for nd in res[nid]['scoping_ids']:
                        data[col_name].append(vm_stress[0].GetEntityDataById(nd)[0])
            """
            
            # Create an alternating stress column for each scale factor if a RV analysis
            if str(analysis_type).ToLower() == 'spectrum':
                alt_stress_scld = []
                for k, sf in enumerate([2, 3]):
                    # Create scale operator
                    scale_op = dpf.operators.math.scale_fc()
                    if ANSYS_VER.ToUpper() == '2024 R2':
                        scale_op.inputs.ponderation.Connect(sf)   # 2024 R2
                    else:
                        scale_op.inputs.weights.Connect(sf)       # 2025 R2
                    
                    # Add column to output data dictionary
                    col_name = str(sf) + '-sigma Alt Eqv Stress ' + stress_unit
                    cols.append(col_name)
                    data[col_name] = []
                    
                    """
                    Get the von Mises stress at the corresponding node of the static structural analysis.  This is an 
                    "alternating stress" component of the analysis.
                    # Scale the von Mises stress
                    """
                    scale_op.inputs.fields_container.Connect(alt_stress_fc)
                    alt_stress_scld_fc = scale_op.outputs.fields_container
                    alt_stress_scld.append(alt_stress_scld_fc.GetData())
                    for i, t in enumerate(ss_active_times):
                        for nd in mean_stress[0].ScopingIds:
                            data[col_name].append(alt_stress_scld[k][0].GetEntityDataById(nd)[0])

            x = datetime.datetime.now()
                
            file_name_body = 'mean_alt_nodal_eqv_stress_summary--ns=' + ns_name + '--sys_name=' + analysis.Name + '--type=' + str(analysis_type) + '--' + x.strftime("%m-%d-%y")
            write_csv(user_dir + '/' + file_name_body + ".csv", data, cols)
                
            print("[INFO] Process completed for Mean-Alternating Eqv Stress results")
            print("Open File: " + chr(34) + user_dir + chr(92) + file_name_body + ".csv" + chr(34))
