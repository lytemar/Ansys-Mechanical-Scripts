""" Script to Generate Local DPF HTML Help

Used from within Mechanical Scripting
"""

import mech_dpf
import Ans.DataProcessing as dpf

my_output_path = (r"cC:\Users\Public\Downloads")
op = dpf.operators.utility.html_doc()
op.inputs.output_path.Connect(my_output_path)
op.Run()
