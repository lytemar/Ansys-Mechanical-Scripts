"""
Add force convergence contact trackers to Solution Information for all nonlinear contacts
=========================================================================================
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
        # Create Force Convergence tracker
        _ = sol_info.AddContactPairForceConvergenceNorm()
        _.ContactRegion = c
        trackers[c] = _
        
# Rename the trackers by definition
for c, tr in trackers.items():
    tr.RenameBasedOnDefinition()

# Place the trackers into a group folder
grp = []
for i, c in enumerate(trackers.keys()):
    grp.append(trackers[c])
tree = Tree.Group(grp)
tree.Name = "Contact Trackers - Force Convergence"

Tree.Activate([analysis.Solution])