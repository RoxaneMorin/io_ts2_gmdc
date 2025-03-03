#-------------------------------------------------------------------------------

__all__ = ['group_attribute_values', 'flatten_attribute_values', 'populate_corner_attribute_values', 'populate_point_attribute_values']

#-------------------------------------------------------------------------------


def group_attribute_values(attribute, value_type, group_length):
    flat_attribute = [0] * len(attribute.data) * group_length
    attribute.data.foreach_get(value_type, flat_attribute)
    grouped_attribute = [flat_attribute[i:i+group_length] for i in range(0, len(flat_attribute), group_length)]

    return grouped_attribute


def flatten_attribute_values(attribute):
    return [value for sublist in attribute for value in sublist]


def populate_corner_attribute_values(mesh, grouped_point_attribute):
    corner_attribute = []
    for loop in mesh.loops:
        corner_attribute.append(grouped_point_attribute[loop.vertex_index])
    return corner_attribute


def populate_point_attribute_values(mesh, grouped_corner_attribute):
    values_per_vertex = dict()
    for loop in mesh.loops:
        loop_value = grouped_corner_attribute[loop.index]
        if loop.vertex_index in values_per_vertex:
            values_per_vertex[loop.vertex_index].append(loop_value)
        else:
            values_per_vertex[loop.vertex_index] = []
            values_per_vertex[loop.vertex_index].append(loop_value)

    point_attribute = []
    for vertex in mesh.vertices:
        value_count = len(values_per_vertex[vertex.index])
        accumulated_values = [sum(values) for values in zip(*values_per_vertex[vertex.index])]
        new_value = [value/value_count for value in accumulated_values]
        point_attribute.append(new_value)
    return point_attribute
