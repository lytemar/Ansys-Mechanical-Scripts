import mech_dpf
import Ans.DataProcessing as dpf
mech_dpf.setExtAPI(ExtAPI)

# Set path to results file
analysis = ExtAPI.DataModel.Project.Model.Analyses[3]
filepath = analysis.ResultFileName
model = dpf.Model(filepath)
mesh = model.Mesh

# Get the beam elements
op_scope = dpf.operators.scoping.on_mesh_property()
op_scope.inputs.requested_location.Connect("element")
op_scope.inputs.property_name.Connect("beam_elements")
op_scope.inputs.mesh.Connect(model.Mesh)
op_scope.outputs.mesh_scoping.GetData()
# DPF  Scoping: 
#  with Elemental location and 2 entities
 
op_scope_t = dpf.operators.scoping.transpose()
op_scope_t.inputs.mesh_scoping.Connect(op_scope)
op_scope_t.inputs.meshed_region.Connect(mesh)
op_scope_t.outputs.mesh_scoping.GetDataT1()
# DPF  Scoping: 
#  with Nodal location and 4 entities
 
op_nodal = dpf.operators.result.element_nodal_force(data_sources=model.DataSources, mesh_scoping=op_scope_t.outputs.mesh_scoping)
op_nodal.outputs.fields_container.GetData()


beam_connects = Model.Connections.GetChildren(DataModelObjectCategory.Beam, True)
bcNames = [bc.Name for bc in beam_connects]
bcProps = [bc.Properties for bc in beam_connects]