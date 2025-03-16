'''
jan.holinka@seznam.cz
Created by Jan Holinka
This file is part of Dimensions and Lines. Dimensions and Lines is free software; you can redistribute it 
and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; 
either version 3 of the License, or (at your option) any later version. This program is distributed in the hope 
that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or 
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details. You should have received 
a copy of the GNU General Public License along with this program; if not, see <https://www.gnu.org/licenses>.
'''

import importlib

if "dimension_addon_by_der" in locals():
    importlib.reload(dimension_addon_by_der)
else:
    from . import dimension_addon_by_der

#if "bpy" in locals():
    #import imp
    #imp.reload(dimension_addon_by_der)
#else:
    #from . import (
        #dimension_addon_by_der,
    #)

import bpy

#from . import dimension_addon_by_der

def register():
    dimension_addon_by_der.register()
     
def unregister():
    dimension_addon_by_der.unregister()