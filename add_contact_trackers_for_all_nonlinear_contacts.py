"""
Add contact trackers to Solution Information for all nonlinear contacts
==================================================================
"""

model = ExtAPI.DataModel.Project.Model
analysis = model.Analyses[0]
sol_info = analysis.Solution.SolutionInformation

# Get all nonliner connections and contacts
conns = model.Connections
contacts = conns.GetChildren(DataModelObjectCategory.ContactRegion, True)
linear_contacts = [ContactType.Bonded, ContactType.NoSeparation]
contacts = [c for c in contacts if c.ContactType not in linear_contacts]
supp_conts = [c for c in contacts if c.Suppressed]

# Create contact trackers
with Transaction():         # Suppress GUI update until complete to speed the process
    for c in contacts:
        _ = sol_info.AddNumberContacting()
        _.ContactRegion = c
        _.RenameBasedOnDefinition()
    
    for c in contacts:
        _ = sol_info.AddContactPressure()
        _.ContactRegion = c
        _.RenameBasedOnDefinition()
        
    for c in contacts:
        _ = sol_info.AddPenetration()
        _.ContactRegion = c
        _.RenameBasedOnDefinition()
    
    for c in contacts:
        _ = sol_info.AddContactMaximumNormalStiffness()
        _.ContactRegion = c
        _.RenameBasedOnDefinition()
        
    for c in contacts:
        _ = sol_info.AddStabilizationEnergy()
        _.ContactRegion = c
        _.RenameBasedOnDefinition()
        
    for c in contacts:
        _ = sol_info.AddContactPairForceConvergenceNorm()
        _.ContactRegion = c
        _.RenameBasedOnDefinition()
    
    for c in contacts:
        _ = sol_info.AddGap()
        _.ContactRegion = c
        _.RenameBasedOnDefinition()


# TODO:  Add contact trackers for each contact into its own folder