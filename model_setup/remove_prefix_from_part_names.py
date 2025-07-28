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
                temp = Body.Name.split("\\")
                if len(temp) == 1:
                    Body.Name = temp[0]
                else:
                    Body.Name = temp[1]
            # Remove "Midsurface - " at the beginning of the name
            if "Midsurface" in BName:
                Body.Name = re.findall('(?<=Midsurface\s-\s).*$', Body.Name)[0]
            body_names.append(Body.Name)
