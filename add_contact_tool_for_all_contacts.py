"""
Add contact tools to the solution branch for all contacts
=========================================================

Functions
---------
createContactTool
    Create a contact tool for a single contact containing Pressure, Frictional Stress, Sliding Distance, Penetration and Gap for a list of times
"""
#import time
#StartTime = time.time()

model = ExtAPI.DataModel.Project.Model
analyses = model.Analyses
analysis = model.Analyses[0]
analysis_settings = analysis.AnalysisSettings
n = analysis_settings.NumberOfSteps             # number of time steps
DISP_TIMES = [analysis_settings.GetStepEndTime(i) for i in range(1, n+1, 1)]

# Get all nonliner connections and contacts
conns = model.Connections
contacts = conns.GetChildren(DataModelObjectCategory.ContactRegion, True)
linear_contacts = [ContactType.Bonded, ContactType.NoSeparation]
#contacts = [c for c in contacts if c.ContactType not in linear_contacts]
#supp_conts = [c for c in contacts if c.Suppressed]

# Contact names and IDs
contNames = [i.Name for i in contacts]
contIDs = [i.ObjectId for i in contacts]

# Create contact tool for each contact

def createContactTool(contactID, lstContID, contName, dispTimes):
    """
    Create a contact tool for a single contact containing Pressure, Frictional Stress, Sliding Distance, Penetration and Gap for a list of times
    
    Parameters
    ----------
    contactID : int
        The ID of the contact for which to create the tool
    lstContID : list of ints
        list of contact IDs for all contacts in the model
    contName : string
        The name of the contact for which the tool is created
    dispTimes : list of Quantities
        list of analysis times for which to display contact tools
        
    Returns
    -------
    Ansys.ACT.Automation.Mechanical.PostContactTool
        The newly created post processing contact tool
    """
    
    # add a contact tool
    contact_tool = analysis.Solution.AddContactTool()
    
    # scope only to single contact ID
    # These lines are unsupported beta features
    #contact_tool.InternalObject.AddScopedContact(contIDs[130])
    [contact_tool.InternalObject.RemoveScopedContact(i) for i in lstContID if i != contactID]
    
    # rename the contact tool
    contact_tool.Name = "Contact Tool - " + contName
    print("Contact tool name: " + contact_tool.Name)
    
    # Create contact Status, Pressure, Frictional Stress, Penetration and Gap for each time in dispTimes
    for idx, time in enumerate(dispTimes):
        # Status
        if idx == 0:
            status = contact_tool.GetChildren(DataModelObjectCategory.ContactStatus, True)[0]
        else:
            status = contact_tool.AddStatus()
        status.DisplayTime = time
        status.Name = "Status - " + str(time)
        
        # Pressure
        pressure = contact_tool.AddPressure()
        pressure.DisplayTime = time
        pressure.Name = "Pressure - " + str(time)
        
        # Frictional Stress
        fric_stress = contact_tool.AddFrictionalStress()
        fric_stress.DisplayTime = time
        fric_stress.Name = "Frictional Stress - " + str(time)
        
        # Penetration
        pene = contact_tool.AddPenetration()
        pene.DisplayTime = time
        pene.Name = "Penetration - " + str(time)
        
        # Gap
        gap = contact_tool.AddGap()
        gap.DisplayTime = time
        gap.Name = "Gap - " + str(time)
        
        # Sliding Distance
        slide_dist = contact_tool.AddSlidingDistance()
        slide_dist.DisplayTime = time
        slide_dist.Name = "Sliding Distance - " + str(time)
        
    return contact_tool

with Transaction():         # Suppress GUI update until complete to speed the process
    # Create contact tools and collect in a list
    contact_tools = [createContactTool(id, contIDs, name, DISP_TIMES) for id, name in zip(contIDs, contNames)]
    # contact_tools = [createContactTool(id, contIDs, name, DISP_TIMES) for id, name,c  in zip(contIDs, contNames, contacts) if not c.Suppressed]

# Put all contact tools into a group folder
group = Tree.Group(contact_tools)
group.Name = "Contact Tools"

Tree.Activate([analysis.Solution])

#print(str(time.time() - StartTime))
