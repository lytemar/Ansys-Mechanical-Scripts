"""
Retrieve Reaction Moments Values at all analysis times for Moment Reaction Probes.
==================================================================================

This script reads the Tabular Data for each moment reaction probe and writes the data to a CSV file.

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
    ANSYS_VER = str(ExtAPI.DataModel.Project.ProductVersion)


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

   
    # Get all moment reaction probes
    MomentReactionCurrAnalysis = [child for child in analysis.Solution.Children if child.DataModelObjectCategory == DataModelObjectCategory.MomentReaction]
    
    # Get moment unit
    moment_unit = ExtAPI.DataModel.CurrentUnitFromQuantityName("Moment")
    timeUnit = ExtAPI.DataModel.CurrentUnitFromQuantityName("Time")
    
    # Loop through all reaction probes and create a results dictionary
    res = {}
    for result in MomentReactionCurrAnalysis:
        result.Activate()
        rid = result.ObjectId
        res[rid] = {}
        res[rid]['Name'] = result.Name
        timeCol = [a[0] for a in getTableData(result,2)]
        res[rid]['Time'] = [float(t) for t in timeCol[1:]]
        xReaction =[a[0] for a in getTableData(result,3)]
        res[rid]['MX'] = [float(x) for x in xReaction[1:]]
        yReaction =[a[0] for a in getTableData(result,4)]
        res[rid]['MY'] = [float(y) for y in yReaction[1:]]
        zReaction =[a[0] for a in getTableData(result,5)]
        res[rid]['MZ'] = [float(z) for z in zReaction[1:]]
        totalReaction =[a[0] for a in getTableData(result,6)]
        res[rid]['M_Total'] = [float(z) for z in totalReaction[1:]]
        matrix_full = [[timeCol[i], xReaction[i], yReaction[i], zReaction[i], totalReaction[i]] for i in range(len(timeCol))]
        
    # Create data dictionary to written to output csv file
    data = {}
    # Data column names
    cols = ['Moment Reaction Name',
            'Moment Reaction ID',
            'Time [' + timeUnit + ']',
            'MX [' + moment_unit + ']',
            'MY [' + moment_unit + ']',
            'MZ [' + moment_unit + ']',
            'Total Moment [' + moment_unit + ']']

    for c in cols:
        data[c] = []

    for rid in sorted(res.keys()):
        for t in range(len(res[rid]['Time'])):
            data[cols[0]].append(res[rid]['Name'])
            data[cols[1]].append(rid)
            data[cols[2]].append(res[rid]['Time'][t])
            data[cols[3]].append(res[rid]['MX'][t])
            data[cols[4]].append(res[rid]['MY'][t])
            data[cols[5]].append(res[rid]['MZ'][t])
            data[cols[6]].append(res[rid]['M_Total'][t])

    x = datetime.datetime.now()
    
    file_name_body = analysis.Name + ' - Moment_Reactions_' + x.strftime("%m-%d-%y")
    writeCSV(user_dir + '/' + file_name_body + ".csv", data, cols)
    
    print("[INFO] Process completed for " + analysis.Name)
    print("Open File: " + chr(34) + user_dir + chr(92) + file_name_body + ".csv" + chr(34) + '\n')