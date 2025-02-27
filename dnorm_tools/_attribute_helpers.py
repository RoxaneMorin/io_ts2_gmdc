#-------------------------------------------------------------------------------

__all__ = ['group_attribute_values', 'populate_corner_attribute_values']

#-------------------------------------------------------------------------------



def group_attribute_values(attribute, group_length):
    flat_attribute = [0] * len(attribute.data) * group_length
    attribute.data.foreach_get('vector', flat_attribute)
    grouped_attribute = [flat_attribute[i:i+group_length] for i in range(0, len(flat_attribute), group_length)]

    return grouped_attribute


def populate_corner_attribute_values(mesh, point_attribute):
    corner_attribute = []
    for loop in mesh.loops:
        corner_attribute.append(point_attribute[loop.vertex_index])
    return corner_attribute
