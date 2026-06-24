"""
Create a new coordinate system with specified origin and three orthogonal unit direction vectors.
=================================================================================================
"""

import math
 
##########################################################
# Created by P. Thieffry
# Last update: 2021/04/07
def dotProduct(v1,v2):
    return v2[0]*v1[0]+v2[1]*v1[1]+v2[2]*v1[2]
 
def TransformationMatrix(origCS,targCS):
    # compute transformation matrix to align origCS to targCS
    # All coordinates are expressed in the global CS
    #
    tMat=[[dotProduct(origCS[0],targCS[0]),dotProduct(origCS[0],targCS[1]),dotProduct(origCS[0],targCS[2])],
    [dotProduct(origCS[1],targCS[0]),dotProduct(origCS[1],targCS[1]),dotProduct(origCS[1],targCS[2])],
    [dotProduct(origCS[2],targCS[0]),dotProduct(origCS[2],targCS[1]),dotProduct(origCS[2],targCS[2])]]
    return tMat
##########################################################
 
##########################################################
# Modified from: https://learnopencv.com/rotation-matrix-to-euler-angles/
def rotationMatrixToEulerAngles_ZYX( R ) :
    sy = math.sqrt(R[0][0] * R[0][0] +  R[1][0] * R[1][0])
    singular = sy < 1e-6
    factor = 180./math.pi
    if  not singular :
        x = math.atan2(R[2][1] , R[2][2])*factor
        y = math.atan2(-R[2][0], sy)*factor
        z = math.atan2(R[1][0], R[0][0])*factor
    else :
        x = math.atan2(-R[1][2], R[1][1])*factor
        y = math.atan2(-R[2][0], sy)*factor
        z = 0
    return [z, y, x]
##########################################################
 
def norm( v ):
    return ( v[0]**2 + v[1]**2 + v[2]**2 )**0.5
 
def unit_vec( v ):
    n = norm( v )
    return [ _/n for _ in v ]
 
def CreateCS( origin , xyz , name , unit='mm' ):
    # Create coordinate
    testCS = ExtAPI.DataModel.Project.Model.CoordinateSystems.AddCoordinateSystem()
    testCS.OriginDefineBy= CoordinateSystemAlignmentType.Fixed
    testCS.OriginX = Quantity(origin[0],unit)
    testCS.OriginY = Quantity(origin[1],unit)
    testCS.OriginZ = Quantity(origin[2],unit)
 
    # Get rotations
    origCS = [[1,0,0],[0,1,0],[0,0,1]]
    tMat = TransformationMatrix(origCS,xyz)
    angs = rotationMatrixToEulerAngles_ZYX(tMat)
 
    ##########################################################
    # Created by M.H. Pernelle
    # Last update: 2021/06
    # Perform transformation
    testCS.PrimaryAxisDefineBy = CoordinateSystemAlignmentType.GlobalX
    # Rotation Z
    testCS.RotateZ()
    testCS.SetTransformationValue(1,angs[0])
    # Rotation Y
    testCS.RotateY()
    testCS.SetTransformationValue(2,angs[1])
    # Rotation X
    testCS.RotateX()
    testCS.SetTransformationValue(3,angs[2])
    ##########################################################
 
    # Set name
    testCS.Name = name
 
# Orientation vectors
# xyz = [x, y, z]
xyz = [[0.85, -.53, .05],[.53, .84, -.13],[.03, .14, .99]]

# Origin with respect to global coordinates
orig = [.44, 2.40, -.05]
CreateCS( orig , xyz , 'my_cs' , unit='in' )
