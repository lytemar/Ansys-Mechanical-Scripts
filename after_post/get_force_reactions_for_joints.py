"""
Get all force and moment reactions for joints using results from results file.
==============================================================================

This has been tested on  2025 R1.

"""

def after_post(this, solution):# Do not edit this line
    """
    Called after post processing.
    Keyword Arguments : 
        this -- the datamodel object instance of the python code object you are currently editing in the tree
        solution -- Solution
    """


    # To access properties created using the Property Provider, please use the following command.
    # this.GetCustomPropertyByPath("your_property_group_name/your_property_name")

    # To access scoping properties use the following to access geometry scoping and named selection respectively:
    # this.GetCustomPropertyByPath("your_property_group_name/your_property_name/Geometry Selection")
    # this.GetCustomPropertyByPath("your_property_group_name/your_property_name/Named Selection")

    ######################### DESIRED OUTPUT UNITS ##################################
    lengthUnitStr = 'in'            # DESIRED LENGTH OUTPUT UNIT (usually 'in' or 'mm')
    forceUnitStr = 'lbf'            # DESIRED FOURCE OUTPUT UNIT (usually 'lbf' or 'N')
    momentUnitStr = forceUnitStr + '*' + lengthUnitStr                  # Desired moment/torque output unit
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
    analysis = solution.Parent
    solver_data = solution.SolverData
    analysis_type = analysis.AnalysisType
    analysis_settings = analysis.AnalysisSettings
    
    # Data Sources
    filepath = analysis.ResultFileName
    dataSource = dpf.DataSources(filepath)
    model = dpf.Model(dataSource)

    #  Place units in Ansys Mechanical format for output conversion
    lengthUnit = '[' + lengthUnitStr + ']'
    forceUnit = '[' + forceUnitStr + ']'            # Desired force output unit
    momentUnit = '[' + momentUnitStr + ']'          # Desired moment/torque output unit

    lengthQuan = Quantity(1, lengthUnitStr)         # Desired length output unit quantity
    forceQuan = Quantity(1, forceUnitStr)           # Desired force output unit quantity
    momentQuan = Quantity(1, momentUnitStr)         # Desired moment output unit quantity

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

 
    # Current solver units of interest and quantities
    solLenUnitStr = analysis.CurrentConsistentUnitFromQuantityName("Length")
    solForceUnitStr = analysis.CurrentConsistentUnitFromQuantityName("Force")
    solMomentUnitStr = analysis.CurrentConsistentUnitFromQuantityName("Moment")
    solLenQuan = Quantity(1, solLenUnitStr)
    solForceQuan = Quantity(1, solForceUnitStr)
    solMomentQuan = Quantity(1, solMomentUnitStr)
    
    # 2024 R2, force in lbf, moment in lbf*in if type is random vibration
    if str(analysis_type).ToLower() == 'spectrum':
        solForceUnitStr = 'N'
        solMomentUnitStr = 'N*mm'
        solForceQuan = Quantity(1, solForceUnitStr)
        solMomentQuan = Quantity(1, solMomentUnitStr)
    elif str(analysis_type).ToLower() == 'responsespectrum':
        solForceUnitStr = 'N'
        solMomentUnitStr = 'N*mm'
        solForceQuan = Quantity(1, solForceUnitStr)
        solMomentQuan = Quantity(1, solMomentUnitStr)
    
       
    # Time sets
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
    mesh_op.inputs.data_sources.Connect(dataSource)
    my_mesh = mesh_op.outputs.mesh.GetData()
    
    # Time scoping
    timeScoping = dpf.Scoping()
    timeScoping.Ids = timeIds
    timeScoping.Location = 'Time'
    
    # Get all joints and the element information
    joints = {}
    joint_conns = DataModel.GetObjectsByType(DataModelObjectCategory.Joint)
    jointElemIds = [solver_data.GetObjectData(joint).ElementId for joint in joint_conns]
    jointNames = [j.Name for j in joint_conns]
    jointTypes = [j.Type for j in joint_conns]
    
    for j, eid in zip(joint_conns, jointElemIds):
        if eid != 0:
            joints[eid]={}
            joints[eid]['Name'] = j.Name
            joints[eid]['TranslationX'] = j.TranslationX
            joints[eid]['TranslationY'] = j.TranslationY
            joints[eid]['TranslationZ'] = j.TranslationZ
            joints[eid]['Rotations'] = j.Rotations
            joints[eid]['Conn ID'] = j.ObjectId
            joints[eid]['Type'] = j.Type
            joints[eid]['times'] = all_times
            joints[eid]['FX'] = []
            joints[eid]['FY'] = []
            joints[eid]['FZ'] = []
            joints[eid]['MX'] = []
            joints[eid]['MY'] = []
            joints[eid]['MZ'] = []
    
    jointElemIds = [j for j in jointElemIds if j != 0]
    
    # Joint Element Scoping
    jointElem_scoping = dpf.Scoping()
    jointElem_scoping.Location = "Elemental"
    jointElem_scoping.Ids = joints.keys()
    
    # Get Field data
    # item_index is the SMISC item ID found in MPC184 documentation
    # FX = axial force in X-dir, FY = axial force in Y-dir, FZ = axial force in Z-dir 
    # MX = Bending moment in X-dir, MY = Bending moment in Y-dir, MZ = Bending Moment in Z-dir
    
    force_fields_idx = {'FX': 1, 'FY': 2, 'FZ': 3, 'JEF1': 43, 'JEF2': 44, 'JEF3': 45}
    moment_fields_idx = {'MX': 4, 'MY': 5, 'MZ': 6, 'JEF4': 46, 'JEF5': 47, 'JEF6': 48}
    
    force_fields = {}
    moment_fields = {}

    # Create force and moment operator
    smiscOp = dpf.operators.result.smisc()
    smiscOp.inputs.data_sources.Connect(dataSource)
    smiscOp.inputs.time_scoping.Connect(timeScoping)
    smiscOp.inputs.mesh_scoping.Connect(jointElem_scoping)

    for k, v in force_fields_idx.items():
        smiscOp.inputs.item_index.Connect(v)
        force_fields[k] = smiscOp.outputs.fields_container.GetData()
    for k, v in moment_fields_idx.items():
        smiscOp.inputs.item_index.Connect(v)
        moment_fields[k] = smiscOp.outputs.fields_container.GetData()

    # Place the axial force and moment reactions into the data dictionary.
    # Take negative value from SMISC output to get correct reaction force direction.
    for t in range(len(timeScoping.Ids)):
        for i, eid in enumerate(force_fields['FX'][t].ScopingIds):
            if joints[eid]['TranslationX'] == Ansys.Mechanical.DataModel.Enums.FixedOrFree.Free:
                joints[eid]['FX'].append(-force_fields['JEF1'][t].Data[i] * solForceQuan)
            else:
                joints[eid]['FX'].append(-force_fields['FX'][t].Data[i] * solForceQuan)
            if joints[eid]['TranslationY'] == Ansys.Mechanical.DataModel.Enums.FixedOrFree.Free:
                joints[eid]['FY'].append(-force_fields['JEF2'][t].Data[i] * solForceQuan)
            else:
                joints[eid]['FY'].append(-force_fields['FY'][t].Data[i] * solForceQuan)
            if joints[eid]['TranslationZ'] == Ansys.Mechanical.DataModel.Enums.FixedOrFree.Free:
                joints[eid]['FZ'].append(-force_fields['JEF3'][t].Data[i] * solForceQuan)
            else:
                joints[eid]['FZ'].append(-force_fields['FZ'][t].Data[i] * solForceQuan)
            if joints[eid]['Rotations'] == Ansys.Mechanical.DataModel.Enums.JointRotationDOFType.FreeAll:
                joints[eid]['MX'].append(-moment_fields['JEF4'][t].Data[i] * solMomentQuan)
                joints[eid]['MY'].append(-moment_fields['JEF5'][t].Data[i] * solMomentQuan)
                joints[eid]['MZ'].append(-moment_fields['JEF6'][t].Data[i] * solMomentQuan)
            elif joints[eid]['Rotations'] == Ansys.Mechanical.DataModel.Enums.JointRotationDOFType.FreeX:
                joints[eid]['MX'].append(-moment_fields['JEF4'][t].Data[i] * solMomentQuan)
                joints[eid]['MY'].append(-moment_fields['MY'][t].Data[i] * solMomentQuan)
                joints[eid]['MZ'].append(-moment_fields['MZ'][t].Data[i] * solMomentQuan)
            elif joints[eid]['Rotations'] == Ansys.Mechanical.DataModel.Enums.JointRotationDOFType.FreeY:
                joints[eid]['MY'].append(-moment_fields['JEF5'][t].Data[i] * solMomentQuan)
                joints[eid]['MX'].append(-moment_fields['MX'][t].Data[i] * solMomentQuan)
                joints[eid]['MZ'].append(-moment_fields['MZ'][t].Data[i] * solMomentQuan)
            elif joints[eid]['Rotations'] == Ansys.Mechanical.DataModel.Enums.JointRotationDOFType.FreeZ:
                joints[eid]['MZ'].append(-moment_fields['JEF6'][t].Data[i] * solMomentQuan)
                joints[eid]['MX'].append(-moment_fields['MX'][t].Data[i] * solMomentQuan)
                joints[eid]['MY'].append(-moment_fields['MY'][t].Data[i] * solMomentQuan)
            else:
                joints[eid]['MX'].append(-moment_fields['MX'][t].Data[i] * solMomentQuan)
                joints[eid]['MY'].append(-moment_fields['MY'][t].Data[i] * solMomentQuan)
                joints[eid]['MZ'].append(-moment_fields['MZ'][t].Data[i] * solMomentQuan)
            
    # Create data dictionary to written to output csv file
    data = {}
    cols = ['Joint Connection Name',
            'Joint Type',
            'Joint Element ID',
            'Joint Connection ID',
            'Time ' + timeUnit,
            'Set',
            'FX ' + forceUnit,
            'FY ' + forceUnit,
            'FZ ' + forceUnit,
            'MX ' + momentUnit,
            'MY ' + momentUnit,
            'MZ ' + momentUnit]
    
    for c in cols:
        data[c] = []

    for eid in sorted(joints.keys()):
        for t in range(len(timeScoping.Ids)):
            data[cols[0]].append(joints[eid]['Name'])
            data[cols[1]].append(joints[eid]['Type'])
            data[cols[2]].append(eid)
            data[cols[3]].append(joints[eid]['Conn ID'])
            data[cols[4]].append(joints[eid]['times'][t])
            if str(analysis_type).ToLower().Contains('spectrum'): 
                data[cols[5]].append(timeIds[0])
            else:
                data[cols[5]].append(t+1)
            data[cols[6]].append(joints[eid]['FX'][t] / forceQuan)
            data[cols[7]].append(joints[eid]['FY'][t] / forceQuan)
            data[cols[8]].append(joints[eid]['FZ'][t] / forceQuan)
            data[cols[9]].append(joints[eid]['MX'][t] / momentQuan)
            data[cols[10]].append(joints[eid]['MY'][t] / momentQuan)
            data[cols[11]].append(joints[eid]['MZ'][t] / momentQuan)
      

    x = datetime.datetime.now()
    
    file_name_body = analysis.Name + ' - type=' + str(analysis_type) + ' - Joint_Reactions_' + x.strftime("%m") + "-" + x.strftime("%d") + "-" + x.strftime("%y")
    writeCSV(user_dir + '/' + file_name_body + ".csv", data, cols)
