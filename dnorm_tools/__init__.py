#-------------------------------------------------------------------------------

from ._ntoc_helpers import convert_normal_to_color
from ._attribute_helpers import group_attribute_values, flatten_attribute_values, populate_corner_attribute_values, populate_point_attribute_values
from ._dnorm_functions import original_to_current_normals, current_to_original_normals, add_dN_to_current, original_plus_dN_to_current, retarget_dN_to_current_normals, set_dN_from_current_vs_original, clear_dNorms, clear_dNorms_for_vertex_group, clear_dNorms_excluding_vertex_group, switch_vector_attribute_domain
from ._ntoc_functions import update_currentNtoC, update_oNtoC, update_dNtoC, regenerate_currentNtoC, regenerate_oNtoC, regenerate_all_dNtoCs, regenerate_dNtoC, switch_color_attribute_domain