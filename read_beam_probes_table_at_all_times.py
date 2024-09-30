"""
Read and Write-Out Beam Probe Results Object Table at all analysis times for items in TreeGrouping Folder.
=================================================================================================================

This script reads the Tabular Data for each beam probe result object and writes the data to a CSV file.

"""
import wbjn
import datetime
import csv
import mech_dpf
import materials
import Ans.DataProcessing as dpf
cmd = 'returnValue(GetUserFilesDirectory())'
user_dir = wbjn.ExecuteCommand(ExtAPI, cmd)
mech_dpf.setExtAPI(ExtAPI)

################### Parameters ########################
analysisNumbers = [0]       # List of analysis systems to apply this script
RESULTS_FOLDER = 'Beam Probes'   # Name of results TreeGroupingFolder
################### End Parameters ########################


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
        if group.Name == name:
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


def getTableData(t0,colNum):
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


for a in analysisNumbers:
    analysis = Model.Analyses[a]
    solver_data = analysis.Solution.SolverData
    
    # Get all results ovjects
    resGroup = getResultsGroupByName(RESULTS_FOLDER, analysis.Solution)
    resChildren = [r for r in resGroup.Children]
       
    # Get the current units
    forceUnit = ExtAPI.DataModel.CurrentUnitFromQuantityName("Force")
    timeUnit = ExtAPI.DataModel.CurrentUnitFromQuantityName("Time")
    lengthUnit = ExtAPI.DataModel.CurrentUnitFromQuantityName("Length")
    stressUnit = ExtAPI.DataModel.CurrentUnitFromQuantityName("Stress")
    momentUnit = ExtAPI.DataModel.CurrentUnitFromQuantityName("Moment")
    stiffnessUnit = ExtAPI.DataModel.CurrentUnitFromQuantityName("Stiffness")
    areaUnit = ExtAPI.DataModel.CurrentUnitFromQuantityName("Area")
    
    forceQuan = Quantity(1, forceUnit)
    timeQuan = Quantity(1, timeUnit)
    stressQuan = Quantity(1, stressUnit)
    lengthQuan = Quantity(1, lengthUnit)
    areaQuan = Quantity(1, areaUnit)
    momentQuan = Quantity(1, momentUnit)
    stiffnessQuan = Quantity(1, stiffnessUnit)
    inertiaQuan = Quantity(1, lengthUnit + '^4')
    
    forceUnit = '[' + forceUnit + ']'
    timeUnit = '[' + timeUnit + ']'
    lengthUnit = '[' + lengthUnit + ']'
    stressUnit = '[' + stressUnit + ']'
    areaUnit = '[' + lengthUnit + '^2]'
    momentUnit = '[' + momentUnit + ']'
    stiffnessUnit = '[' + stiffnessUnit + ']'
    inertiaUnit = '[' + lengthUnit + '^4]'
    
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
    
    # Loop through all beam probes and create a results dictionary
    res = {}
    for result in resChildren:
        result.Activate()
        rid = result.BoundaryConditionSelection.ObjectId
        res[rid] = {}
        res[rid]['Name'] = result.BoundaryConditionSelection.Name
        timeCol = [a[0] for a in getTableData(result,2)]
        res[rid]['Time'] = [float(t) for t in timeCol[1:]]
        FX =[a[0] for a in getTableData(result,3)]
        FX = [float(x)*forceQuan for x in FX[1:]]
        res[rid]['Axial'] = FX
        TQ =[a[0] for a in getTableData(result,4)]
        TQ = [float(y)*momentQuan for y in TQ[1:]]
        res[rid]['Torque'] = TQ
        resSF_I = [a[0] for a in getTableData(result,5)]
        resSF_I = [float(y) for y in resSF_I[1:]]
        resSF_J = [a[0] for a in getTableData(result,6)]
        resSF_J = [float(y) for y in resSF_J[1:]]
        SF = []
        for i, j in zip(resSF_I, resSF_J):
            if abs(i) >= abs(j):
                SF.append(i * forceQuan)
            else:
                SF.append(j * forceQuan)
        res[rid]['Shear Force'] = SF
        resM_I = [a[0] for a in getTableData(result,7)]
        resM_I = [float(y) for y in resM_I[1:]]
        resM_J = [a[0] for a in getTableData(result,8)]
        resM_J = [float(y) for y in resM_J[1:]]
        bendMom = []
        res[rid]['Bending Moment'] = []
        for i, j in zip(resM_I, resM_J):
            if abs(i) >= abs(j):
                bendMom.append(i * momentQuan)
            else:
                bendMom.append(j * momentQuan)
        res[rid]['Bending Moment'] = bendMom
        rad = result.BoundaryConditionSelection.Radius
        res[rid]['Radius'] = rad
        mat = result.BoundaryConditionSelection.Material
        res[rid]['Material'] = mat
        
        # Compute beam length from reference and mobile coordinates
        xr = result.BoundaryConditionSelection.ReferenceXCoordinate
        yr = result.BoundaryConditionSelection.ReferenceYCoordinate
        zr = result.BoundaryConditionSelection.ReferenceZCoordinate
        xm = result.BoundaryConditionSelection.MobileXCoordinate
        ym = result.BoundaryConditionSelection.MobileYCoordinate
        zm = result.BoundaryConditionSelection.MobileZCoordinate
        length = ((xr-xm)**2 + (yr-ym)**2 + (zr-zm)**2)**(0.5)
        res[rid]['Length'] = length
        
        # Compute beam area, diameter, moments of inertia, axial stiffness
        area = pi*rad**2
        res[rid]['dia'] = 2.0*rad
        res[rid]['area'] = area
        I = pi*rad**4/4.0
        res[rid]['I'] = I
        J = pi*rad**4/2.0
        res[rid]['J'] = J
        if mat in mats.keys():
            modulus = mats[mat]['ElasticModulus']
            stiffness = modulus*area/length
            res[rid]['Stiffness'] = stiffness
        
        # Compute the various stresses
        dirStr = [f/area for f in FX]
        res[rid]['Direct Stress'] = dirStr
        bendStr = [m*rad/I for m in bendMom]
        res[rid]['Bending Stress'] = bendStr
        torStr = [t*rad/J for t in TQ]
        res[rid]['Torsional Stress'] = torStr
        combStr = [d + b for d, b in zip(dirStr, bendStr)]
        res[rid]['Combined Stress'] = combStr
        eqvStr = [(c**2 + 3.0*t**2)**(0.5) for c, t in zip(combStr, torStr)]
        res[rid]['Equivalent Stress'] = eqvStr
        
    

        
    # Create data dictionary to written to output csv file
    data = {}
    # Data column names
    cols = ['Beam Connection Name',
        'Beam Element ID',
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

    for rid in sorted(res.keys()):
        for t in range(len(res[rid]['Time'])):
            data[cols[0]].append(res[rid]['Name'])
            data[cols[1]].append(rid)
            data[cols[2]].append(res[rid]['Material'])
            data[cols[3]].append(res[rid]['dia'] / lengthQuan)
            data[cols[4]].append(res[rid]['Length'] / lengthQuan)
            data[cols[5]].append(res[rid]['area'] / areaQuan)
            data[cols[6]].append(res[rid]['I'] / inertiaQuan)
            data[cols[7]].append(res[rid]['J'] / inertiaQuan)
            if res[rid]['Material'] in mats.keys():
                data[cols[8]].append(res[rid]['Stiffness'] / stiffnessQuan)
            else:
                data[cols[8]].append(0)
            data[cols[9]].append(res[rid]['Time'][t])
            data[cols[10]].append(t+1)
            data[cols[11]].append(res[rid]['Axial'][t] / forceQuan)
            data[cols[12]].append(res[rid]['Shear Force'][t] / forceQuan)
            data[cols[13]].append(res[rid]['Torque'][t] / momentQuan)
            data[cols[14]].append(res[rid]['Bending Moment'][t] / momentQuan)
            data[cols[15]].append(res[rid]['Equivalent Stress'][t] / stressQuan)
            data[cols[16]].append(res[rid]['Direct Stress'][t] / stressQuan)
            data[cols[17]].append(res[rid]['Bending Stress'][t] / stressQuan)
            data[cols[18]].append(res[rid]['Combined Stress'][t] / stressQuan)
            data[cols[19]].append(res[rid]['Torsional Stress'][t] / stressQuan)

    x = datetime.datetime.now()
    
    file_name_body = analysis.Name + ' - Beam_Probe_Results_All_Times_' + x.strftime("%m") + "-" + x.strftime("%d") + "-" + x.strftime("%y")
    writeCSV(user_dir + '/' + file_name_body + ".csv", data, cols)
    
    print("[INFO] Process completed for " + analysis.Name)
    print("Open File: " + chr(34) + user_dir + chr(92) + file_name_body + ".csv" + chr(34) + '\n')