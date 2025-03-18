#-------------------------------------------------------------------------------

__all__ = ['original_to_current_normals', 'current_to_original_normals', 'add_dN_to_current', 'original_plus_dN_to_current', 'retarget_dN_to_current_normals', 'set_dN_from_current_vs_original', 'clear_dNorms', 'transfer_attribute_via_topology', 'transfer_attribute_via_nearest_vertex', 'transfer_attribute_via_nearest_surface', 'switch_vector_attribute_domain']

#-------------------------------------------------------------------------------


import bpy
from bpy import context, types, props
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
from mathutils.interpolate import poly_3d_calc

from ._attribute_helpers import (
    group_attribute_values,
    flatten_attribute_values,
    populate_corner_attribute_values,
    populate_point_attribute_values,
    zero_out_small_vector
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

        resulting_normals.append(blended_normals.normalized())

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

    resulting_normals = [(Vector(oNormal) + Vector(dNormal)).normalized() for oNormal, dNormal in zip(grouped_oN, grouped_dN)]

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

    # Ensure that the deltas don't have uselessly small values.
    resulting_deltas = [zero_out_small_vector(cNormal - Vector(oNormal), 0.001) for cNormal, oNormal in zip(grouped_cN, grouped_oN)]

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
        if dN_attribute.domain == 'POINT':
            mesh.attributes.remove(dN_attribute)
            mesh.attributes.new(dN_name, 'FLOAT_VECTOR', 'CORNER')
        mesh.attributes[dN_name].data.foreach_set('vector', flat_deltas)

    else:
        # Simply generate and assign an array of zeroes of the same length.
        zeroes = [0] * len(mesh.attributes[dN_name].data) * 3
        mesh.attributes[dN_name].data.foreach_set('vector', zeroes)

    obj.data.update()


# ATTRIBUTE TRANSFER

# SUBFUNCTION - RETARGETING
def handle_retargeting_via_topology(source_mesh, dest_mesh, retargeting_mode_source, retargeting_mode_dest, grouped_source_attribute, oN_attribute_name):

    if bpy.app.version < (4, 1, 0):
        source_mesh.calc_normals_split()
        dest_mesh.calc_normals_split()

    if retargeting_mode_source == "Original Normals":
        source_oN_attribute = source_mesh.attributes[oN_attribute_name]
        grouped_sourceN = group_attribute_values(source_oN_attribute, 'vector', 3)
        if source_oN_attribute.domain == 'POINT':
           grouped_sourceN = populate_corner_attribute_values(source_mesh, grouped_sourceN)
    elif retargeting_mode_source == "Current Normals":
        grouped_sourceN = [normal.vector for normal in source_mesh.corner_normals]

    if retargeting_mode_dest == "Original Normals":
        dest_oN_attribute = dest_mesh.attributes[oN_attribute_name]
        grouped_destN = group_attribute_values(dest_oN_attribute, 'vector', 3)
        if dest_oN_attribute.domain == 'POINT':
           grouped_destN = populate_corner_attribute_values(dest_mesh, grouped_destN)
    elif retargeting_mode_dest == "Current Normals":
        grouped_destN = [normal.vector for normal in dest_mesh.corner_normals]

    resulting_source_normals = [Vector(base) + Vector(attribute) for base, attribute in zip(grouped_sourceN, grouped_source_attribute)] 
    retargeted_attribute = [rNormal - Vector(destNormal) for destNormal, rNormal in zip(grouped_destN, resulting_source_normals)] 

    return retargeted_attribute

def handle_retargeting_via_nearest_vertex (source_mesh, dest_mesh, retargeting_mode_source, retargeting_mode_dest, grouped_source_attribute, vertex_mapping, oN_attribute_name):

    if bpy.app.version < (4, 1, 0):
        source_mesh.calc_normals_split()
        dest_mesh.calc_normals_split()

    if retargeting_mode_source == "Original Normals":
        source_oN_attribute = source_mesh.attributes[oN_attribute_name]
        grouped_sourceN = group_attribute_values(source_oN_attribute, 'vector', 3)
        if source_oN_attribute.domain == 'CORNER':
           grouped_sourceN = populate_point_attribute_values(source_mesh, grouped_sourceN)
    elif retargeting_mode_source == "Current Normals":
        grouped_sourceN = [normal.vector for normal in source_mesh.corner_normals]
        grouped_sourceN = populate_point_attribute_values(source_mesh, grouped_sourceN)
    grouped_sourceN = [grouped_sourceN[i] for i in vertex_mapping]
    grouped_sourceN_plus_dN = [Vector(sourceN) + Vector(dN) for sourceN, dN in zip(grouped_sourceN, grouped_source_attribute)] 

    if retargeting_mode_dest == "Original Normals":
        dest_oN_attribute = dest_mesh.attributes[oN_attribute_name]
        grouped_destN = group_attribute_values(dest_oN_attribute, 'vector', 3)
        if dest_oN_attribute.domain == 'CORNER':
           grouped_destN = populate_point_attribute_values(dest_mesh, grouped_destN)
    elif retargeting_mode_dest == "Current Normals":
        grouped_destN = [normal.vector for normal in dest_mesh.corner_normals]
        grouped_destN = populate_point_attribute_values(dest_mesh, grouped_destN)

    retargeted_attribute = [sourceNormal - Vector(destNormal) for destNormal, sourceNormal in zip(grouped_destN, grouped_sourceN_plus_dN)] 

    return retargeted_attribute

def handle_retargeting_via_nearest_surface(source_mesh, dest_mesh, retargeting_mode_source, retargeting_mode_dest, grouped_source_attribute, vertex_mapping, oN_attribute_name):

    if bpy.app.version < (4, 1, 0):
        source_mesh.calc_normals_split()
        dest_mesh.calc_normals_split()

    if retargeting_mode_source == "Original Normals":
        source_oN_attribute = source_mesh.attributes[oN_attribute_name]
        grouped_sourceN = group_attribute_values(source_oN_attribute, 'vector', 3)
        if source_oN_attribute.domain == 'POINT':
           grouped_sourceN = populate_corner_attribute_values(source_mesh, grouped_sourceN)
    elif retargeting_mode_source == "Current Normals":
        grouped_sourceN = [normal.vector for normal in source_mesh.corner_normals]

    interpolated_sourceN = []
    for vertex in dest_mesh.vertices:
        indices = vertex_mapping[vertex.index][0]
        weights = vertex_mapping[vertex.index][1]

        interpolated_value = Vector([0.0, 0.0, 0.0])
        for i, w in zip(indices, weights):
            interpolated_value += Vector(grouped_sourceN[i]) * w
        interpolated_sourceN.append(interpolated_value)

    grouped_sourceN_plus_dN = [sourceN + Vector(dN) for sourceN, dN in zip(interpolated_sourceN, grouped_source_attribute)] 

    if retargeting_mode_dest == "Original Normals":
        dest_oN_attribute = dest_mesh.attributes[oN_attribute_name]
        grouped_destN = group_attribute_values(dest_oN_attribute, 'vector', 3)
        if dest_oN_attribute.domain == 'CORNER':
           grouped_destN = populate_point_attribute_values(dest_mesh, grouped_destN)
    elif retargeting_mode_dest == "Current Normals":
        grouped_destN = [normal.vector for normal in dest_mesh.corner_normals]
        grouped_destN = populate_point_attribute_values(dest_mesh, grouped_destN)

    retargeted_attribute = [sourceNormal - Vector(destNormal) for destNormal, sourceNormal in zip(grouped_destN, grouped_sourceN_plus_dN)] 

    return retargeted_attribute


# SUBFUNCTION - MASKING
def handle_masking_via_topology(dest_obj, dest_mesh, masking_mode, vertex_group_name, target_attribute_name, grouped_source_attribute):

    my_attribute = dest_mesh.attributes[target_attribute_name]
    grouped_my_attribute = group_attribute_values(my_attribute, 'vector', 3)

    if my_attribute.domain == 'POINT':
        grouped_my_attribute = populate_corner_attribute_values(dest_mesh, grouped_my_attribute)

    vertex_group = dest_obj.vertex_groups[vertex_group_name]

    for loop in dest_mesh.loops:
        source_value = Vector(grouped_source_attribute[loop.index])
        my_value = Vector(grouped_my_attribute[loop.index])

        if masking_mode == "Only":
            try:
                vertex_weight = vertex_group.weight(loop.vertex_index)
                blended_value = my_value.lerp(source_value, vertex_weight)
                grouped_source_attribute[loop.index] = blended_value
            except:
                grouped_source_attribute[loop.index] = my_value

        elif masking_mode == "Excluding":
            try:
                vertex_weight = vertex_group.weight(loop.vertex_index)
                blended_value = source_value.lerp(my_value, vertex_weight)
                grouped_source_attribute[loop.index] = blended_value
            except:
                pass

    return grouped_source_attribute

def handle_masking_per_vertex(dest_obj, dest_mesh, masking_mode, vertex_group_name, dest_attribute_name, grouped_source_attribute):

    my_attribute = dest_mesh.attributes[dest_attribute_name]
    grouped_my_attribute = group_attribute_values(my_attribute, 'vector', 3)
    if my_attribute.domain == 'CORNER':
        grouped_my_attribute = populate_point_attribute_values(dest_mesh, grouped_my_attribute)

    vertex_group = dest_obj.vertex_groups[vertex_group_name]

    for vertex in dest_mesh.vertices:
        collected_value = Vector(grouped_source_attribute[vertex.index])
        my_value = Vector(grouped_my_attribute[vertex.index])

        if masking_mode == "Only":
            try:
                vertex_weight = vertex_group.weight(vertex.index)
                blended_value = my_value.lerp(collected_value, vertex_weight)
                grouped_source_attribute[vertex.index] = blended_value
            except:
                grouped_source_attribute[vertex.index] = my_value

        elif masking_mode == "Excluding":
            try:
                vertex_weight = vertex_group.weight(vertex.index)
                blended_value = collected_value.lerp(my_value, vertex_weight)
                grouped_source_attribute[vertex.index] = blended_value
            except:
                pass

    return grouped_source_attribute


# TOPOLOGY
def transfer_attribute_via_topology(context, source_mesh, source_attribute_name, dest_attribute_name, oN_attribute_name, masking_mode, vertex_group_name, retargeting_mode_source, retargeting_mode_dest):
    dest_obj = context.object
    dest_mesh = dest_obj.data

    source_attribute = source_mesh.attributes[source_attribute_name]
    grouped_source_attribute = group_attribute_values(source_attribute, 'vector', 3)
    if source_attribute.domain == 'POINT':
        grouped_source_attribute = populate_corner_attribute_values(dest_mesh, grouped_source_attribute)

    if retargeting_mode_dest != "None" and source_attribute_name != oN_attribute_name:
        grouped_source_attribute = handle_retargeting_via_topology(source_mesh, dest_mesh, retargeting_mode_source, retargeting_mode_dest, grouped_source_attribute, oN_attribute_name)

    if masking_mode != "None" and vertex_group_name != "None" and source_attribute_name in dest_mesh.attributes:
        grouped_source_attribute = handle_masking_via_topology(dest_obj, dest_mesh, masking_mode, vertex_group_name, source_attribute_name, grouped_source_attribute)
                
    flat_source_attribute = flatten_attribute_values(grouped_source_attribute)
    if dest_attribute_name in dest_mesh.attributes:
       dest_mesh.attributes.remove(dest_mesh.attributes[dest_attribute_name])
    dest_mesh.attributes.new(dest_attribute_name, 'FLOAT_VECTOR', 'CORNER')
    dest_mesh.attributes[dest_attribute_name].data.foreach_set('vector', flat_source_attribute)

    dest_obj.data.update()

# NEAREST VERTEX
def transfer_attribute_via_nearest_vertex(context, source_obj, source_attribute_name, dest_attribute_name, oN_attribute_name, masking_mode, vertex_group_name, retargeting_mode_source, retargeting_mode_dest):
    dest_obj = context.object
    dest_mesh = dest_obj.data

    source_mesh = source_obj.data

    source_attribute = source_mesh.attributes[source_attribute_name]
    grouped_source_attribute = group_attribute_values(source_attribute, 'vector', 3)
    if source_attribute.domain == 'CORNER':
        grouped_source_attribute = populate_point_attribute_values(source_mesh, grouped_source_attribute)

    # Build the search tree.
    tree_size = len(source_mesh.vertices)
    kd_tree = KDTree(tree_size)
    for vertex in source_mesh.vertices:
        world_space_pos = source_obj.matrix_world @ vertex.co
        kd_tree.insert(world_space_pos, vertex.index)
    kd_tree.balance()

    collected_attributes = []
    vertex_mapping = []
    for vertex in dest_mesh.vertices:
        source_position, source_index, source_distance = kd_tree.find(vertex.co)
        attribute_at_vertex = grouped_source_attribute[source_index]
        collected_attributes.append(attribute_at_vertex)
        vertex_mapping.append(source_index)

    if retargeting_mode_dest != "None" and source_attribute_name != oN_attribute_name:
        collected_attributes = handle_retargeting_via_nearest_vertex(source_mesh, dest_mesh, retargeting_mode_source, retargeting_mode_dest, collected_attributes, vertex_mapping, oN_attribute_name)

    if masking_mode != "None" and vertex_group_name != "None" and dest_attribute_name in dest_mesh.attributes:
        collected_attributes = handle_masking_per_vertex(dest_obj, dest_mesh, masking_mode, vertex_group_name, dest_attribute_name, collected_attributes)
    
    flat_collected_attribute = flatten_attribute_values(collected_attributes)
    if dest_attribute_name in dest_mesh.attributes:
       dest_mesh.attributes.remove(dest_mesh.attributes[dest_attribute_name])
    dest_mesh.attributes.new(dest_attribute_name, 'FLOAT_VECTOR', 'POINT')
    dest_mesh.attributes[dest_attribute_name].data.foreach_set('vector', flat_collected_attribute)

    dest_obj.data.update()

# NEAREST SURFACE / POINT ON FACE
def transfer_attribute_via_nearest_surface(context, source_obj, source_attribute_name, dest_attribute_name, oN_attribute_name, masking_mode, vertex_group_name, retargeting_mode_source, retargeting_mode_dest):
    dest_obj = context.object
    dest_mesh = dest_obj.data
    source_mesh = source_obj.data

    source_attribute = source_mesh.attributes[source_attribute_name]
    grouped_source_attribute = group_attribute_values(source_attribute, 'vector', 3)
    if source_attribute.domain == 'POINT':
        grouped_source_attribute = populate_corner_attribute_values(source_mesh, grouped_source_attribute)

    # Build the search tree.
    bhv_tree = BVHTree.FromObject(source_obj, context.evaluated_depsgraph_get())

    collected_attributes = []
    vertex_mapping = []
    for vertex in dest_mesh.vertices:
        source_position, source_normal, source_index, source_distance = bhv_tree.find_nearest(vertex.co)

        indices = source_mesh.polygons[source_index].loop_indices
        vertices = []
        for i in source_mesh.polygons[source_index].vertices:
            vertices.append(source_mesh.vertices[i].co)    

        weights = poly_3d_calc(vertices, source_position)

        interpolated_value = Vector([0.0, 0.0, 0.0])
        for i, w in zip(indices, weights):
            interpolated_value += Vector(grouped_source_attribute[i]) * w

        collected_attributes.append(interpolated_value)
        vertex_mapping.append((indices, weights))

    if retargeting_mode_dest != "None" and source_attribute_name != oN_attribute_name:
        collected_attributes = handle_retargeting_via_nearest_surface(source_mesh, dest_mesh, retargeting_mode_source, retargeting_mode_dest, collected_attributes, vertex_mapping, oN_attribute_name)

    if masking_mode != "None" and vertex_group_name != "None" and dest_attribute_name in dest_mesh.attributes:
        collected_attributes = handle_masking_per_vertex(dest_obj, dest_mesh, masking_mode, vertex_group_name, dest_attribute_name, collected_attributes)

    flat_collected_attribute = flatten_attribute_values(collected_attributes)
    if dest_attribute_name in dest_mesh.attributes:
       dest_mesh.attributes.remove(dest_mesh.attributes[dest_attribute_name])
    dest_mesh.attributes.new(dest_attribute_name, 'FLOAT_VECTOR', 'POINT')
    dest_mesh.attributes[dest_attribute_name].data.foreach_set('vector', flat_collected_attribute)

    dest_obj.data.update()


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