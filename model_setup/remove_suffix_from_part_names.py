'''
Rename all bodies, removing all text after the slash
====================================================
'''

import re

# Model
model = ExtAPI.DataModel.Project.Model

# Get parts
Parts = model.Geometry.GetChildren(DataModelObjectCategory.Part, True)

print("Renaming parts and bodies:")
with Transaction():             # Suppress GUI update until finish to improve speed

    for Part in Parts:

		# Collect all body IDs and names into lists
        body_names = []
        for Body in Part.Children:
            BName = Body.Name
            if "Beam" in BName:
                Body.Name = "Beam " + re.findall('(?<=Beam\s).*$', Body.Name)[0]
            else:
                Body.Name = Body.Name.split("\\")[0]
            body_names.append(Body.Name)
