"""
Calculate Stress Resultants for all beam connections using results from beam probes.
===================================================================================

"""
import wbjn
import datetime
import csv
cmd = 'returnValue(GetUserFilesDirectory())'
user_dir = wbjn.ExecuteCommand(ExtAPI, cmd)

################### Parameters ########################
analysisNumbers = [0]       # List of analysis systems to apply this script

#  Place units in Ansys Mechanical format for output conversion
lengthUnit = 'in'           # Desired length output unit
areaUnit = '[' + lengthUnit + '^2]'    # Area Unit
forceUnit = 'lbf'           # Desired force output unit
stressUnit = '[' + forceUnit + ' ' + lengthUnit + '^-2]'         # Desired stress output unit
momentUnit = '[' + forceUnit + ' ' + lengthUnit + ']'               # Desired moment/torque output unit

lengthUnit = '[' + lengthUnit + ']'
forceUnit = '[' + forceUnit + ']'


################### End Parameters ########################

def writeCSV(filename, data, cols):
    """
    Function to write python data to a csv file.
    
    Parameters
    ----------
    filename : str
        Filepath for the output file
    data : dict
        Data dictionary
    cols : list of str
        Column header names
    
    Returns
    -------
    None
    """
    with open(filename, 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(cols)
        writer.writerows(zip(*[data[col] for col in cols]))


for a in analysisNumbers:
    analysis = Model.Analyses[a]
    analysis_settings = analysis.AnalysisSettings
    n = analysis_settings.NumberOfSteps             # number of time steps
    # List of display times for future use
    DISP_TIMES = [analysis_settings.GetStepEndTime(i) for i in range(1, n+1, 1)]
    
    # List of beam probes
    beam_probes = analysis.Solution.GetChildren(DataModelObjectCategory.BeamProbe, True)
    
    # Boundary condition (beam connection) for each beam probe
    beam_conns = [p.BoundaryConditionSelection for p in beam_probes]
    N_BEAM_CONNS = len(beam_conns)      # Number of beam connections
    
    # Dimesions for each beam connection
    rads = [c.Radius for c in beam_conns]               # Cross-Sectional Radius
    areas = [pi*r**2 for r in rads]                     # Cross_Sectional Area
    Is = [(pi*r**4)/4.0 for r in rads]                  # Area moment of inertia
    Js = [(pi*r**4)/2.0 for r in rads]                  # Ploar moment of inertia
    
    # Get Results from the beam probes
    afs = [p.AxialForce for p in beam_probes]           # Axial forces
    tqs = [p.Torque for p in beam_probes]               # Torques
    sfis = [p.ShearForceAtI for p in beam_probes]       # Shear forces at I
    sfjs = [p.ShearForceAtJ for p in beam_probes]       # Shear forces at J
    mis = [p.MomentAtI for p in beam_probes]            # Moments at I
    mjs = [p.MomentAtJ for p in beam_probes]            # Moments at J
    
    # Maximum shear forces and bending moments
    sfs = [max(abs(sfi), abs(sfj)) for sfi, sfj in zip(sfis, sfjs)]
    moms = [max(abs(mi), abs(mj)) for mi, mj in zip(mis, mjs)]
    
    # Stress resultants
    axStrs = [af/area for af, area in zip(afs, areas)]          # Axial stresses
    bndStrs = [mom*rad/I for mom, rad, I in zip(moms, rads, Is)]   # Bending stresses
    dirStrs = [a + b for a, b in zip(axStrs, bndStrs)]              # Direct stresses
    torStrs = [tq*rad/J for tq, rad, J in zip(tqs, rads, Js)]   # Torsional stresses
    shStrs = [sf/area*4.0/3 for sf, area in zip(sfs, areas)]   # Shear stresses
    tau_xys = [max(abs(t+s), abs(t-s)) for t, s in zip(torStrs, shStrs)]   # Maximum tau_xy stresses
    sig_p1s = [d/2 + ((d/2)**2 + txy**2)**(0.5) for d, txy in zip(dirStrs, tau_xys)]   # Maximum principal stresses
    sig_p2s = [d/2 - ((d/2)**2 + txy**2)**(0.5) for d, txy in zip(dirStrs, tau_xys)]   # Minimum principal stresses
    tauMaxStrs = [1/2.0*(s1 - s2) for s1, s2 in zip(sig_p1s, sig_p2s)]    # Maximum Shear Stress
    eqvStrs = [(s1**2 + s2**2 - s1*s2)**(0.5) for s1, s2, in zip(sig_p1s, sig_p2s)]     # Equivalent stresses
    
    # Create data dictionary to written to output csv file
    data = {}
    cols = ['Results Probe Name',
            'Beam Connection Name',
            'Radius ' + lengthUnit,
            'Cross-Sectional Area ' + areaUnit,
            'Axial Force ' + forceUnit,
            'Torque ' + momentUnit,
            'Maximum Shear Force ' + forceUnit,
            'Maximum Bending Moment ' + momentUnit,
            'Maximum Equivalent Stress ' + stressUnit,
            'Axial Stress ' + stressUnit,
            'Maximum Bending Stress ' + stressUnit,
            'Maximum Direct Stress ' + stressUnit,
            'Torsional Stress ' + stressUnit,
            'Maximum Principal Stress ' + stressUnit,
            'Minimum Principal Stress ' + stressUnit,
            'Maximum Shear Stress ' + stressUnit]
    data[cols[0]] = [p.Name for p in beam_probes]
    data[cols[1]] = [p.Name for p in beam_conns]
    data[cols[2]] = [r/Quantity('1 ' + lengthUnit) for r in rads]
    data[cols[3]] = [a/Quantity('1 ' + areaUnit) for a in areas]
    data[cols[4]] = [f/Quantity('1 ' + forceUnit) for f in afs]
    data[cols[5]] = [t/Quantity('1 ' + momentUnit) for t in tqs]
    data[cols[6]] = [f/Quantity('1 ' + forceUnit) for f in sfs]
    data[cols[7]] = [mom/Quantity('1 ' + momentUnit) for mom in moms]
    data[cols[8]] = [s/Quantity('1 ' + stressUnit) for s in eqvStrs]
    data[cols[9]] = [s/Quantity('1 ' + stressUnit) for s in axStrs]
    data[cols[10]] = [s/Quantity('1 ' + stressUnit) for s in bndStrs]
    data[cols[11]] = [s/Quantity('1 ' + stressUnit) for s in dirStrs]
    data[cols[12]] = [s/Quantity('1 ' + stressUnit) for s in torStrs]
    data[cols[13]] = [s/Quantity('1 ' + stressUnit) for s in sig_p1s]
    data[cols[14]] = [s/Quantity('1 ' + stressUnit) for s in sig_p2s]
    data[cols[15]] = [s/Quantity('1 ' + stressUnit) for s in tauMaxStrs]
    
    
    x = datetime.datetime.now()
    
    file_name_body = analysis.Name + ' - Bolt_Results_' + x.strftime("%m") + "-" + x.strftime("%d") + "-" + x.strftime("%y")
    writeCSV(user_dir + '/' + file_name_body + ".csv", data, cols)
    
    print("[INFO] Process completed for " + analysis.Name)
    print("Open File: " + chr(34) + user_dir + chr(92) + file_name_body + ".csv" + chr(34) + '\n')
