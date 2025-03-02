#-------------------------------------------------------------------------------

__all__ = ['update_currentNtoC', 'update_oNtoC', 'update_dNtoC', 'regenerate_currentNtoC', 'regenerate_oNtoC', 'regenerate_all_dNtoCs', 'regenerate_dNtoC', 'switch_color_attribute_domain']

#-------------------------------------------------------------------------------


import bpy
from bpy import context, types, props
from mathutils import Vector

from ._attribute_helpers import (
    group_attribute_values,
    flatten_attribute_values,
    populate_corner_attribute_values,
    populate_point_attribute_values
    )
from ._ntoc_helpers import (
    convert_normal_to_color
    )



# NORMALS TO COLOURS
def update_currentNtoC(context, currentNtoC_attribute_name):
    obj = context.object
    mesh = obj.data

    if bpy.app.version < (4, 1, 0):
        mesh.calc_normals_split()

    for loop in mesh.loops:
        normal = mesh.corner_normals[loop.index].vector
        color_normal = convert_normal_to_color(normal)
        mesh.attributes[currentNtoC_attribute_name].data[loop.index].color_srgb = color_normal


def update_oNtoC(context, oN_attribute_name, oNtoC_attribute_name):
    obj = context.object
    mesh = obj.data

    oN_attribute = mesh.attributes[oN_attribute_name]
    oN = group_attribute_values(oN_attribute, 'vector', 3)
    if oN_attribute.domain == 'POINT':
        oN = populate_corner_attribute_values(mesh, oN)

    for loop in mesh.loops:
        normal = oN[loop.index]
        color_normal = convert_normal_to_color(normal)
        mesh.attributes[oNtoC_attribute_name].data[loop.index].color_srgb = color_normal


def update_dNtoC(context, oN_attribute_name, dN_attribute_name, dNtoC_attribute_name):
    obj = context.object
    mesh = obj.data

    oN_attribute = mesh.attributes[oN_attribute_name]
    oN = group_attribute_values(oN_attribute, 'vector', 3)
    if oN_attribute.domain == 'POINT':
        oN = populate_corner_attribute_values(mesh, oN)
    
    dN_attribute = mesh.attributes[dN_attribute_name]
    dN = group_attribute_values(dN_attribute, 'vector', 3)
    if dN_attribute.domain == 'POINT':
        dN = populate_corner_attribute_values(mesh, dN)

    for loop in mesh.loops:
        normal = Vector(oN[loop.index])
        delta = Vector(dN[loop.index])
        dNormal = normal + delta
        color_normal = convert_normal_to_color(dNormal)
        mesh.attributes[dNtoC_attribute_name].data[loop.index].color_srgb = color_normal


def regenerate_currentNtoC(context, currentNtoC_attribute_name):
    obj = context.object
    mesh = obj.data

    if currentNtoC_attribute_name in mesh.attributes:
        mesh.attributes.remove(mesh.attributes[currentNtoC_attribute_name])
    mesh.attributes.new(currentNtoC_attribute_name, 'FLOAT_COLOR', 'CORNER')
    
    update_currentNtoC(context, currentNtoC_attribute_name)
    
    obj.data.update()


def regenerate_oNtoC(context, oN_attribute_name, oNtoC_attribute_name):
    obj = context.object
    mesh = obj.data

    if oNtoC_attribute_name in mesh.attributes:
        mesh.attributes.remove(mesh.attributes[oNtoC_attribute_name])
    mesh.attributes.new(oNtoC_attribute_name, 'FLOAT_COLOR', 'CORNER')
    
    update_oNtoC(context, oN_attribute_name, oNtoC_attribute_name)
    
    obj.data.update()


def regenerate_all_dNtoCs(context, oN_attribute_name, key_names, dN_attribute_suffix, dNtoC_attribute_suffix):
    obj = context.object
    mesh = obj.data
    
    for key_name in key_names:
        dN_attribute_name = key_name + dN_attribute_suffix
        dNtoC_attribute_name = key_name + dNtoC_attribute_suffix

        if dNtoC_attribute_name in mesh.attributes:
            mesh.attributes.remove(mesh.attributes[dNtoC_attribute_name])
        mesh.attributes.new(dNtoC_attribute_name, 'FLOAT_COLOR', 'CORNER')

        update_dNtoC(context, oN_attribute_name, dN_attribute_name, dNtoC_attribute_name)
    
    obj.data.update()


def regenerate_dNtoC(context, oN_attribute_name, key_name, dN_attribute_suffix, dNtoC_attribute_suffix):
    obj = context.object
    mesh = obj.data
    
    dN_attribute_name = key_name + dN_attribute_suffix
    dNtoC_attribute_name = key_name + dNtoC_attribute_suffix

    if dNtoC_attribute_name in mesh.attributes:
        mesh.attributes.remove(mesh.attributes[dNtoC_attribute_name])
    mesh.attributes.new(dNtoC_attribute_name, 'FLOAT_COLOR', 'CORNER')

    update_dNtoC(context, oN_attribute_name, dN_attribute_name, dNtoC_attribute_name)
    
    obj.data.update()
    


# DOMAIN SWITCH
def switch_color_attribute_domain(context, attribute_name):
    obj = context.object
    mesh = obj.data

    attribute = mesh.attributes[attribute_name]
    grouped_attribute = group_attribute_values(attribute, 'color_srgb', 4)

    if attribute.domain == 'POINT':
        corner_attribute = populate_corner_attribute_values(mesh, grouped_attribute)
        flat_corner_attribute = flatten_attribute_values(corner_attribute)

        mesh.attributes.remove(attribute)
        mesh.attributes.new(attribute_name, 'FLOAT_COLOR', 'CORNER')
        mesh.attributes[attribute_name].data.foreach_set('color_srgb', flat_corner_attribute)

    elif attribute.domain == 'CORNER':
        point_attribute = populate_point_attribute_values(mesh, grouped_attribute)
        flat_point_attribute = flatten_attribute_values(point_attribute)

        mesh.attributes.remove(attribute)
        mesh.attributes.new(attribute_name, 'FLOAT_COLOR', 'POINT')
        mesh.attributes[attribute_name].data.foreach_set('color_srgb', flat_point_attribute)

    obj.data.update()
    return mesh.attributes[attribute_name].domain


