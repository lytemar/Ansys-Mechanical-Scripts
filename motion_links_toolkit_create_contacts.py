"""
Create Contact Regions for a Chain Drive Defined from the Ansys Motion Links Tookit from Named Selections.  This is a wrokaround for a bug in the Motion Links Toolkit as of Version 2023 R2.
=============================================================================================================================================================================================

Parameters
---------
roller_surfs : Named Selection
    All roller OD faces
drive_sprocket_contact_surfs_teeth : Named Selection
    All sprocket tooth faces that contact the rollers
drive_sprocket_contact_surfs_side : Named Selection
	Side faces of the drive sprocket (that contact the side faces of the chain)
pulley_contact_chain_rollers : Named Selection
	Pulley face(s) that contact the chain rollers
pulley_contact_chain_outer_sides : Named Selection
	Pulley face(s) that contact the outer side of the chain
outer_side_chain : Named Selection
	Outer most chain link faces
insideChain : Named Selection
	Inner most chain link plate faces
"""

#import time
#StartTime = time.time()

DataModel = ExtAPI.DataModel

# before we run the script, we have to create a Named Selection with the name "roller_surfs", which presents the contact surface of chain rollers
nsRollers = DataModel.GetObjectsByName("roller_surfs")[0]

# we can find the Named Selections by name (it has to be unique)
nsDrive_sprocket = DataModel.GetObjectsByName("drive_sprocket_contact_surfs_teeth")[0]
nsPulley = DataModel.GetObjectsByName("pulley_contact_chain_rollers")[0]
nsDrive_Pulley = DataModel.GetObjectsByName("pulley_contact_chain_outer_sides")[0]
nsChainOutsideSurface = DataModel.GetObjectsByName("outer_side_chain")[0]
nsDrive_sprocket_outside = DataModel.GetObjectsByName("drive_sprocket_contact_surfs_side")[0]
nsChainInsideSurface = DataModel.GetObjectsByName("insideChain")[0]


# insert a contact group
SprocketTeethAndPulley = Model.Connections.AddConnectionGroup()
SprocketTeethAndPulley.Name = "sprocket teeth and pulley ID"

# insert a contact region for the sprocket teeth and chain rollers
SprocketToRollers = SprocketTeethAndPulley.AddContactRegion()
SprocketToRollers.Name = "sprocket to rollers contact"
SprocketToRollers.TargetLocation = nsDrive_sprocket
SprocketToRollers.SourceLocation = nsRollers

# insert a contact region for the pulley inside and chain outside surface
SprocketToRollers = SprocketTeethAndPulley.AddContactRegion()
SprocketToRollers.Name = "Pulley to chain outside contact"
SprocketToRollers.TargetLocation = nsDrive_Pulley
SprocketToRollers.SourceLocation = nsChainOutsideSurface

# insert a contact region for the sprocket outside Surface and chain inside surface
SprocketToRollers = SprocketTeethAndPulley.AddContactRegion()
SprocketToRollers.Name = "Sprocket outside surface to chain inside contact"
SprocketToRollers.TargetLocation = nsDrive_sprocket_outside
SprocketToRollers.SourceLocation = nsChainInsideSurface


# insert another contact region for pulley side
PulleyToRollers = SprocketTeethAndPulley.AddContactRegion()
PulleyToRollers.Name = "pulley to rollers contact"
PulleyToRollers.TargetLocation = nsPulley
PulleyToRollers.SourceLocation = nsRollers
