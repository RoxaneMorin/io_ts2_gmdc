#-------------------------------------------------------------------------------

__all__ = ['original_to_current_normals', 'current_to_original_normals', 'add_dN_to_current', 'original_plus_dN_to_current', 'retarget_dN_to_current_normals', 'set_dN_from_current_vs_original', 'clear_dNorms', 'switch_vector_attribute_domain']

#-------------------------------------------------------------------------------


import bpy
from bpy import context, types, props
from mathutils import Vector

from ._attribute_helpers import (
    clamp_vector,
    group_attribute_values,
    flatten_attribute_values,
    populate_corner_attribute_values,
    populate_point_attribute_values
    )


# ORIGINAL NORMALS

# SET CURRENT
def original_to_current_normals(context, oN_attribute_name, masking_mode, vertex_group_name):
    obj = context.object
    mesh = obj.data

    if bpy.app.version < (4, 1, 0):
        mesh.calc_normals_split()

    oN_attribute = mesh.attributes[oN_attribute_name]
    grouped_oN = group_attribute_values(oN_attribute, 'vector', 3)
    if oN_attribute.domain == 'POINT':
        grouped_oN = populate_corner_attribute_values(mesh, grouped_oN)

    if masking_mode != "None" and vertex_group_name != "None":
        vertex_group = obj.vertex_groups[vertex_group_name]

        for loop in mesh.loops:
            original_normals = Vector(grouped_oN[loop.index])
            current_normals = mesh.corner_normals[loop.index].vector

            if masking_mode == "Only":
                try:
                    vertex_weight = vertex_group.weight(loop.vertex_index)
                    blended_normals = current_normals.lerp(original_normals, vertex_weight)
                    grouped_oN[loop.index] = blended_normals
                except:
                    grouped_oN[loop.index] = current_normals

            elif masking_mode == "Excluding":
                try:
                    vertex_weight = vertex_group.weight(loop.vertex_index)
                    blended_normals = original_normals.lerp(current_normals, vertex_weight)
                    grouped_oN[loop.index] = blended_normals
                except:
                    pass

    mesh.normals_split_custom_set(grouped_oN)

    obj.data.update()


# SAVE ATTRIBUTE
def current_to_original_normals(context, oN_attribute_name, masking_mode, vertex_group_name):
    obj = context.object
    mesh = obj.data
    
    if bpy.app.version < (4, 1, 0):
        mesh.calc_normals_split()

    grouped_cN = [normal.vector for normal in mesh.corner_normals]

    if oN_attribute_name in mesh.attributes:
        oN_attribute = mesh.attributes[oN_attribute_name]

        if masking_mode != "None" and vertex_group_name != "None":
            vertex_group = obj.vertex_groups[vertex_group_name]

            grouped_oN = group_attribute_values(oN_attribute, 'vector', 3)
            if oN_attribute.domain == 'POINT':
                grouped_oN = populate_corner_attribute_values(mesh, grouped_oN)

            for loop in mesh.loops:
                original_normals = Vector(grouped_oN[loop.index])
                current_normals = grouped_cN[loop.index]

                if masking_mode == "Only":
                    try:
                        vertex_weight = vertex_group.weight(loop.vertex_index)
                        blended_normals = original_normals.lerp(current_normals, vertex_weight)
                        grouped_cN[loop.index] = blended_normals
                    except:
                        grouped_cN[loop.index] = original_normals

                elif masking_mode == "Excluding":
                    try:
                        vertex_weight = vertex_group.weight(loop.vertex_index)
                        blended_normals = current_normals.lerp(original_normals, vertex_weight)
                        grouped_cN[loop.index] = blended_normals
                    except:
                        pass

        mesh.attributes.remove(oN_attribute)
    
    mesh.attributes.new(oN_attribute_name, 'FLOAT_VECTOR', 'CORNER')

    flat_cN = flatten_attribute_values(grouped_cN)
    mesh.attributes[oN_attribute_name].data.foreach_set('vector', flat_cN)

    obj.data.update()



# DNORMS

# SET CURRENT
def add_dN_to_current(context, dN_name, masking_mode, vertex_group_name):
    obj = context.object
    mesh = obj.data
    
    if bpy.app.version < (4, 1, 0):
        mesh.calc_normals_split()

    grouped_cN = [normal.vector for normal in mesh.corner_normals]

    dN_attribute = mesh.attributes[dN_name]
    grouped_dN = group_attribute_values(dN_attribute, 'vector', 3)
    if dN_attribute.domain == 'POINT':
        grouped_dN = populate_corner_attribute_values(mesh, grouped_dN)

    if masking_mode != "None" and vertex_group_name != "None":
        vertex_group = obj.vertex_groups[vertex_group_name]

    resulting_normals = []
    for loop in mesh.loops:
        current_normals = grouped_cN[loop.index]
        morph_normals = Vector(grouped_dN[loop.index])
        blended_normals = current_normals + morph_normals

        if masking_mode == "Only":
            try:
                vertex_weight = vertex_group.weight(loop.vertex_index)
                blended_normals = current_normals.lerp(blended_normals, vertex_weight)
            except:
                blended_normals = current_normals

        elif masking_mode == "Excluding":
            try:
                vertex_weight = vertex_group.weight(loop.vertex_index)
                blended_normals = blended_normals.lerp(current_normals, vertex_weight)
            except:
                pass

        resulting_normals.append(clamp_vector(blended_normals, -1.0, 1.0))

    mesh.normals_split_custom_set(resulting_normals)

    obj.data.update()


def original_plus_dN_to_current(context, dN_name, oN_attribute_name, masking_mode, vertex_group_name):
    obj = context.object
    mesh = obj.data
    
    if bpy.app.version < (4, 1, 0):
        mesh.calc_normals_split()
    
    oN_attribute = mesh.attributes[oN_attribute_name]
    grouped_oN = group_attribute_values(oN_attribute, 'vector', 3)
    if oN_attribute.domain == 'POINT':
            grouped_oN = populate_corner_attribute_values(mesh, grouped_oN)
    dN_attribute = mesh.attributes[dN_name]
    grouped_dN = group_attribute_values(dN_attribute, 'vector', 3)
    if dN_attribute.domain == 'POINT':
            grouped_dN = populate_corner_attribute_values(mesh, grouped_dN)

    resulting_normals = [clamp_vector(Vector(oNormal) + Vector(dNormal), -1.0, 1.0) for oNormal, dNormal in zip(grouped_oN, grouped_dN)]

    if masking_mode != "None" and vertex_group_name != "None":
        vertex_group = obj.vertex_groups[vertex_group_name]

        grouped_cN = [normal.vector for normal in mesh.corner_normals]

        for loop in mesh.loops:
            current_normals = grouped_cN[loop.index]
            new_normals = resulting_normals[loop.index]

            if masking_mode == "Only":
                try:
                    vertex_weight = vertex_group.weight(loop.vertex_index)
                    blended_normals = current_normals.lerp(new_normals, vertex_weight)
                    resulting_normals[loop.index] = blended_normals
                except:
                    resulting_normals[loop.index] = current_normals

            elif masking_mode == "Excluding":
                try:
                    vertex_weight = vertex_group.weight(loop.vertex_index)
                    blended_normals = new_normals.lerp(current_normals, vertex_weight)
                    resulting_normals[loop.index] = blended_normals
                except:
                    pass

    mesh.normals_split_custom_set(resulting_normals)

    obj.data.update()


# SAVE ATTRIBUTE
def set_dN_from_current_vs_original(context, dN_name, oN_attribute_name, masking_mode, vertex_group_name):
    obj = context.object
    mesh = obj.data
    
    if bpy.app.version < (4, 1, 0):
        mesh.calc_normals_split()

    grouped_cN = [normal.vector for normal in mesh.corner_normals]

    oN_attribute = mesh.attributes[oN_attribute_name]
    grouped_oN = group_attribute_values(oN_attribute, 'vector', 3)
    if oN_attribute.domain == 'POINT':
        grouped_oN = populate_corner_attribute_values(mesh, grouped_oN)

    resulting_deltas = [cNormal - Vector(oNormal) for cNormal, oNormal in zip(grouped_cN, grouped_oN)]

    if dN_name in mesh.attributes:
        dN_attribute = mesh.attributes[dN_name]

        if masking_mode != "None" and vertex_group_name != "None":
            vertex_group = obj.vertex_groups[vertex_group_name]

            grouped_dN = group_attribute_values(dN_attribute, 'vector', 3)
            if dN_attribute.domain == 'POINT':
                grouped_dN = populate_corner_attribute_values(mesh, grouped_dN)

            for loop in mesh.loops:
                original_delta = Vector(grouped_dN[loop.index])
                new_delta = resulting_deltas[loop.index]

                if masking_mode == "Only":
                    try:
                        vertex_weight = vertex_group.weight(loop.vertex_index)
                        blended_delta = original_delta.lerp(new_delta, vertex_weight)
                        resulting_deltas[loop.index] = blended_delta
                    except:
                        resulting_deltas[loop.index] = original_delta

                elif masking_mode == "Excluding":
                    try:
                        vertex_weight = vertex_group.weight(loop.vertex_index)
                        blended_delta = new_delta.lerp(original_delta, vertex_weight)
                        resulting_deltas[loop.index] = blended_delta
                    except:
                        pass

        mesh.attributes.remove(mesh.attributes[dN_name])

    mesh.attributes.new(dN_name, 'FLOAT_VECTOR', 'CORNER')

    flat_deltas = flatten_attribute_values(resulting_deltas)
    mesh.attributes[dN_name].data.foreach_set('vector', flat_deltas)

    obj.data.update()


# RETARGET
def retarget_dN_to_current_normals(context, dN_name, oN_attribute_name, masking_mode, vertex_group_name):
    obj = context.object
    mesh = obj.data
    
    if bpy.app.version < (4, 1, 0):
        mesh.calc_normals_split()

    grouped_cN = [normal.vector for normal in mesh.corner_normals]

    oN_attribute = mesh.attributes[oN_attribute_name]
    grouped_oN = group_attribute_values(oN_attribute, 'vector', 3)
    if oN_attribute.domain == 'POINT':
        grouped_oN = populate_corner_attribute_values(mesh, grouped_oN)
    dN_attribute = mesh.attributes[dN_name]
    grouped_dN = group_attribute_values(dN_attribute, 'vector', 3)
    if dN_attribute.domain == 'POINT':
        grouped_dN = populate_corner_attribute_values(mesh, grouped_dN)

    resulting_normals = [Vector(oNormal) + Vector(dNormal) for oNormal, dNormal in zip(grouped_oN, grouped_dN)] 
    resulting_deltas = [rNormal - cNormal for cNormal, rNormal in zip(grouped_cN, resulting_normals)] 

    if masking_mode != "None" and vertex_group_name != "None":
        vertex_group = obj.vertex_groups[vertex_group_name]

        for loop in mesh.loops:
            original_delta = Vector(grouped_dN[loop.index])
            new_delta = resulting_deltas[loop.index]

            if masking_mode == "Only":
                try:
                    vertex_weight = vertex_group.weight(loop.vertex_index)
                    blended_delta = original_delta.lerp(new_delta, vertex_weight)
                    resulting_deltas[loop.index] = blended_delta
                except:
                    resulting_deltas[loop.index] = original_delta

            elif masking_mode == "Excluding":
                try:
                    vertex_weight = vertex_group.weight(loop.vertex_index)
                    blended_delta = new_delta.lerp(original_delta, vertex_weight)
                    resulting_deltas[loop.index] = blended_delta
                except:
                    pass

    flat_deltas = flatten_attribute_values(resulting_deltas)
    if dN_attribute.domain == 'POINT':
        mesh.attributes.remove(dN_attribute)
        mesh.attributes.new(dN_name, 'FLOAT_VECTOR', 'CORNER')
    mesh.attributes[dN_name].data.foreach_set('vector', flat_deltas)

    obj.data.update()


# CLEAR
def clear_dNorms(context, dN_name, masking_mode, vertex_group_name):
    obj = context.object
    mesh = obj.data

    if masking_mode != "None" and vertex_group_name != "None":
        vertex_group = obj.vertex_groups[vertex_group_name]

        dN_attribute = mesh.attributes[dN_name]
        grouped_dN = group_attribute_values(dN_attribute, 'vector', 3)
        if dN_attribute.domain == 'POINT':
            grouped_dN = populate_corner_attribute_values(mesh, grouped_dN)

        zero_vector = Vector([0.0, 0.0, 0.0])
        resulting_deltas = [zero_vector] * len(mesh.loops)
        for loop in mesh.loops:
            original_delta = Vector(grouped_dN[loop.index])

            if masking_mode == "Only":
                try:
                    vertex_weight = vertex_group.weight(loop.vertex_index)
                    blended_delta = original_delta.lerp(zero_vector, vertex_weight)
                    resulting_deltas[loop.index] = blended_delta
                except:
                    resulting_deltas[loop.index] = original_delta

            elif masking_mode == "Excluding":
                try:
                    vertex_weight = vertex_group.weight(loop.vertex_index)
                    blended_delta = zero_vector.lerp(original_delta, vertex_weight)
                    resulting_deltas[loop.index] = blended_delta
                except:
                    pass

        flat_deltas = flatten_attribute_values(resulting_deltas)
        mesh.attributes[dN_name].data.foreach_set('vector', flat_deltas)

    else:
        # Simply generate and assign an array of zeroes of the same length.
        zeroes = [0] * len(mesh.attributes[dN_name].data) * 3
        mesh.attributes[dN_name].data.foreach_set('vector', zeroes)

    obj.data.update()


# DOMAIN SWITCH
def switch_vector_attribute_domain(context, attribute_name):
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