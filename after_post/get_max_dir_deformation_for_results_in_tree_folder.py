"""
Retrieve Maximum Value Over Time for Directional Deformation Results in Tree Folder.
====================================================================================================

This script reads the Maximum Value Over Time for Directional Deformation results and wrties the data to a CSV file.
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
    
    ################### Parameters ########################
    DIRECTIONS = ['X', 'Y', 'Z']    # List of directions to extract
    RESULTS_FOLDER = 'Directional Deformation for Named Selections: Results Scoping'   # Common part of results TreeGroupingFolder
    """
    The tree grouping folder for each direction is composed for "<direction>-Axis " before the common part.  For example,
    X-direction results are stored in a folder called `X-Axis Directional Deformation for Named Selections: Results Scoping` 
    """
    ################### End Parameters ########################

    import wbjn
    import datetime
    import csv
    import mech_dpf
    import Ans.DataProcessing as dpf
    cmd = 'returnValue(GetUserFilesDirectory())'
    user_dir = wbjn.ExecuteCommand(ExtAPI, cmd)
    mech_dpf.setExtAPI(ExtAPI)
    analysis = solution.Parent
    solver_data = solution.SolverData
    analysis_type = analysis.AnalysisType
    analysis_name = analysis.Name
    ANSYS_VER = str(ExtAPI.DataModel.Project.ProductVersion)

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

   
    # Get the current units
    lengthUnit = ExtAPI.DataModel.CurrentUnitFromQuantityName("Length")
       
    for d in DIRECTIONS:
        # Add prefix to results folder
        RESULTS_FOLDER_DIR = d.ToUpper() + '-Axis ' + RESULTS_FOLDER
        
        # Get all results that are grouped under the folder RESULTS_FOLDER
        resGroup = getResultsGroupByName(RESULTS_FOLDER_DIR, analysis.Solution)
        resChildren = [r for r in resGroup.Children]
        resNames = [r.Name for r in resChildren]
        resIDs = [r.ObjectId for r in resChildren]
        resLocNames = [r.Location.Name for r in resChildren]
        resMaxValues = [r.MaximumOfMaximumOverTime.Value for r in resChildren]
               
        # Create data dictionary to written to output csv file
        data = {}
        # Data column names
        cols = ['Result ID',
                'Result Name',
                'Scope Name',
                d.ToUpper() +'-Axis Max Directional Deformation [' + lengthUnit + ']']
        
        data = {}
        data[cols[0]] = resIDs
        data[cols[1]] = resNames
        data[cols[2]] = resLocNames
        data[cols[3]] = resMaxValues

        x = datetime.datetime.now()
    
        file_name_body = analysis.Name + ' - ' + d.ToUpper() + '-Axis_Max_Directional_Deformation_' + x.strftime("%m") + "-" + x.strftime("%d") + "-" + x.strftime("%y")
        writeCSV(user_dir + '/' + file_name_body + ".csv", data, cols)
