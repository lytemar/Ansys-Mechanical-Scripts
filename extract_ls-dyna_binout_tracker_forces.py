"""
Extract LS-DYNA Binout Tracker Forces from Solution Information and Compute the Components w.r.t. A Local CSYS.
===============================================================================================================

This has been tested on 2025 R2.



"""

analysisNumbers = [0]       # LIST OF ANALYSIS SYSTEMS TO APPLY THIS SCRIPT
COORD_SYS_NAME = 'Coordinate System'    # Name of the (Cartesian) coordinate system about which to resolve the forces
RESULTS_FOLDER = 'Directional Deformations'  # Name of results TreeGrouping Folder

######################### DESIRED OUTPUT UNITS ##################################
lengthUnitStr = 'in'            # DESIRED LENGTH OUTPUT UNIT (usually 'in' or 'mm')
forceUnitStr = 'lbf'            # DESIRED FOURCE OUTPUT UNIT (usually 'lbf' or 'N')
if lengthUnitStr.ToLower() == 'in' and forceUnitStr.ToLower() == 'lbf':
    stressUnitStr = 'psi'
elif lengthUnitStr.ToLower() == 'mm' and forceUnitStr.ToUpper() == 'N':
    stressUnitStr = 'MPa'
else:
    stressUnitStr = forceUnitStr + '*' + lengthUnitStr + '^-2'          # Desired stress output unit
stiffnessUnitStr = forceUnitStr + '*' + lengthUnitStr + '^-1'           # Desired stiffness output unit
#################################################################################


import wbjn
import datetime
import csv
import mech_dpf
import Ans.DataProcessing as dpf
import materials
import math
cmd = 'returnValue(GetUserFilesDirectory())'
user_dir = wbjn.ExecuteCommand(ExtAPI, cmd)
mech_dpf.setExtAPI(ExtAPI)

#  Place units in Ansys Mechanical format for output conversion
lengthUnit = '[' + lengthUnitStr + ']'
forceUnit = '[' + forceUnitStr + ']'            # Desired force output unit

lengthQuan = Quantity(1, lengthUnitStr)         # Desired length output unit quantity
forceQuan = Quantity(1, forceUnitStr)           # Desired force output unit quantity


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
    

def getResultsGroupByName(name, type):
    """
    Get the Equivalent Stress grouping folder by name
    
    Parameters
    ----------
    name : str
        Name of the Stress Results grouping folder
    type : Ansys.ACT.Automation.Mechanical.Model type
    
    Returns
    -------
    Ansys.ACT.Automation.Mechanical.TreeGroupingFolder
    """
    groups = findTreeGroupingFolders(type)
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


def getTableData(t0, colNum):
    t0.Activate()
    tempTable = []
    paneTabular=ExtAPI.UserInterface.GetPane(MechanicalPanelEnum.TabularData)
    control = paneTabular.ControlUnknown
    for row in range(1,control.RowsCount+1):
        tempRow = []
        for col in range(colNum,colNum+1):
            cellText= control.cell(row ,col ).Text
            tempRow.append(cellText)
        tempTable.append(tempRow)
    return tempTable


def reduce_data_by_lin_interp(ref_times, sig_times, sig_vals):
    """
    Function to reduce the number of points in a signal and align with a reference time series
    using linear interpolation.
    
    Parameters
    ----------
    ref_times : list of float
        Reference signal times to which to align the signal
    sig_times : list of float
        Signal times
    sig_vals : list of float
        Signal values that correspond to sig_times
    
    Returns
    -------
    List of reduced sig_vals
    """
    # Loop through the ref times.  At each ref time, linearly interpolate the signal at values
    # near it and then compute the value at the current reference time.
    new_sig_times = sig_times
    new_sig_vals = sig_vals
    interp_sig_vals = []        # initialize the result list
    N = len(ref_times)          # number of reference times
    
    for i, t in enumerate(ref_times):
        for j, st in enumerate(new_sig_times):
            if st == t:
                interp_sig_vals.append(new_sig_vals[j])
                new_sig_times = new_sig_times[j:]
                new_sig_vals = new_sig_vals[j:]
                break
            elif st > t:
                t1 = new_sig_times[j-1]
                t2 = st
                y1 = new_sig_vals[j-1]
                y2 = new_sig_vals[j]
                m = (y2-y1)/(t2-t1)
                interp_sig_vals.append(y1 + m*(t-t1))
                new_sig_times = new_sig_times[j:]
                new_sig_vals = new_sig_vals[j:]
                break
            elif i == N:
                if j == len(new_sig_times[-1]):
                    interp_sig_vals.append(new_sig_vals[-1])
    return interp_sig_vals
    

# Get the directional vectors for the desired coordinate system
res_csys = [csys for csys in Model.CoordinateSystems.Children if csys.Name.ToLower() == COORD_SYS_NAME.ToLower()]
res_csys = res_csys[0]
res_csys_xaxis = Vector3D(res_csys.PrimaryAxisDirection)
res_csys_yaxis = Vector3D(res_csys.SecondaryAxisDirection)
res_csys_zaxis = Vector3D(res_csys.ZAxis)
identity = Matrix4D()
transformation = identity.CreateSystem(res_csys_xaxis, res_csys_yaxis, res_csys_zaxis)
transformation.Transpose()

# Loop through the analyses
for a in analysisNumbers:
    analysis = Model.Analyses[a]
    charts = DataModel.GetObjectsByType(DataModelObjectCategory.Chart)
    
    # Get the current units
    cur_force_unit = ExtAPI.DataModel.CurrentUnitFromQuantityName("Force")
    cur_time_unit = ExtAPI.DataModel.CurrentUnitFromQuantityName("Time")
    cur_length_unit = ExtAPI.DataModel.CurrentUnitFromQuantityName("Length")
    cur_force_quan = Quantity(1, cur_force_unit)
    cur_time_quan = Quantity(1, cur_time_unit)
    cur_length_quan = Quantity(1, cur_length_unit)
    
    # Force conversion
    force_conv = cur_force_quan/forceQuan
    force_conv = force_conv.Value
    len_conv = cur_length_quan/lengthQuan
    len_conv = len_conv.Value
    
    # Get the Binout trackers from the Solution Information branch
    sol_info_children = analysis.Solution.SolutionInformation.Children
    trkrs = [c for c in sol_info_children if c.GetType() == Ansys.ACT.Automation.Mechanical.Results.ResultTrackers.LSDYNAGeneralTracker]
    trkrs = [t for t in trkrs if t.LSDYNABranchName == 'bndout']
    trkrs = [t for t in trkrs if t.LSDYNASubBranchName == 'velocity/nodes']
    trkr_filters = [t.FilterType for t in trkrs]
    trkr_comps = [t.LSDYNAComponentName for t in trkrs]
    
    # Create a dictionary to store all results
    res={}
    
    # Add directional deformation results to results dictionary.
    # Scope to the desired coordinate system.
    dir_def_group = getResultsGroupByName(RESULTS_FOLDER, analysis.Solution)
    dir_def_children = [r for r in dir_def_group.Children]
    for d in dir_def_children:
        d.CoordinateSystem = res_csys
    [d.EvaluateAllResults() for d in dir_def_children]
    
    for d in dir_def_children:
        d.Activate()
        direction = str(d.NormalOrientation)
        res[direction] = {}
        timeCol = [a[0] for a in getTableData(d,2)]
        res[direction]['Time'] = [float(t) for t in timeCol[1:-1]]
        resAvg =[a[0] for a in getTableData(d,5)]
        res[direction]['Deformation'] = [float(z)*len_conv for z in resAvg[1:-1]]
        res[direction]['DeformationUnit'] = lengthUnit
    ref_times = [float(t) for t in timeCol[1:-1]]
    
    # Populate tracker results
    # Sample the force binout vectors at the same times as the directional deformation outputs
    # Linear interpolation would be best but not implemented here
    for trk in trkrs:
        trk.Activate()
        cname = trk.LSDYNAComponentName + ' global csys'   # one of 'x_force', 'y_force' or 'z_force'
        res[cname] = {}
        timeCol = [a[0] for a in getTableData(trk, 2)]
        sig_times = [float(t) for t in timeCol[1:]]
        res[cname]['Time'] = ref_times
        res[cname]['TimeUnit'] = '[' + cur_time_unit + ']'
        if trk.FilterType == Ansys.Mechanical.DataModel.Enums.FilterType.None:
            force = [a[0] for a in getTableData(trk, 3)]
        else:
            force = [a[0] for a in getTableData(trk, 4)]
        sig_vals = [float(f)*force_conv for f in force[1:]]
        res[cname]['Force'] = reduce_data_by_lin_interp(ref_times, sig_times, sig_vals)
        res[cname]['ForceUnit'] = forceUnit
    

        
    # Create Vector3D's for the force components, transform them, and then place transformed vectors into the results dictionary
    vec3Ds = []
    res['x_force local csys'] = []
    res['y_force local csys'] = []
    res['z_force local csys'] = []
    res['Force Magnitude'] = []
    for (x,y,z) in zip(res['x_force global csys']['Force'], res['y_force global csys']['Force'], res['z_force global csys']['Force']):
        vec = Vector3D(x, y, z)
        res['Force Magnitude'].append(vec.Magnitude)
        vec3Ds.append(transformation.Transform(vec))
    for v in vec3Ds:
        res['x_force local csys'].append(v[0])
        res['y_force local csys'].append(v[1])
        res['z_force local csys'].append(v[2])

    # Create data dictionary to written to output csv file
    data = {}
    cols = ['Time ['+ cur_time_unit + ']',
            'Fx (global csys) ' + forceUnit,
            'Fy (global csys) ' + forceUnit,
            'Fz (global csys) ' + forceUnit,
            'Fx (local csys) ' + forceUnit,
            'Fy (local csys) ' + forceUnit,
            'Fz (local csys) ' + forceUnit,
            'Force Magnitude ' + forceUnit,
            'X-Dir Deform (local csys) ' + lengthUnit,
            'Y-Dir Deform (local csys) ' + lengthUnit,
            'Z-Dir Deform (local csys) ' + lengthUnit]
    
    for c in cols:
        data[c] = []

    res_keys = sorted(res.keys())
    data[cols[0]] = ref_times
    data[cols[1]] = res['x_force global csys']['Force']
    data[cols[2]] = res['y_force global csys']['Force']
    data[cols[3]] = res['z_force global csys']['Force']
    data[cols[4]] = res['x_force local csys']
    data[cols[5]] = res['y_force local csys']
    data[cols[6]] = res['z_force local csys']
    data[cols[7]] = res['Force Magnitude']
    data[cols[8]] = res['XAxis']['Deformation']
    data[cols[9]] = res['YAxis']['Deformation']
    data[cols[10]] = res['ZAxis']['Deformation']
    
    x = datetime.datetime.now()
    
    file_name_body = analysis.Name + ' - Force_Reactions_' + x.strftime("%m") + "-" + x.strftime("%d") + "-" + x.strftime("%y")
    writeCSV(user_dir + '/' + file_name_body + ".csv", data, cols)
    
    print("[INFO] Process completed for " + analysis.Name)
    print("Open File: " + chr(34) + user_dir + chr(92) + file_name_body + ".csv" + chr(34))
    #print("Analysis Type: " + str(analysis_type)  + '\n')
    
