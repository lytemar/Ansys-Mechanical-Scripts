"""
Calculate Stress Resultants for all beam connections using results from beam probes.
===================================================================================

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

#  Place units in Ansys Mechanical format for output conversion
lengthUnitStr = 'in'            # Desired length output unit
forceUnitStr = 'lbf'            # Desired force output unit
stressUnitStr = forceUnitStr + '*' + lengthUnitStr + '^-2'         # Desired stress output unit
momentUnitStr = forceUnitStr + '*' + lengthUnitStr                 # Desired moment/torque output unit

lengthUnit = '[' + lengthUnitStr + ']'
areaUnitStr = lengthUnitStr + '^2'              # Area Unit string
areaUnit = '[' + areaUnitStr + ']'             # Area Unit
inertiaUnitStr = lengthUnitStr + '^4'              # Inertia Unit string
inertiaUnit = '[' + inertiaUnitStr + ']'             # Inertia Unit
forceUnit = '[' + forceUnitStr + ']'
stressUnit = '[' + stressUnitStr + ']'          # Desired stress output unit
momentUnit = '[' + momentUnitStr + ']'          # Desired moment/torque output unit

### Define quantities for units obtained from elemental results
forceQuan = Quantity('1 [lbf]')
momentQuan = Quantity('1 [lbf in]')
stressQuan = Quantity('1 [psi]')

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


def computeEquivStress(combStrs, torStrs):
    """
    Function to compute the von Mises equivalent stress given the combined and torsional stresses
    
    Parameters
    ----------
    combStrs : stress Quantity
        Combined stress = direct stress plus bending stress
    torStrs : stress Quantity
        Torsional stress
    
    Returns
    von Mises stress Quantity
    """
    return (combStrs**2 + 3.0*torStrs**2)**(0.5)


for a in analysisNumbers:
    analysis = Model.Analyses[a]
    solver_data = analysis.Solution.SolverData
    
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
    #timeSteps = [t*Quantity('1 ' + timeUnit) for t in all_times]
    
    # Read mesh in results file
    mesh_op = dpf.operators.mesh.mesh_provider() 
    mesh_op.inputs.data_sources.Connect(dataSources)
    my_mesh = mesh_op.outputs.mesh.GetData()
    
    # Time scoping
    timeScoping = dpf.Scoping()
    timeScoping.Ids = timeIds
    timeScoping.Location = 'Time'
    
    # Get all beams and the element information
    beam_conns = DataModel.GetObjectsByType(DataModelObjectCategory.Beam)
    beamElemIds = [solver_data.GetObjectData(beam).ElementId for beam in beam_conns]
    
    # Create dictionary to store all data for each beam
    beam_dat = {}
    for conn, eid in zip(beam_conns, beamElemIds):
        beam_dat[eid] = {}
        beam_dat[eid]['Name'] = conn.Name
        beam_dat[eid]['rad'] = conn.Radius
        beam_dat[eid]['dia'] = 2.0*conn.Radius
        beam_dat[eid]['area'] = pi*conn.Radius**2
        beam_dat[eid]['I'] = pi*conn.Radius**4/4.0
        beam_dat[eid]['J'] = pi*conn.Radius**4/2.0
        beam_dat[eid]['times'] = all_times
        beam_dat[eid]['FX'] = []
        beam_dat[eid]['Bending Moment'] = []
        beam_dat[eid]['Torque'] = []
        beam_dat[eid]['Direct Stress'] = []
        beam_dat[eid]['Bending Stress'] = []
        beam_dat[eid]['Torsional Stress'] = []
        beam_dat[eid]['Equivalent Stress'] = []
        beam_dat[eid]['Combined Stress'] = []
        
    # Beam Element Scoping
    beamElem_scoping = dpf.Scoping()
    beamElem_scoping.Location = "Elemental"
    beamElem_scoping.Ids = beamElemIds
    
    analysis_settings = analysis.AnalysisSettings

    # Get Field data
    # item_index is the SMISC item ID found in BEAM188 documentation
    # FX = axial force, MY = Bending moment in Y-dir, MZ = Bending Moment in Z-dir, TQ = torque, SFz = Shear Force in Z-dir, SFy = Shear force in Y-dir
    # SDIR = direct stress from axial loading
    # SByT = Bending stress on top in Y-dir, SByB = Bending stress on bottom in Y-dir
    # SBzT = Bending stress on top in Z-dir, SBzB = Bending stress on bottom in Z-dir
    
    #force_fields_idx = {'FX_I': 1, 'FX_J': 14, 'SFz_I': 5, 'SFz_J': 18, 'SFy_I': 6, 'SFy_J': 19}
    force_fields_idx = {'FX_I': 1}
    moment_fields_idx = {'MY_I': 2, 'MY_J': 15, 'MZ_I': 3, 'MZ_J': 16, 'TQ_I': 4, 'TQ_J': 17}
    #moment_fields_idx = {'MY_I': 2, 'MY_J': 15, 'MZ_I': 3, 'MZ_J': 16}
    stress_fields_idx = {'SDIR_I': 31, 'SDIR_J': 36, 'SByT_I': 32, 'SByT_J': 37, 'SByB_I': 33, 'SByB_J': 38, 'SBzT_I': 34, 'SBzT_J': 39, 'SBzB_I': 35, 'SBzB_J': 40}
    
    force_fields = {}
    moment_fields = {}

    for k, v in force_fields_idx.items():
        force_fields[k] = dpf.operators.result.mapdl.smisc(time_scoping=timeScoping.Ids, mesh=my_mesh, data_sources=dataSources, item_index=v, mesh_scoping=beamElem_scoping).outputs.fields_container.GetData()
        # Unit conversion
        unitConvOp = dpf.operators.math.unit_convert_fc()
        unitConvOp.inputs.fields_container.Connect(force_fields[k])
        unitConvOp.inputs.unit_name.Connect(forceUnitStr)
        force_fields[k] = unitConvOp.outputs.fields_container.GetData()
    for k, v in moment_fields_idx.items():
        moment_fields[k] = dpf.operators.result.mapdl.smisc(time_scoping=timeScoping.Ids, mesh=my_mesh, data_sources=dataSources, item_index = v, mesh_scoping=beamElem_scoping).outputs.fields_container.GetData()

    # Place the axial forces and direct stresses into the data dictionary
    for t in range(len(timeScoping.Ids)):
        for i, eid in enumerate(force_fields['FX_I'][t].ScopingIds):
            f = force_fields['FX_I'][t].Data[i] * forceQuan
            beam_dat[eid]['FX'].append(f)
            s = f/beam_dat[eid]['area']
            beam_dat[eid]['Direct Stress'].append(s)
            
    # Compute the equivalent stress at I and J.  Record whichever result is larger in magnitude in the data dictionary.
    for t in range(len(timeScoping.Ids)):
        for i, eid in enumerate(moment_fields['MY_I'][t].ScopingIds):
            M_I = (moment_fields['MY_I'][t].Data[i]**2 + moment_fields['MZ_I'][t].Data[i]**2)**(0.5)*momentQuan
            M_J = (moment_fields['MY_J'][t].Data[i]**2 + moment_fields['MZ_J'][t].Data[i]**2)**(0.5)*momentQuan
            TQ_I = moment_fields['TQ_I'][t].Data[i]*momentQuan
            TQ_J = moment_fields['TQ_J'][t].Data[i]*momentQuan
            bendStr_I = M_I * beam_dat[eid]['rad'] / beam_dat[eid]['I']
            bendStr_J = M_J * beam_dat[eid]['rad'] / beam_dat[eid]['I']
            combStr_I = beam_dat[eid]['Direct Stress'][i] + bendStr_I
            combStr_J = beam_dat[eid]['Direct Stress'][i] + bendStr_J
            torStr_I = TQ_I * beam_dat[eid]['rad'] / beam_dat[eid]['J']
            torStr_J = TQ_J * beam_dat[eid]['rad'] / beam_dat[eid]['J']
            eqvStr_I = computeEquivStress(combStr_I, torStr_I)
            eqvStr_J = computeEquivStress(combStr_J, torStr_J)
            if abs(eqvStrs_I) >= abs(eqvStrs_J):
                beam_dat[eid]['Bending Moment'].append(M_I)
                beam_dat[eid]['Torque'].append(TQ_I)
                beam_dat[eid]['Bending Stress'].append(bendStr_I)
                beam_dat[eid]['Torsional Stress'].append(torStr_I)
                beam_dat[eid]['Equivalent Stress'].append(eqvStr_I)
                beam_dat[eid]['Combined Stress'].append(combStr_I)
            else:
                beam_dat[eid]['Bending Moment'].append(M_J)
                beam_dat[eid]['Torque'].append(TQ_J)
                beam_dat[eid]['Bending Stress'].append(bendStr_J)
                beam_dat[eid]['Torsional Stress'].append(torStr_J)
                beam_dat[eid]['Equivalent Stress'].append(eqvStr_J)
                beam_dat[eid]['Combined Stress'].append(combStr_J)
    
    # Create data dictionary to written to output csv file
    data = {}
    cols = ['Beam Connection Name',
            'Beam Element ID',
            'Radius ' + lengthUnit,
            'Cross-Sectional Area ' + areaUnit,
            'Moment of Inertia ' + inertiaUnit,
            'Polar Moment of Inertia ' + inertiaUnit,
            'Time ' + timeUnit,
            'Set',
            'Axial Force ' + forceUnit,
            'Torque ' + momentUnit,
            'Bending Moment ' + momentUnit,
            'Equivalent Stress ' + stressUnit,
            'Direct Stress ' + stressUnit,
            'Bending Stress ' + stressUnit,
            'Combined Stress ' + stressUnit,
            'Torsional Stress ' + stressUnit]
    
    for c in cols:
        data[c] = []

    for eid in sorted(beam_dat.keys()):
        for t in range(len(timeScoping.Ids)):
            data[cols[0]].append(beam_dat[eid]['Name'])
            data[cols[1]].append(eid)
            data[cols[2]].append(beam_dat[eid]['rad'] / Quantity('1 '+ lengthUnit))
            data[cols[3]].append(beam_dat[eid]['area'] / Quantity('1 '+ areaUnit))
            data[cols[4]].append(beam_dat[eid]['I'] / Quantity('1 ' + inertiaUnit))
            data[cols[5]].append(beam_dat[eid]['J'] / Quantity('1 ' + inertiaUnit))
            data[cols[6]].append(beam_dat[eid]['times'][t])
            data[cols[7]].append(t+1)
            data[cols[8]].append(beam_dat[eid]['FX'][t] / Quantity('1 ' + forceUnit))
            data[cols[9]].append(beam_dat[eid]['Torque'][t] / Quantity('1 ' + momentUnit))
            data[cols[10]].append(beam_dat[eid]['Bending Moment'][t] / Quantity('1 ' + momentUnit))
            data[cols[11]].append(beam_dat[eid]['Equivalent Stress'][t] / Quantity('1 ' + stressUnit))
            data[cols[12]].append(beam_dat[eid]['Direct Stress'][t] / Quantity('1 ' + stressUnit))
            data[cols[13]].append(beam_dat[eid]['Bending Stress'][t] / Quantity('1 ' + stressUnit))
            data[cols[14]].append(beam_dat[eid]['Combined Stress'][t] / Quantity('1 ' + stressUnit))
            data[cols[15]].append(beam_dat[eid]['Torsional Stress'][t] / Quantity('1 ' + stressUnit))
        

    x = datetime.datetime.now()
    
    file_name_body = analysis.Name + ' - Bolt_Results_' + x.strftime("%m") + "-" + x.strftime("%d") + "-" + x.strftime("%y")
    writeCSV(user_dir + '/' + file_name_body + ".csv", data, cols)
    
    print("[INFO] Process completed for " + analysis.Name)
    print("Open File: " + chr(34) + user_dir + chr(92) + file_name_body + ".csv" + chr(34) + '\n')