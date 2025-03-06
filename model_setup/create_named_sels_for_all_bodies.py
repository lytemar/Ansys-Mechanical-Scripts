'''
Create Named Selections for all bodies in the Geometry branch
=============================================================

Functions
---------
createNamedSelection
    Create a named selection with a name and geometry selection



'''
import re

def createNamedSelection(name, location):
    """
    Create a named selection with a name and geometry selection
    
    Parameters
    ----------
    name : str
        The name of the named selection
    location : list
        The list of IDs for the geometry selection
        
    Returns
    -------
    Ansys.ACT.Automation.Mechanical.NamedSelection
    
    """
    repl_str = r'[^\w]'     # find all non-alphanumeric characters
    _ = model.AddNamedSelection()
    _.Name = re.sub(repl_str, '_', name)[:32]       # limit length to 32 characters
    _.Location = location
    
    return _

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

        NSn = []
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
            
            print("Number of bodies in part: ", len(body_ids))
    
            # Create named selection for individual bodies.  If a multibody part, create named selection for the multibody part too.
            if len(body_ids) == 1:
                Sel.Ids = body_ids
                print("Sel.Ids: ", Sel.Ids)
                # Create named selection
                NSn.append(createNamedSelection(body_names[0], Sel))
            else:
                # Create Named Selection for the multibody part as a whole
                Sel.Ids = body_ids
                # print("Sel.Ids: ", Sel.Ids)
                NSn.append(createNamedSelection(Part.Name, Sel))
                # Create Named Selections for each part that composes the multibody part
                for id, name in zip(body_ids, body_names):
                    Sel.Ids = [id]
                    print("Sel.Ids: ", Sel.Ids)
                    _ = Part.Name + "_" + name
                    NSn.append(createNamedSelection(_, Sel))
    except:
        print("Add an empty Named Selection first, then re-run")
        
    # Append numbers after name in name selections if there are multiple bodies with the same name and limit length to 32
    i = 1   # counting variable
    # Get the names of the created named selections
    NSn_names = [x.Name for x in NSn]
    # Create dictionary with names and counts
    NSn_stats = {}
    for nm in NSn_names:
        if NSn_names.count(nm) > 1:
            NSn_stats[nm] = NSn_names.count(nm)
    for index, ns in enumerate(NSn):
        if ns.Name in NSn_stats.keys():
            val = NSn_stats[ns.Name]
            if val > 0:
                ns_name = ns.Name
                NSn[index].Name = ns_name[:32-1-len(str(val))] + "_" + str(val)     # truncate the name and append "_<num>"
                val -= 1
                NSn_stats[ns_name] = val
    
    # Place the new named selections in a Tree Grouping folder
    group = Tree.Group(NSn)
    group.Name = "Auto-generated"

