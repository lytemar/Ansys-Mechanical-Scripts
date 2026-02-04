"""
Retrieve Nodal Contact Pressure With Nodal Coordinates Over Time for a Contact.
====================================================================================================

This script outputs the node ID, nodal coordinates and contact pressure for a contact provided by name and writes the
data to a CSV file.
"""
################### Parameters ########################
analysis_numbers = [0]       # List of analysis systems to apply this script
static_struct_last_time_only = 'y'     # 'Y' = only output last time step for static structural, 'N' = output all time steps
contact_name = "Frictional - flange_1_mate To flange_2_mate"  # Contact name for pressure results
use_loc_csys = 'y'                # get nodal coordinates w.r.t. ('y' = loca coordinate system, 'n' = global coordinate system)
loc_csys_name = "Loc Csys"        # Name of local coordinate system for nodal coordinates
length_unit_str = 'm'            # DESIRED LENGTH OUTPUT UNIT (usually 'in' or 'mm', case sensitive)
force_unit_str = 'N'            # DESIRED FOURCE OUTPUT UNIT (usually 'lbf' or 'N', case sensitive)
################### End Parameters ########################

import wbjn
import datetime
import csv
import mech_dpf
import Ans.DataProcessing as dpf
cmd = 'returnValue(GetUserFilesDirectory())'
user_dir = wbjn.ExecuteCommand(ExtAPI, cmd)
mech_dpf.setExtAPI(ExtAPI)
ANSYS_VER = str(ExtAPI.DataModel.Project.ProductVersion)

if length_unit_str.ToLower() == 'in' and force_unit_str.ToLower() == 'lbf':
    stress_unit_str = 'psi'
elif length_unit_str.ToLower() == 'mm' and force_unit_str.ToUpper() == 'N':
    stress_unit_str = 'MPa'
else:
    stress_unit_str = force_unit_str + '*' + length_unit_str + '^-2'          # Desired stress output unit
    


#  Place units in Ansys Mechanical format for output conversion
length_unit = '[' + length_unit_str + ']'
stress_unit = '[' + stress_unit_str + ']'

# Desired unit quantities
length_quan = Quantity(1, length_unit_str)
stress_quan = Quantity(1, stress_unit_str)

# Active Length units
active_length_unit_str = DataModel.CurrentConsistentUnitFromQuantityName("Length")
active_length_quan = Quantity(1, active_length_unit_str)


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
        Column header names = 
    
    Returns
    -------
    None
    """
    with open(filename, 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(cols)
        writer.writerows(zip(*[data[col] for col in cols]))

# Get the directional vectors for the desired coordinate system
if use_loc_csys.ToLower() == 'y':
    res_csys = [csys for csys in Model.CoordinateSystems.Children if csys.Name.ToLower() == loc_csys_name.ToLower()]
    res_csys = res_csys[0]
    res_csys_xaxis = Vector3D(res_csys.PrimaryAxisDirection)
    res_csys_yaxis = Vector3D(res_csys.SecondaryAxisDirection)
    res_csys_zaxis = Vector3D(res_csys.ZAxis)
    conv_fac = active_length_quan/length_quan
    res_csys_origin = Vector3D(res_csys.Origin)*conv_fac.Value
    identity = Matrix4D()
    transformation = identity.CreateSystem(res_csys_xaxis, res_csys_yaxis, res_csys_zaxis)
    transformation.Transpose()


for a in analysis_numbers:
    analysis = Model.Analyses[a]
    solver_data = analysis.Solution.SolverData
    data_source = dpf.DataSources(analysis.ResultFileName)
    model = dpf.Model(data_source)
    whole_mesh = model.Mesh
    streams = mech_dpf.GetStreams(0)
    
    all_times = model.TimeFreqSupport.TimeFreqs.Data
    time_unit_str = str(model.TimeFreqSupport.TimeFreqs.Unit)               # Time stepping unit
    time_unit = '[' + time_unit_str + ']'
    number_sets = model.TimeFreqSupport.NumberSets      # Number of time steps
    time_ids = range(1, number_sets + 1)                 # List of time steps
    if static_struct_last_time_only.ToLower() == 'y':
        time_ids = [time_ids[len(time_ids)-1]]            # Last time step
    active_times = [all_times[t-1] for t in time_ids]       # Solution times corresponding to available time_ids
    
    # Time scoping
    time_scoping = dpf.Scoping()
    time_scoping.Ids = time_ids
    time_scoping.Location = 'Time'
    
    # List of contact objects by name
    cont_objs = ExtAPI.DataModel.GetObjectsByName(contact_name)
    
    # Create a results dictionary to store all results
    res = {}
    
    # identify Contact Elements from Contact Objects
    for c in cont_objs:
        cont_name = c.Name
        cont_data = solver_data.GetObjectData(c)
        mat_cont = cont_data.SourceId
        mat_targ = cont_data.TargetId
        
        scop_on_prop_op = dpf.operators.scoping.on_property()
        scop_on_prop_op.inputs.property_name.Connect("material")
        scop_on_prop_op.inputs.property_id.Connect(mat_cont)
        scop_on_prop_op.inputs.requested_location.Connect("Elemental")
        scop_on_prop_op.inputs.streams_container.Connect(streams)
        #scop_on_prop_op.inputs.data_sources.Connect(data_source)
        cont_obj_elements = scop_on_prop_op.outputs.mesh_scoping.GetData().Ids
        # Get the nodes for each contact element
        nodes = []
        [nodes.append(model.Mesh.ElementById(x).NodeIds) for x in cont_obj_elements]
        # Flatten the list of lists and remove duplicates
        cont_obj_nodes = sorted(set([item for sublist in nodes for item in sublist]))
        
        # This is known to be buggy
        #cont_obj_elements = solver_data.ElementIdsByMaterialId(mat_cont.ToString())
        #cont_obj_nodes = sorted(solver_data.NodeIdsByMaterialId(mat_cont.ToString()))
        
        mesh_scoping = dpf.Scoping()
        mesh_scoping.Location = dpf.locations.nodal
        mesh_scoping.Ids = cont_obj_nodes

        mesh_from_scoping = dpf.operators.mesh.from_scoping()
        mesh_from_scoping.inputs.scoping.Connect(mesh_scoping)
        mesh_from_scoping.inputs.mesh.Connect(whole_mesh)
        my_mesh = mesh_from_scoping.outputs.getmesh()
        
        # Create a contact pressure operator and resulting fields container
        cont_pres_op = dpf.operators.result.contact_pressure()
        cont_pres_op.inputs.data_sources.Connect(data_source)
        cont_pres_op.inputs.mesh_scoping.Connect(mesh_from_scoping)
        cont_pres_op.inputs.time_scoping.Connect(time_scoping)
        cont_pres_op.inputs.requested_location.Connect('Nodal')
        cont_pres_fc = cont_pres_op.outputs.fields_container
        
        # Convert the contact pressure to desired pressure units
        unit_conv_op = dpf.operators.math.unit_convert_fc()
        unit_conv_op.inputs.unit_name.Connect(stress_unit_str)
        unit_conv_op.inputs.fields_container.Connect(cont_pres_fc)
        cont_pres_fc = unit_conv_op.outputs.fields_container
        
        # Contact Pressure Fields Container Data
        contact_pressures = cont_pres_fc.GetData()
        cont_node_ids = sorted(contact_pressures[0].ScopingIds)
        
        # Nodal coordinates operator (about the global coordinate system)
        nd_coords_op = dpf.operators.mesh.node_coordinates()
        nd_unit_conv_op = dpf.operators.math.unit_convert()
        nd_unit_conv_op.inputs.unit_name.Connect(length_unit_str)
        nd_coords_op.inputs.mesh.Connect(my_mesh)
        node_coords = nd_coords_op.outputs.getcoordinates_as_field()
        nd_unit_conv_op.inputs.entity_to_convert.Connect(node_coords)
        node_coords = nd_unit_conv_op.outputs.getconverted_entity_as_field()

        # Add nodal coordinates to the results dictionary
        k = cont_data.SourceId
        res[k] = {}
        res[k]['Node_ID'] = []
        if use_loc_csys.ToLower() == 'y':
            res[k]['Csys'] = loc_csys_name
        else:
            res[k]['Csys'] = 'Global'
        res[k]['Node_X'] = []
        res[k]['Node_Y'] = []
        res[k]['Node_Z'] = []
        res[k]['Contact_Pressure'] = {}
        
        # Create Vector3D for nodal coordinates, transform them, and place transformed vectors in results dictionary 
        for n in cont_node_ids:
            res[k]['Node_ID'].append(n)
            x, y, z = node_coords.GetEntityDataById(n)
            vec = Vector3D(x, y, z)
            if use_loc_csys.ToLower() == 'y':
                vec = transformation.Transform(vec) - res_csys_origin
            res[k]['Node_X'].append(vec[0])
            res[k]['Node_Y'].append(vec[1])
            res[k]['Node_Z'].append(vec[2])
                
        # Loop through all requested times
        for i,t in enumerate(active_times):
            res[k]['Contact_Pressure'][t] = {}
            res[k]['Contact_Pressure'][t]['Pres'] = []
            for n in res[k]['Node_ID']:
                res[k]['Contact_Pressure'][t]['Pres'].append(contact_pressures[i].GetEntityDataById(n)[0])
                
        # Create data dictionary to written to output csv file
        for t in active_times:
            data = {}
            # Data column names
            cols = ['Node ID',
                    'Node X [' + length_unit + ']',
                    'Node Y [' + length_unit + ']',
                    'Node Z [' + length_unit + ']',
                    'Contact Pressure [' + stress_unit + ']']
            
            data[cols[0]] = res[k]['Node_ID']
            data[cols[1]] = res[k]['Node_X']
            data[cols[2]] = res[k]['Node_Y']
            data[cols[3]] = res[k]['Node_Z']
            data[cols[4]] = res[k]['Contact_Pressure'][t]['Pres']
    
            x = datetime.datetime.now()
        
            file_name_body = analysis.Name + '__' + cont_name.replace('\\','_') + ' - Cont_Pres_Time=' + str(t) + "_Csys=" + res[k]['Csys'] + "__" + x.strftime("%m") + "-" + x.strftime("%d") + "-" + x.strftime("%y")
            writeCSV(user_dir + '/' + file_name_body + ".csv", data, cols)
            
            print("[INFO] Process completed for " + analysis.Name)
            print("Open File: " + chr(34) + user_dir + chr(92) + file_name_body + ".csv" + chr(34) + '\n')
    
    streams.ReleaseHandles()

