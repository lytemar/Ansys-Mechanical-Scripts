"""
Add contact trackers to Solution Information for all nonlinear contacts
=======================================================================
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
trackers = {}
with Transaction(True):         # Suppress GUI update until complete to speed the process
    for c in contacts:
        trackers[c] = []
        
        # Create Number Contacting tracker
        _ = sol_info.AddNumberContacting()
        _.ContactRegion = c
        trackers[c].append(_)
        
        # Create Contact Pressure tracker
        _ = sol_info.AddContactPressure()
        _.ContactRegion = c
        trackers[c].append(_)
        
        # Create Penetration tracker
        _ = sol_info.AddPenetration()
        _.ContactRegion = c
        trackers[c].append(_)
    
        # Create Max Normal Stiffness tracker
        _ = sol_info.AddContactMaximumNormalStiffness()
        _.ContactRegion = c
        trackers[c].append(_)
        
        # Create Stabilization Energy tracker
        _ = sol_info.AddStabilizationEnergy()
        _.ContactRegion = c
        trackers[c].append(_)
        
        # Create Force Convergence tracker
        _ = sol_info.AddContactPairForceConvergenceNorm()
        _.ContactRegion = c
        trackers[c].append(_)
    
        # Create Gap tracker
        _ = sol_info.AddGap()
        _.ContactRegion = c
        trackers[c].append(_)
        
# Rename the trackers by definition
for c, tr in trackers.items():
    for t in tr:
        t.RenameBasedOnDefinition()

# Place the trackers into grouping folders for each contact
groups =[]
for i, c in enumerate(trackers.keys()):
    groups.append(Tree.Group(trackers[c]))
    groups[i].Name = "Contact - " + c.Name

# Place the tracker folders into one common folder
grps = Tree.Group(groups)
grps.Name = "Contact Trackers"
