#-------------------------------------------------------------------------------

__all__ = ['original_to_current_normals', 'current_to_original_normals', 'add_dN_to_current', 'original_plus_dN_to_current', 'retarget_dN_to_current_normals']

#-------------------------------------------------------------------------------


import bpy
from bpy import context, types, props
from mathutils import Vector

from ._attribute_helpers import (
    group_attribute_values,
    populate_corner_attribute_values
    )


# ORIGINAL NORMALS

def original_to_current_normals(context, oN_attribute_name):
    obj = context.object
    mesh = obj.data

    if bpy.app.version < (4, 1, 0):
        mesh.calc_normals_split()

    oN_attribute = mesh.attributes[oN_attribute_name]
    grouped_oN = group_attribute_values(oN_attribute, 3)
    
    if oN_attribute.domain == 'POINT':
        mesh.normals_split_custom_set_from_vertices(grouped_oN)
    elif oN_attribute.domain == 'CORNER':
        mesh.normals_split_custom_set(grouped_oN)

    obj.data.update()


def current_to_original_normals(context, oN_attribute_name):
    obj = context.object
    mesh = obj.data
    
    if bpy.app.version < (4, 1, 0):
        mesh.calc_normals_split()
    
    if context.object.dnorm_props.oN_attribute:
        existing_attribute = mesh.attributes[oN_attribute_name]
        mesh.attributes.remove(existing_attribute)
    mesh.attributes.new(oN_attribute_name, 'FLOAT_VECTOR', 'CORNER')
    
    for loop in mesh.loops:
        mesh.attributes[oN_attribute_name].data[loop.index].vector = mesh.corner_normals[loop.index].vector

    obj.data.update()



# DNORMS

# TODO: figure out why adding onto normals calculate from faces produce seams.


def add_dN_to_current(context, dN_name):
    obj = context.object
    mesh = obj.data
    
    if bpy.app.version < (4, 1, 0):
        mesh.calc_normals_split()

    dN_attribute = mesh.attributes[dN_name]
    grouped_dN = group_attribute_values(dN_attribute, 3)

    resulting_normals = []
    if dN_attribute.domain == 'POINT':
        for loop in mesh.loops:
            normal = mesh.corner_normals[loop.index].vector + Vector(grouped_dN[loop.vertex_index])
            resulting_normals.append(normal.normalized())
    elif dN_attribute.domain == 'CORNER':
        for loop in mesh.loops:
            normal = mesh.corner_normals[loop.index].vector + Vector(grouped_dN[loop.index])
            resulting_normals.append(normal.normalized())
    mesh.normals_split_custom_set(resulting_normals)

    obj.data.update()


def original_plus_dN_to_current(context, dN_name, oN_attribute_name):
    obj = context.object
    mesh = obj.data
    
    if bpy.app.version < (4, 1, 0):
        mesh.calc_normals_split()
    
    oN_attribute = mesh.attributes[oN_attribute_name]
    grouped_oN = group_attribute_values(oN_attribute, 3)
    dN_attribute = mesh.attributes[dN_name]
    grouped_dN = group_attribute_values(dN_attribute, 3)

    if oN_attribute.domain == dN_attribute.domain == 'POINT':
        resulting_normals = [(Vector(oNormal) + Vector(dNormal)).normalized() for oNormal, dNormal in zip(grouped_oN, grouped_dN)]
        mesh.normals_split_custom_set_from_vertices(resulting_normals)
    else:
        if oN_attribute.domain == 'POINT':
            grouped_oN = populate_corner_attribute_values(mesh, grouped_oN)
        if dN_attribute.domain == 'POINT':
            grouped_dN = populate_corner_attribute_values(mesh, grouped_dN)
        resulting_normals = [(Vector(oNormal) + Vector(dNormal)).normalized() for oNormal, dNormal in zip(grouped_oN, grouped_dN)]
        mesh.normals_split_custom_set(resulting_normals)

    obj.data.update()





def retarget_dN_to_current_normals(context, dN_name, oN_attribute_name):
    obj = context.object
    mesh = obj.data
    
    if bpy.app.version < (4, 1, 0):
        mesh.calc_normals_split()
    
    oN_attribute = mesh.attributes[oN_attribute_name]
    grouped_oN = group_attribute_values(oN_attribute, 3)
    dN_attribute = mesh.attributes[dN_name]
    grouped_dN = group_attribute_values(dN_attribute, 3)

    if oN_attribute.domain == 'POINT':
        grouped_oN = populate_corner_attribute_values(mesh, grouped_oN)
    if dN_attribute.domain == 'POINT':
        grouped_dN = populate_corner_attribute_values(mesh, grouped_dN)

    if dN_attribute.domain == 'POINT':
        mesh.attributes.remove(dN_attribute)
        mesh.attributes.new(dN_name, 'FLOAT_VECTOR', 'CORNER')

    for loop in mesh.loops:
        morph_normal = Vector(grouped_oN[loop.index]) + Vector(grouped_dN[loop.index])
        new_delta = morph_normal - mesh.corner_normals[loop.index].vector
        mesh.attributes[dN_name].data[loop.index].vector = new_delta

    obj.data.update() 