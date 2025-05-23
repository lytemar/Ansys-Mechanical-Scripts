"""
Calculate Stress Resultants for all beam connections using results from results file.
=====================================================================================

"""

analysisNumbers = [0, 2]       # LIST OF ANALYSIS SYSTEMS TO APPLY THIS SCRIPT

######################### DESIRED OUTPUT UNITS ##################################
lengthUnitStr = 'in'            # DESIRED LENGTH OUTPUT UNIT (usually 'in' or 'mm')
forceUnitStr = 'lbf'            # DESIRED FOURCE OUTPUT UNIT (usually 'lbf' or 'N')
if lengthUnitStr.ToLower() == 'in' and forceUnitStr.ToLower() == 'lbf':
    stressUnitStr = 'psi'
elif lengthUnitStr.ToLower() == 'mm' and forceUnitStr.ToUpper() == 'N':
    stressUnitStr = 'MPa'
else:
    stressUnitStr = forceUnitStr + '*' + lengthUnitStr + '^-2'          # Desired stress output unit
momentUnitStr = forceUnitStr + '*' + lengthUnitStr                  # Desired moment/torque output unit
stiffnessUnitStr = forceUnitStr + '*' + lengthUnitStr + '^-1'       # Desired stiffness output unit
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

#  Place units in Ansys Mechanical format for output conversion
lengthUnitStr = 'in'            # Desired length output unit
forceUnitStr = 'lbf'            # Desired force output unit
if lengthUnitStr.ToLower() == 'in' and forceUnitStr.ToLower() == 'lbf':
    stressUnitStr = 'psi'
elif lengthUnitStr.ToLower() == 'mm' and forceUnitStr.ToUpper() == 'N':
    stressUnitStr = 'MPa'
else:
    stressUnitStr = forceUnitStr + '*' + lengthUnitStr + '^-2'          # Desired stress output unit
momentUnitStr = forceUnitStr + '*' + lengthUnitStr                  # Desired moment/torque output unit
stiffnessUnitStr = forceUnitStr + '*' + lengthUnitStr + '^-1'       # Desired stiffness output unit

lengthUnit = '[' + lengthUnitStr + ']'
areaUnitStr = lengthUnitStr + '^2'              # Area Unit string
areaUnit = '[' + areaUnitStr + ']'              # Area Unit
inertiaUnitStr = lengthUnitStr + '^4'           # Inertia Unit string
inertiaUnit = '[' + inertiaUnitStr + ']'        # Inertia Unit
forceUnit = '[' + forceUnitStr + ']'            # Desired force output unit
stressUnit = '[' + stressUnitStr + ']'          # Desired stress output unit
momentUnit = '[' + momentUnitStr + ']'          # Desired moment/torque output unit
stiffnessUnit = '[' + stiffnessUnitStr + ']'    # Desired stiffness output unit

lengthQuan = Quantity(1, lengthUnitStr)         # Desired length output unit quantity
areaQuan = Quantity(1, areaUnitStr)             # Desired area output unit quantity
stiffnessQuan = Quantity(1, stiffnessUnitStr)   # Desired stiffness output unit quantity
inertiaQuan = Quantity(1, inertiaUnitStr)       # Desired inertia output unit quantity
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
    if str(analysis_type).ToLower() == 'spectrum':
        timeIds = [2]
    elif str(analysis_type).ToLower() == 'responsespectrum':
        timeIds = [1]
    timeSets = model.TimeFreqSupport.TimeFreqs.ScopingIds  # List of time steps
    
    # Read mesh in results file
    mesh_op = dpf.operators.mesh.mesh_provider() 
    mesh_op.inputs.data_sources.Connect(dataSources)
    my_mesh = mesh_op.outputs.mesh.GetData()
    
    # Time scoping
    timeScoping = dpf.Scoping()
    timeScoping.Ids = timeIds
    timeScoping.Location = 'Time'
    
    # Get all materials and properties
    mats = {}
    matList = ExtAPI.DataModel.Project.Model.Materials.Children
    matNames = [m.Name for m in matList]
    matEDs = [m.GetEngineeringDataMaterial() for m in matList]
    matProps = [materials.GetListMaterialProperties(ed) for ed in matEDs]
    for n, ed, p in zip(matNames, matEDs, matProps):
        if 'Elasticity' in p:
            elasticity = materials.GetMaterialPropertyByName(ed, "Elasticity")
            if "Young's Modulus" in elasticity:
                mats[n] = {}
                mats[n]['ElasticModulus'] = elasticity["Young's Modulus"][1] * Quantity('1 ['+ elasticity["Young's Modulus"][0] + ']')

    # Get all beams and the element information
    beams = {}
    beam_conns = DataModel.GetObjectsByType(DataModelObjectCategory.Beam)
    beamElemIds = [solver_data.GetObjectData(beam).ElementId for beam in beam_conns]
    
    for b, eid in zip(beam_conns, beamElemIds):
        if eid != 0:
            beams[eid]={}
            beams[eid]['Name'] = b.Name
            beams[eid]['Conn ID'] = b.ObjectId
            xr = b.ReferenceXCoordinate
            yr = b.ReferenceYCoordinate
            zr = b.ReferenceZCoordinate
            xm = b.MobileXCoordinate
            ym = b.MobileYCoordinate
            zm = b.MobileZCoordinate
            l = ((xr-xm)**2 + (yr-ym)**2 + (zr-zm)**2)**(0.5)
            beams[eid]['len'] = l
            beams[eid]['Material'] = b.Material
            rad = b.Radius
            beams[eid]['rad'] = rad
            area = pi*rad**2
            beams[eid]['area'] = area
            beams[eid]['dia'] = 2.0*rad
            beams[eid]['I'] = pi*rad**4/4.0
            beams[eid]['J'] = pi*rad**4/2.0
            if b.Material in mats.keys():
                modulus = mats[b.Material]['ElasticModulus']
                stiffness = modulus*area/l
                beams[eid]['Stiffness'] = stiffness
            beams[eid]['times'] = all_times
            beams[eid]['FX'] = []
            beams[eid]['Shear Force'] = []
            beams[eid]['Bending Moment'] = []
            beams[eid]['Torque'] = []
            beams[eid]['Direct Stress'] = []
            beams[eid]['Bending Stress'] = []
            beams[eid]['Torsional Stress'] = []
            beams[eid]['Equivalent Stress'] = []
            beams[eid]['Combined Stress'] = []
    
    beamElemIds = [b for b in beamElemIds if b != 0]
    xRefCoords = [b.ReferenceXCoordinate for b in beam_conns]
    yRefCoords = [b.ReferenceYCoordinate for b in beam_conns]
    zRefCoords = [b.ReferenceZCoordinate for b in beam_conns]
    xMobCoords = [b.MobileXCoordinate for b in beam_conns]
    yMobCoords = [b.MobileYCoordinate for b in beam_conns]
    zMobCoords = [b.MobileZCoordinate for b in beam_conns]
    beamLengths = [((xr-xm)**2 + (yr-ym)**2 + (zr-zm)**2)**(0.5) for xr, yr ,zr, xm, ym, zm in zip(xRefCoords, yRefCoords, zRefCoords, xMobCoords, yMobCoords, zMobCoords)]
    beamMats = [b.Material for b in beam_conns]
    
    # Beam Element Scoping
    beamElem_scoping = dpf.Scoping()
    beamElem_scoping.Location = "Elemental"
    beamElem_scoping.Ids = beams.keys()
    
    analysis_settings = analysis.AnalysisSettings

    # Get Field data
    # item_index is the SMISC item ID found in BEAM188 documentation
    # FX = axial force, MY = Bending moment in Y-dir, MZ = Bending Moment in Z-dir, TQ = torque, SFz = Shear Force in Z-dir, SFy = Shear force in Y-dir
    # SDIR = direct stress from axial loading
    # SByT = Bending stress on top in Y-dir, SByB = Bending stress on bottom in Y-dir
    # SBzT = Bending stress on top in Z-dir, SBzB = Bending stress on bottom in Z-dir
    
    #force_fields_idx = {'FX_I': 1, 'FX_J': 14, 'SFz_I': 5, 'SFz_J': 18, 'SFy_I': 6, 'SFy_J': 19}
    force_fields_idx = {'FX_I': 1, 'SFz_I': 5, 'SFz_J': 18, 'SFy_I': 6, 'SFy_J': 19}
    moment_fields_idx = {'MY_I': 2, 'MY_J': 15, 'MZ_I': 3, 'MZ_J': 16, 'TQ_I': 4, 'TQ_J': 17}
    #moment_fields_idx = {'MY_I': 2, 'MY_J': 15, 'MZ_I': 3, 'MZ_J': 16}
    stress_fields_idx = {'SDIR_I': 31, 'SDIR_J': 36, 'SByT_I': 32, 'SByT_J': 37, 'SByB_I': 33, 'SByB_J': 38, 'SBzT_I': 34, 'SBzT_J': 39, 'SBzB_I': 35, 'SBzB_J': 40}
    
    force_fields = {}
    moment_fields = {}

    for k, v in force_fields_idx.items():
        force_fields[k] = dpf.operators.result.mapdl.smisc(time_scoping=timeScoping.Ids, mesh=my_mesh, data_sources=dataSources, item_index=v, mesh_scoping=beamElem_scoping).outputs.fields_container.GetData()
    for k, v in moment_fields_idx.items():
        moment_fields[k] = dpf.operators.result.mapdl.smisc(time_scoping=timeScoping.Ids, mesh=my_mesh, data_sources=dataSources, item_index = v, mesh_scoping=beamElem_scoping).outputs.fields_container.GetData()

    # Get the units from the fields containers
    solForceQuan = Quantity(1, force_fields['FX_I'][0].Unit)
    solMomentQuan = Quantity(1, moment_fields['MY_I'][0].Unit)
    
    # Place the axial forces and direct stresses into the data dictionary
    for t in range(len(timeScoping.Ids)):
        for i, eid in enumerate(force_fields['FX_I'][t].ScopingIds):
            f = force_fields['FX_I'][t].Data[i] * solForceQuan
            beams[eid]['FX'].append(f)
            SFz_I = force_fields['SFz_I'][t].Data[i]
            SFy_I = force_fields['SFy_I'][t].Data[i]
            SFz_J = force_fields['SFz_J'][t].Data[i]
            SFy_J = force_fields['SFy_J'][t].Data[i]
            SF_I = (SFz_I**2 + SFy_I**2)**(0.5)
            SF_J = (SFz_J**2 + SFy_J**2)**(0.5)
            if abs(SF_I) >= abs(SF_J):
                beams[eid]['Shear Force'].append(SF_I * solForceQuan)
            else:
                beams[eid]['Shear Force'].append(SF_J * solForceQuan)
            s = f/beams[eid]['area']
            beams[eid]['Direct Stress'].append(s)
            
    # Compute the equivalent stress at I and J.  Record whichever result is larger in magnitude in the data dictionary.
    for t in range(len(timeScoping.Ids)):
        for i, eid in enumerate(moment_fields['MY_I'][t].ScopingIds):
            M_I = (moment_fields['MY_I'][t].Data[i]**2 + moment_fields['MZ_I'][t].Data[i]**2)**(0.5)*solMomentQuan
            M_J = (moment_fields['MY_J'][t].Data[i]**2 + moment_fields['MZ_J'][t].Data[i]**2)**(0.5)*solMomentQuan
            TQ_I = moment_fields['TQ_I'][t].Data[i]*solMomentQuan
            TQ_J = moment_fields['TQ_J'][t].Data[i]*solMomentQuan
            bendStr_I = M_I * beams[eid]['rad'] / beams[eid]['I']
            bendStr_J = M_J * beams[eid]['rad'] / beams[eid]['I']
            combStr_I = beams[eid]['Direct Stress'][t] + bendStr_I
            combStr_J = beams[eid]['Direct Stress'][t] + bendStr_J
            torStr_I = TQ_I * beams[eid]['rad'] / beams[eid]['J']
            torStr_J = TQ_J * beams[eid]['rad'] / beams[eid]['J']
            eqvStr_I = computeEquivStress(combStr_I, torStr_I)
            eqvStr_J = computeEquivStress(combStr_J, torStr_J)
            if abs(eqvStr_I) >= abs(eqvStr_J):
                beams[eid]['Bending Moment'].append(M_I)
                beams[eid]['Torque'].append(TQ_I)
                beams[eid]['Bending Stress'].append(bendStr_I)
                beams[eid]['Torsional Stress'].append(torStr_I)
                beams[eid]['Equivalent Stress'].append(eqvStr_I)
                beams[eid]['Combined Stress'].append(combStr_I)
            else:
                beams[eid]['Bending Moment'].append(M_J)
                beams[eid]['Torque'].append(TQ_J)
                beams[eid]['Bending Stress'].append(bendStr_J)
                beams[eid]['Torsional Stress'].append(torStr_J)
                beams[eid]['Equivalent Stress'].append(eqvStr_J)
                beams[eid]['Combined Stress'].append(combStr_J)
    
    # Create data dictionary to written to output csv file
    data = {}
    cols = ['Beam Connection Name',
            'Beam Element ID',
            'Beam Connection ID',
            'Material',
            'Diameter ' + lengthUnit,
            'Length ' + lengthUnit,
            'Cross-Sectional Area ' + areaUnit,
            'Moment of Inertia ' + inertiaUnit,
            'Polar Moment of Inertia ' + inertiaUnit,
            'Stiffness ' + stiffnessUnit,
            'Time ' + timeUnit,
            'Set',
            'Axial Force ' + forceUnit,
            'Shear Force ' + forceUnit,
            'Torque ' + momentUnit,
            'Bending Moment ' + momentUnit,
            'Equivalent Stress ' + stressUnit,
            'Direct Stress ' + stressUnit,
            'Bending Stress ' + stressUnit,
            'Combined Stress ' + stressUnit,
            'Torsional Stress ' + stressUnit]
    
    for c in cols:
        data[c] = []

    for eid in sorted(beams.keys()):
        for t in range(len(timeScoping.Ids)):
            data[cols[0]].append(beams[eid]['Name'])
            data[cols[1]].append(eid)
            data[cols[2]].append(beams[eid]['Conn ID'])
            data[cols[3]].append(beams[eid]['Material'])
            data[cols[4]].append(beams[eid]['dia'] / lengthQuan)
            data[cols[5]].append(beams[eid]['len'] / lengthQuan)
            data[cols[6]].append(beams[eid]['area'] / areaQuan)
            data[cols[7]].append(beams[eid]['I'] / inertiaQuan)
            data[cols[8]].append(beams[eid]['J'] / inertiaQuan)
            if beams[eid]['Material'] in mats.keys():
                data[cols[9]].append(beams[eid]['Stiffness'] / stiffnessQuan)
            else:
                data[cols[9]].append(0)
            data[cols[10]].append(beams[eid]['times'][t])
            if str(analysis_type).ToLower().Contains('spectrum'): 
                data[cols[11]].append(timeIds[0])
            else:
                data[cols[11]].append(t+1)
            data[cols[12]].append(beams[eid]['FX'][t] / forceQuan)
            data[cols[13]].append(beams[eid]['Shear Force'][t] / forceQuan)
            data[cols[14]].append(beams[eid]['Torque'][t] / momentQuan)
            data[cols[15]].append(beams[eid]['Bending Moment'][t] / momentQuan)
            data[cols[16]].append(beams[eid]['Equivalent Stress'][t] / stressQuan)
            data[cols[17]].append(beams[eid]['Direct Stress'][t] / stressQuan)
            data[cols[18]].append(beams[eid]['Bending Stress'][t] / stressQuan)
            data[cols[19]].append(beams[eid]['Combined Stress'][t] / stressQuan)
            data[cols[20]].append(beams[eid]['Torsional Stress'][t] / stressQuan)
        

    x = datetime.datetime.now()
    
    file_name_body = analysis.Name + ' - type=' + str(analysis_type) + ' - Bolt_Results_' + x.strftime("%m") + "-" + x.strftime("%d") + "-" + x.strftime("%y")
    writeCSV(user_dir + '/' + file_name_body + ".csv", data, cols)
    
    print("[INFO] Process completed for " + analysis.Name)
    print("Open File: " + chr(34) + user_dir + chr(92) + file_name_body + ".csv" + chr(34) + '\n')