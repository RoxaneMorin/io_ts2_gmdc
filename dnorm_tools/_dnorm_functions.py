#-------------------------------------------------------------------------------

__all__ = ['original_to_current_normals', 'current_to_original_normals', 'add_dN_to_current', 'original_plus_dN_to_current', 'retarget_dN_to_current_normals', 'set_dN_from_current_vs_original', 'clear_dNorms', 'clear_dNorms_for_vertex_group', 'clear_dNorms_excluding_vertex_group', 'switch_dN_domain']

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


# ORIGINAL NORMALS

# SET CURRENT
def original_to_current_normals(context, oN_attribute_name):
    obj = context.object
    mesh = obj.data

    if bpy.app.version < (4, 1, 0):
        mesh.calc_normals_split()

    oN_attribute = mesh.attributes[oN_attribute_name]
    grouped_oN = group_attribute_values(oN_attribute, 'vector', 3)
    
    if oN_attribute.domain == 'POINT':
        mesh.normals_split_custom_set_from_vertices(grouped_oN)
    elif oN_attribute.domain == 'CORNER':
        mesh.normals_split_custom_set(grouped_oN)

    obj.data.update()


# SAVE ATTRIBUTE
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

# SET CURRENT
def add_dN_to_current(context, dN_name):
    obj = context.object
    mesh = obj.data
    
    if bpy.app.version < (4, 1, 0):
        mesh.calc_normals_split()

    dN_attribute = mesh.attributes[dN_name]
    grouped_dN = group_attribute_values(dN_attribute, 'vector', 3)

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
    grouped_oN = group_attribute_values(oN_attribute, 'vector', 3)
    dN_attribute = mesh.attributes[dN_name]
    grouped_dN = group_attribute_values(dN_attribute, 'vector', 3)

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


# SAVE ATTRIBUTE
def set_dN_from_current_vs_original(context, dN_name, oN_attribute_name):
    obj = context.object
    mesh = obj.data
    
    if bpy.app.version < (4, 1, 0):
        mesh.calc_normals_split()

    if dN_name in mesh.attributes:
        mesh.attributes.remove(mesh.attributes[dN_name])
    mesh.attributes.new(dN_name, 'FLOAT_VECTOR', 'CORNER')

    oN_attribute = mesh.attributes[oN_attribute_name]

    if oN_attribute.domain == 'POINT':
        for loop in mesh.loops:
            current_normal = mesh.corner_normals[loop.index].vector
            original_normal = oN_attribute.data[loop.vertex_index].vector
            new_delta = current_normal - original_normal
            mesh.attributes[dN_name].data[loop.index].vector = new_delta       

    elif oN_attribute.domain == 'CORNER':
        for loop in mesh.loops:
            current_normal = mesh.corner_normals[loop.index].vector
            original_normal = oN_attribute.data[loop.index].vector
            new_delta = current_normal - original_normal
            mesh.attributes[dN_name].data[loop.index].vector = new_delta

    obj.data.update()


# EDIT
def retarget_dN_to_current_normals(context, dN_name, oN_attribute_name):
    obj = context.object
    mesh = obj.data
    
    if bpy.app.version < (4, 1, 0):
        mesh.calc_normals_split()
    
    # TODO: make sure it works okay. Have encountered weirdness while testing.

    oN_attribute = mesh.attributes[oN_attribute_name]
    grouped_oN = group_attribute_values(oN_attribute, 'vector', 3)
    dN_attribute = mesh.attributes[dN_name]
    grouped_dN = group_attribute_values(dN_attribute, 'vector', 3)

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


# CLEAR
def clear_dNorms(context, dN_name):
    obj = context.object
    mesh = obj.data

    # Simply generate and assign an array of zeroes of the same length.
    zeroes = [0] * len(mesh.attributes[dN_name].data) * 3
    mesh.attributes[dN_name].data.foreach_set('vector', zeroes)

    obj.data.update()

def clear_dNorms_for_vertex_group(context, dN_name, vertex_group_name):
    obj = context.object
    mesh = obj.data

    dN_attribute = mesh.attributes[dN_name]
    vertex_group = obj.vertex_groups[vertex_group_name]

    if dN_attribute.domain == 'POINT':
        for vertex in mesh.vertices:
            try:
                vertex_dN = dN_attribute.data[vertex.index].vector
                dN_weight = 1 - vertex_group.weight(vertex.index)
                new_dN = [value * dN_weight for value in vertex_dN]
                mesh.attributes[dN_name].data[vertex.index].vector = Vector(new_dN)
            except:
                pass

    elif dN_attribute.domain == 'CORNER':
        for loop in mesh.loops:
            try:
                vertex_dN = dN_attribute.data[loop.index].vector
                dN_weight = 1 - vertex_group.weight(loop.vertex_index)
                new_dN = [value * dN_weight for value in vertex_dN]
                mesh.attributes[dN_name].data[loop.index].vector = Vector(new_dN)
            except:
                pass

    obj.data.update()


def clear_dNorms_excluding_vertex_group(context, dN_name, vertex_group_name):
    obj = context.object
    mesh = obj.data

    dN_attribute = mesh.attributes[dN_name]
    vertex_group = obj.vertex_groups[vertex_group_name]

    if dN_attribute.domain == 'POINT':
        for vertex in mesh.vertices:
            try:
                vertex_dN = dN_attribute.data[vertex.index].vector
                dN_weight = vertex_group.weight(vertex.index)
                new_dN = [value * dN_weight for value in vertex_dN]
                mesh.attributes[dN_name].data[vertex.index].vector = Vector(new_dN)
            except:
                mesh.attributes[dN_name].data[vertex.index].vector = Vector([0.0, 0.0, 0.0])

    elif dN_attribute.domain == 'CORNER':
        for loop in mesh.loops:
            try:
                vertex_dN = dN_attribute.data[loop.index].vector
                dN_weight = vertex_group.weight(loop.vertex_index)
                new_dN = [value * dN_weight for value in vertex_dN]
                mesh.attributes[dN_name].data[loop.index].vector = Vector(new_dN)
            except:
                mesh.attributes[dN_name].data[loop.index].vector = Vector([0.0, 0.0, 0.0])
    
    obj.data.update()




def switch_dN_domain(context, attribute_name):
    obj = context.object
    mesh = obj.data

    attribute = mesh.attributes[attribute_name]
    grouped_attribute = group_attribute_values(attribute, 'vector', 3)

    if attribute.domain == 'POINT':
        corner_attribute = populate_corner_attribute_values(mesh, grouped_attribute)
        flat_corner_attribute = flatten_attribute_values(corner_attribute)

        mesh.attributes.remove(attribute)
        mesh.attributes.new(attribute_name, 'FLOAT_VECTOR', 'CORNER')
        mesh.attributes[attribute_name].data.foreach_set('vector', flat_corner_attribute)

    elif attribute.domain == 'CORNER':
        point_attribute = populate_point_attribute_values(mesh, grouped_attribute)
        flat_point_attribute = flatten_attribute_values(point_attribute)

        mesh.attributes.remove(attribute)
        mesh.attributes.new(attribute_name, 'FLOAT_VECTOR', 'POINT')
        mesh.attributes[attribute_name].data.foreach_set('vector', flat_point_attribute)

    obj.data.update()
    return mesh.attributes[attribute_name].domain