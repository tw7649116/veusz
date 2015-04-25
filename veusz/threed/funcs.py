#    Copyright (C) 2013 Jeremy S. Sanders
#    Email: Jeremy Sanders <jeremy@jeremysanders.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
##############################################################################

import math
import numpy as N

def pt_3_4(p):
    """Convert a 3D point to an affine point."""
    return N.array([p[0],p[1],p[2],1.])

def normalise(v):
    return v / N.linalg.norm(v)

def rotateM(angle, vec):
    """Return a matrix for a rotation of angle around vec.

    matrix: 4x4
    angle: radians
    vec: 3-vec
    """

    c = math.cos(angle)
    s = math.sin(angle)

    # axis
    a = normalise(N.array(vec))
    # temporary
    t = (1 - c) * a

    rotate = N.array([
        [c+t[0]*a[0],        0+t[1]*a[0]-s*a[2], 0+t[2]*a[0]+s*a[1], 0],
        [0+t[0]*a[1]+s*a[2], c+t[1]*a[1],        0+t[2]*a[1]-s*a[0], 0],
        [0+t[0]*a[2]-s*a[1], 0+t[1]*a[2]+s*a[0], c+t[2]*a[2],        0],
        [0,                  0,                  0,                  1]
        ])

    return rotate

def translationM(vec):
    """Return a translation matrix for vector (3vec)."""
    return N.array([
            [1, 0, 0, vec[0]],
            [0, 1, 0, vec[1]],
            [0, 0, 1, vec[2]],
            [0, 0, 0, 1     ]
            ])