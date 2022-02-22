'''
Create Named Selections for all bodies in the Geometry branch
=============================================================

Functions
---------
createNamedSelection
    Create a named selection with a name and geometry selection
'''

def createNamedSelection(name, location):
    """
    Create a named selection with a name and geometry selection
    
    Parameters
    ----------
    name : str
        The name of the named selection
    location : list
        The list of IDs for the geometry selection
    """
    _ = model.AddNamedSelection()
    _.Name = name
    _.Location = location

# Selection
SlMn = ExtAPI.SelectionManager
SlMn.ClearSelection()
Sel = SlMn.CreateSelectionInfo(SelectionTypeEnum.GeometryEntities)

# Model
model = ExtAPI.DataModel.Project.Model

# Get parts
Parts = model.Geometry.GetChildren(DataModelObjectCategory.Part, True)

print("Listing properties of Items:")
with Transaction():             # Suppress GUI update until finish to improve speed
    try:

        for Part in Parts:
            PName = Part.Name
    		
    		# Collect all body IDs and names into lists
            body_ids = []
            body_names = []
            for Body in Part.Children:
                BName = Body.Name
                BId = Body.GetGeoBody().Id
                print("Body name: " + BName + ", BId: " + str(BId))
                body_ids.append(BId)
                body_names.append(BName)
    
            # Create named selection for individual bodies.  If a multibody part, create named selection for the multibody part too.
            if len(body_ids) == 1:
                Sel.Ids = body_ids
                print("Sel.Ids: ", Sel.Ids)
                # Create named selection
                createNamedSelection(body_names[0], Sel)
            else:
                # Create Named Selection for the multibody part as a whole
                Sel.Ids = body_ids
                # print("Sel.Ids: ", Sel.Ids)
                createNamedSelection(Part.Name, Sel)
                # Create Named Selections for each part that composes the multibody part
                for id, name in zip(body_ids, body_names):
                    Sel.Ids = [id]
                    print("Sel.Ids: ", Sel.Ids)
                    _ = Part.Name + ": " + name
                    createNamedSelection(_, Sel)
    except:
        print("Add an empty Named Selection first, then re-run")
        
    # Append numbers after name in name selections if there are multiple bodies with the same name
    i = 1   # counting variable
    # Get all created named selections
    NSn = ExtAPI.DataModel.Project.Model.NamedSelections.GetChildren(DataModelObjectCategory.NamedSelection, True)
    # Get the names of the created named selections
    NSn_names = [x.Name for x in NSn]
    # Create dictionary with names and counts
    NSn_stats = {}
    for nm in NSn_names:
        # NSn_stats[nm] = 0
        if NSn_names.count(nm) > 1:
            NSn_stats[nm] = NSn_names.count(nm)
    for index, ns in enumerate(NSn):
        if ns.Name in NSn_stats.keys():
            val = NSn_stats[ns.Name]
            if val > 0:
                ns_name = ns.Name
                NSn[index].Name = ns_name + " " + str(val)
                val -= 1
                NSn_stats[ns_name] = val

