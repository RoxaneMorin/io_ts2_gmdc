
import bpy
from bpy import context, types, props
from mathutils import Vector

from .dnorm_tools import (
    original_to_current_normals,
    current_to_original_normals,
    add_dN_to_current,
    original_plus_dN_to_current,
    retarget_dN_to_current_normals,
    set_dN_from_current_vs_original,
    clear_dNorms,
    clear_dNorms_for_vertex_group,
    clear_dNorms_excluding_vertex_group,
    switch_vector_attribute_domain,
    update_currentNtoC,
    update_oNtoC,
    update_dNtoC,
    regenerate_currentNtoC,
    regenerate_oNtoC,
    regenerate_all_dNtoCs,
    regenerate_dNtoC,
    switch_color_attribute_domain
    )



# GLOBAL PARAMETERS
oN_attribute_name = "OriginalNormals"
currentNtoC_attribute_name = "CurrentNormals_AsColours"
oNtoC_attribute_name = "OriginalNormals_AsColours"
dN_attribute_suffix = "_dN"
dNtoC_attribute_suffix = "_NtoC"



# HELPERS
def get_valid_shape_key_names(context):
    obj = context.object
    if obj and obj.type == 'MESH' and obj.data.shape_keys:
        # Ignore the Basis and :: keys.
        return [key.name for key in obj.data.shape_keys.key_blocks[1:] if key.name != "::"]
    return []

def get_valid_dN_attribute_names(context):
    obj = context.object
    if obj and obj.type == 'MESH':
        mesh = obj.data
        return [attribute.name for attribute in mesh.attributes if dN_attribute_suffix in attribute.name]
    return []

def get_valid_NtoC_attribute_names(context):
    obj = context.object
    if obj and obj.type == 'MESH':
        mesh = obj.data
        return [attribute.name for attribute in mesh.attributes if dNtoC_attribute_suffix in attribute.name]
    return []


def has_oN_attribute(context):
    obj = context.id_data
    if obj and obj.type == 'MESH':
        mesh = obj.data
        return oN_attribute_name in mesh.attributes
    return False

def has_oNtoC_attribute(context):
    obj = context.id_data
    if obj and obj.type == 'MESH':
        mesh = obj.data
        return oNtoC_attribute_name in mesh.attributes
    return False

def has_currentNtoC_attribute(context):
    obj = context.id_data
    if obj and obj.type == 'MESH':
        mesh = obj.data
        return currentNtoC_attribute_name in mesh.attributes
    return False

def has_corresponding_dN_attribute(context, key_name):
     obj = context.object
     if obj and obj.type == 'MESH':
        mesh = obj.data
        dN_attribute_name = key_name + dN_attribute_suffix
        if dN_attribute_name in mesh.attributes:
            return True
     return False

def has_any_dN_attribute(context, key_names):
    obj = context.object
    if obj and obj.type == 'MESH':
        mesh = obj.data
        for key_name in key_names:
            dN_attribute_name = key_name + dN_attribute_suffix
            if dN_attribute_name in mesh.attributes:
                return True
    return False

def has_corresponding_dNtoC_attribute(context, key_name):
     obj = context.object
     if obj and obj.type == 'MESH':
        mesh = obj.data
        dNtoC_attribute_name = key_name + dNtoC_attribute_suffix
        if dNtoC_attribute_name in mesh.attributes:
            return True
     return False

def has_any_dNtoC_attribute(context, key_names):
     obj = context.object
     if obj and obj.type == 'MESH':
        mesh = obj.data
        for key_name in key_names:
            dNtoC_attribute_name = key_name + dNtoC_attribute_suffix
            if dNtoC_attribute_name in mesh.attributes:
                return True
     return False


def populate_shape_key_enum(self, context):
    obj = context.object
    if obj and obj.type == 'MESH' and obj.data.shape_keys:
        # Ignore the Basis and :: keys.
        return [(key.name, key.name, "") for key in obj.data.shape_keys.key_blocks[1:] if key.name != "::"]
    return [("None", "None", "No valid shape keys exist.")]

def populate_vertex_group_enum(self, context):
    groups = [("None", "None", "Do not use a vertex group.")]
    obj = context.object
    if obj and obj.type == 'MESH' and obj.vertex_groups:
        groups.extend([(vertex_group.name, vertex_group.name, "") for vertex_group in obj.vertex_groups])
    return groups

def populate_dN_attribute_enum(self, context):
    obj = context.object
    if obj and obj.type == 'MESH':
        mesh = obj.data
        attributes = [(attribute.name, attribute.name, "") for attribute in mesh.attributes if dN_attribute_suffix in attribute.name]
        if len(attributes) > 0:
            return attributes
    return [("None", "None", "No valid attribute exists.")]

def populate_NtoC_attribute_enum(self, context):
    obj = context.object
    if obj and obj.type == 'MESH':
        mesh = obj.data
        attributes = [(attribute.name, attribute.name, "") for attribute in mesh.attributes if dNtoC_attribute_suffix in attribute.name]
        if len(attributes) > 0:
            return attributes
    return [("None", "None", "No valid attribute exists.")]

def populate_preview_material_targets_enum(self, context):
    obj = context.object
    targets = []

    if obj and obj.type == 'MESH':
        mesh = obj.data
        if oN_attribute_name in mesh.attributes:
            targets.extend([(oN_attribute_name, oN_attribute_name, "The mesh's original normal attribute.")])
        targets.extend([(attribute.name, attribute.name, "") for attribute in mesh.attributes if dN_attribute_suffix in attribute.name])
        if currentNtoC_attribute_name in mesh.attributes:
            targets.extend([(currentNtoC_attribute_name, currentNtoC_attribute_name, "The mesh's current-normals-to-colour attribute.")])
        if oNtoC_attribute_name in mesh.attributes:
            targets.extend([(oNtoC_attribute_name, oNtoC_attribute_name, "The mesh's original-normals-to-colour attribute.")])
        targets.extend([(attribute.name, attribute.name, "") for attribute in mesh.attributes if dNtoC_attribute_suffix in attribute.name])
        
    if len(targets) > 0:
        return targets
    else:
        return [("None", "None", "No valid attribute exists.")]



def is_valid_other_mesh(context, mesh):
    obj = context.id_data
    return mesh != obj.data



def fetch_domain_switch_info_for(obj, attribute_name):
    if attribute_name in obj.data.attributes:
        if obj.data.attributes[attribute_name].domain == 'CORNER':
            return ("Switch Attribute Domain to Vertex", 'NORMALS_VERTEX_FACE')
        else:
            return ("Switch Attribute Domain to Face Corner", 'NORMALS_VERTEX')
    else: 
        return ("Switch Attribute Domain", 'QUESTION')




# PROPERTIES
class dNormsTools_properties(types.PropertyGroup):
    shape_keys_for_dN: props.EnumProperty(name="Shape Keys", items=populate_shape_key_enum)
    shape_keys_for_dNtoC: props.EnumProperty(name="Shape Keys", items=populate_shape_key_enum)
    
    

    oN_attribute: props.BoolProperty(name="Original Normals Attribute", get=has_oN_attribute)
    currentNtoC_attribute: props.BoolProperty(name="Current Normals Colour Attribute", get=has_currentNtoC_attribute)
    oNtoC_attribute: props.BoolProperty(name="Original Normals Colour Attribute", get=has_oNtoC_attribute)

    # Not sure these are useful:
    dN_attributtes: props.EnumProperty(name="Morph Normal Deltas Attributes", items=populate_dN_attribute_enum)
    dNtoC_attributes: props.EnumProperty(name="Morph Normals Colour Attributes", items=populate_NtoC_attribute_enum)
    
    


    vertex_groups: props.EnumProperty(name="Vertex Groups", items=populate_vertex_group_enum)

    preview_material_targets: props.EnumProperty(name="Preview Material Targets", items=populate_preview_material_targets_enum)
        
    preview_material: props.PointerProperty(name="Preview Material", type=types.Material)
    previous_material: props.PointerProperty(name="Previously Active Material", type=types.Material)

    other_mesh : props.PointerProperty(name="Source Mesh", type=types.Mesh, poll=is_valid_other_mesh)
    
    



# OPERATORS

# ORIGINAL NORMALS

# SET CURRENT
class dNormsTools_OT_oN_to_current_normals(bpy.types.Operator):
    bl_idname = "dnorms_tools.on_to_current_normals"
    bl_label = "Copy OriginalNormals Attribute to Current Mesh Normals."
    bl_description = "Set the contents of OriginalNormals as this mesh's current face normals"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        has_oN = context.object.dnorm_props.oN_attribute
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and has_oN
    
    def execute(self, context):
        original_to_current_normals(context, oN_attribute_name)

        print("\nThe current face normals have been replaced by those stored in the attribute '{}'.".format(oN_attribute_name))
        return {'FINISHED'} 


# SAVE ATTRIBUTE
class dNormsTools_OT_current_normals_to_oN(bpy.types.Operator):
    bl_idname = "dnorms_tools.current_normals_to_on"
    bl_label = "Copy Current Mesh Normals to OriginalNormals Attribute"
    bl_description = "Replace the contents of OriginalNormals with this mesh's current face normals"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH"
    
    def execute(self, context):
        current_to_original_normals(context, oN_attribute_name)
        
        print("\nThe current face normals have been copied into the attribute '{}'.".format(oN_attribute_name))
        return {'FINISHED'}


# DNORMS

# SET CURRENT
class dNormsTools_OT_add_dN_to_current(bpy.types.Operator):
    bl_idname = "dnorms_tools.add_dn_to_current"
    bl_label = "Add dN Attribute to Current Mesh Normals."
    bl_description = "Add the target morph normal delta attribute to this mesh's current face normals"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        key_name = context.object.dnorm_props.shape_keys_for_dN
        dN_exists = has_corresponding_dN_attribute(context, key_name)
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and dN_exists
    
    def execute(self, context):
        key_name = context.object.dnorm_props.shape_keys_for_dN
        dN_name = key_name + dN_attribute_suffix
        add_dN_to_current(context, dN_name)

        print("\nThe values of the attribute '{}' have been added to the current face normals.".format(dN_name))
        return {'FINISHED'} 

class dNormsTools_OT_set_current_from_oN_plus_dN(bpy.types.Operator):
    bl_idname = "dnorms_tools.set_current_from_on_plus_dn"
    bl_label = "Copy the Sum of OriginalNormals and dN Attributes to Current Mesh Normals."
    bl_description = "Set the sums of the OriginalNormals and target morph normal delta attributes as this mesh's current face normals"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        has_oN = context.object.dnorm_props.oN_attribute
        key_name = context.object.dnorm_props.shape_keys_for_dN
        dN_exists = has_corresponding_dN_attribute(context, key_name)
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and has_oN and dN_exists
    
    def execute(self, context):
        key_name = context.object.dnorm_props.shape_keys_for_dN
        dN_name = key_name + dN_attribute_suffix
        original_plus_dN_to_current(context, dN_name, oN_attribute_name)

        print("\nThe current face normals have been replaced by the sums of the attributes '{}' and '{}'.".format(oN_attribute_name, dN_name))
        return {'FINISHED'} 


# SAVE ATTRIBUTE
class dNormsTools_OT_set_dN_from_current_vs_oN(bpy.types.Operator):
    bl_idname = "dnorms_tools.set_dn_from_current_vs_on"
    bl_label = "Save Delta Between Current and Original Normals to dN Attribute."
    bl_description = "Saves the deltas between the original and current mesh normals into the target morph normal attribute."
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        has_oN = context.object.dnorm_props.oN_attribute
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and has_oN
    
    def execute(self, context):
        key_name = context.object.dnorm_props.shape_keys_for_dN
        dN_name = key_name + dN_attribute_suffix
        set_dN_from_current_vs_original(context, dN_name, oN_attribute_name)

        print("\nSet the contents of the morph normal attribute '{}' to the deltas between '{}' and the current face normals.".format(dN_name, oN_attribute_name))
        return {'FINISHED'} 


# EDIT
class dNormsTools_OT_retarget_dN_to_current(bpy.types.Operator):
    bl_idname = "dnorms_tools.retarget_dn_to_current"
    bl_label = "Retarget Morph Deltas to Current Normals."
    bl_description = "Recalculate the target deltas for the resulting morph normals to correspond to the current face normals."
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        has_oN = context.object.dnorm_props.oN_attribute
        key_name = context.object.dnorm_props.shape_keys_for_dN
        dN_exists = has_corresponding_dN_attribute(context, key_name)
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and has_oN and dN_exists
    
    def execute(self, context):
        key_name = context.object.dnorm_props.shape_keys_for_dN
        dN_name = key_name + dN_attribute_suffix
        retarget_dN_to_current_normals(context, dN_name, oN_attribute_name)

        print("\nRecalculated the '{}' attribute in proportion to the current face normals.".format(dN_name, oN_attribute_name))
        return {'FINISHED'} 


# CLEAR
class dNormsTools_OT_clear_dN(bpy.types.Operator):
    bl_idname = "dnorms_tools.clear_dn"
    bl_label = "Reset Target Morph Normals"
    bl_description = "Set all values of the target morph normal attribute to zero"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        key_name = context.object.dnorm_props.shape_keys_for_dN
        dN_exists = has_corresponding_dN_attribute(context, key_name)
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and dN_exists
    
    def execute(self, context):
        key_name = context.object.dnorm_props.shape_keys_for_dN
        dN_name = key_name + dN_attribute_suffix
        clear_dNorms(context, dN_name)
        
        print("\nCleared the contents of the morph normal attribute '{}'.".format(dN_name))
        return {'FINISHED'}

class dNormsTools_OT_clear_dN_for_vg(bpy.types.Operator):
    bl_idname = "dnorms_tools.clear_dn_for_vg"
    bl_label = "Reset Target Morph Normals for Vertex Group"
    bl_description = "\nSet the values of the target morph normal attribute to zero for the given vertex group.\nVertex group values of less than one attenuate rather than nullify"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        key_name = context.object.dnorm_props.shape_keys_for_dN
        dN_exists = has_corresponding_dN_attribute(context, key_name)
        vertex_group_name = context.object.dnorm_props.vertex_groups
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and dN_exists and vertex_group_name != "None"
    
    def execute(self, context):
        key_name = context.object.dnorm_props.shape_keys_for_dN
        dN_name = key_name + dN_attribute_suffix
        vertex_group_name = context.object.dnorm_props.vertex_groups
        clear_dNorms_for_vertex_group(context, dN_name, vertex_group_name)
        
        print("\nCleared the contents of the morph normal attribute '{}' for the vertex group '{}'.".format(dN_name, vertex_group_name))
        return {'FINISHED'}

class dNormsTools_OT_clear_dN_excluding_vg(bpy.types.Operator):
    bl_idname = "dnorms_tools.clear_dn_excluding_vg"
    bl_label = "Reset Target Morph Normals Excluding Vertex Group"
    bl_description = "\nSet the values of the target morph normal attribute to zero, excluding the vertex group.\nVertex group values of less than one are affected to various degrees"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        key_name = context.object.dnorm_props.shape_keys_for_dN
        dN_exists = has_corresponding_dN_attribute(context, key_name)
        vertex_group_name = context.object.dnorm_props.vertex_groups
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and dN_exists and vertex_group_name != "None"
    
    def execute(self, context):
        key_name = context.object.dnorm_props.shape_keys_for_dN
        dN_name = key_name + dN_attribute_suffix
        vertex_group_name = context.object.dnorm_props.vertex_groups
        clear_dNorms_excluding_vertex_group(context, dN_name, vertex_group_name)
        
        print("\nCleared the contents of the morph normal attribute '{}', excluding the vertex group '{}'.".format(dN_name, vertex_group_name))
        return {'FINISHED'}


# SWITCH DOMAINS
class dNormsTools_OT_switch_oN_domain(bpy.types.Operator):
    bl_idname = "dnorms_tools.change_on_domain"
    bl_label = "Change OriginalNormals Domain."
    bl_description = "Switches the domain of the OriginalNormals attribute from Vertex to Face Corner and vice versa\nThe icon represents its current domain"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        has_oN = context.object.dnorm_props.oN_attribute
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and has_oN
    
    def execute(self, context):
        initial_domain = context.object.data.attributes[oN_attribute_name].domain
        resulting_domain = switch_vector_attribute_domain(context, oN_attribute_name)
        
        print("\nChanged the domain of the attribute '{}' from {} to {}.".format(oN_attribute_name, initial_domain, resulting_domain))
        return {'FINISHED'}


class dNormsTools_OT_switch_dN_domain(bpy.types.Operator):
    bl_idname = "dnorms_tools.change_dn_domain"
    bl_label = "Change dN Domain"
    bl_description = "Switches the domain of this morph normal attribute from Vertex to Face Corner and vice versa.\nThe icon represents its current domain"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        key_name = context.object.dnorm_props.shape_keys_for_dN
        dN_exists = has_corresponding_dN_attribute(context, key_name)
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and dN_exists
    
    def execute(self, context):
        key_name = context.object.dnorm_props.shape_keys_for_dN
        dN_name = key_name + dN_attribute_suffix
        initial_domain = context.object.data.attributes[dN_name].domain
        resulting_domain = switch_vector_attribute_domain(context, dN_name)
        
        print("\nChanged the domain of the attribute '{}' from {} to {}.".format(dN_name, initial_domain, resulting_domain))
        return {'FINISHED'}


class dNormsTools_OT_switch_oNtoC_domain(bpy.types.Operator):
    bl_idname = "dnorms_tools.change_ontoc_domain"
    bl_label = "Change OriginalNormals_AsColours Domain."
    bl_description = "Switches the domain of the OriginalNormals_AsColours attribute from Vertex to Face Corner and vice versa\nThe icon represents its current domain"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        has_oNtoC = context.object.dnorm_props.oNtoC_attribute
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and has_oNtoC
    
    def execute(self, context):
        initial_domain = context.object.data.attributes[oNtoC_attribute_name].domain
        resulting_domain = switch_color_attribute_domain(context, oNtoC_attribute_name)
        
        print("\nChanged the domain of the attribute '{}' from {} to {}.".format(oNtoC_attribute_name, initial_domain, resulting_domain))
        return {'FINISHED'}


class dNormsTools_OT_switch_currentNtoC_domain(bpy.types.Operator):
    bl_idname = "dnorms_tools.change_currentntoc_domain"
    bl_label = "Change CurrentNormals_AsColours Domain."
    bl_description = "Switches the domain of the CurrentNormals_AsColours attribute from Vertex to Face Corner and vice versa\nThe icon represents its current domain"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        has_currentNtoC = context.object.dnorm_props.currentNtoC_attribute
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and has_currentNtoC
    
    def execute(self, context):
        initial_domain = context.object.data.attributes[currentNtoC_attribute_name].domain
        resulting_domain = switch_color_attribute_domain(context, currentNtoC_attribute_name)
        
        print("\nChanged the domain of the attribute '{}' from {} to {}.".format(currentNtoC_attribute_name, initial_domain, resulting_domain))
        return {'FINISHED'}


class dNormsTools_OT_switch_dNtoC_domain(bpy.types.Operator):
    bl_idname = "dnorms_tools.change_dntoc_domain"
    bl_label = "Change dNtoC Domain"
    bl_description = "Switches the domain of this morph normal to colour attribute from Vertex to Face Corner and vice versa.\nThe icon represents its current domain"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        key_name = context.object.dnorm_props.shape_keys_for_dN
        dNtoC_exists = has_corresponding_dNtoC_attribute(context, key_name)
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and dNtoC_exists
    
    def execute(self, context):
        key_name = context.object.dnorm_props.shape_keys_for_dNtoC
        dNtoC_name = key_name + dNtoC_attribute_suffix
        initial_domain = context.object.data.attributes[dNtoC_name].domain
        resulting_domain = switch_color_attribute_domain(context, dNtoC_name)
        
        print("\nChanged the domain of the attribute '{}' from {} to {}.".format(dNtoC_name, initial_domain, resulting_domain))
        return {'FINISHED'}


# ADD & DELETE ATTRIBUTES
class dNormsTools_OT_add_missing_attributes(bpy.types.Operator):
    bl_idname = "dnorms_tools.add_missing_attributes"
    bl_label = "Add Missing Attributes"
    bl_description = "Create any missing normal delta and normal-to-colour attributes for all shape keys, as well as the original and current normals.\nThe OriginalNormals attribute is set with the current face normals; the normal deltas with zeroes"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        valid_shape_keys = context.object.dnorm_props.shape_keys_for_dN
        has_oN = context.object.dnorm_props.oN_attribute
        shape_key_names = get_valid_shape_key_names(context)
        has_any_dN = has_any_dN_attribute(context, shape_key_names)
        has_currentNtoC = context.object.dnorm_props.currentNtoC_attribute
        has_oNtoC = context.object.dnorm_props.oNtoC_attribute
        has_any_dNtoC = has_any_dNtoC_attribute(context, shape_key_names)
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and valid_shape_keys != "None" and (not has_oN or not has_any_dN or not has_currentNtoC or not has_oNtoC or not has_any_dNtoC)
    
    def execute(self, context):
        log = add_missing_attributes(context)
        
        output_string = "\nThe following attributes were created:"
        for entry in log:
            output_string += "\n- {}".format(entry)
        print(output_string)
        return {'FINISHED'}


class dNormsTools_OT_delete_all_attributes(bpy.types.Operator):
    bl_idname = "dnorms_tools.delete_all_attributes"
    bl_label = "Delete All Attributes"
    bl_description = "Delete all normal delta and normal-to-colour attributes, including those of the original and current normals"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        has_oN = context.object.dnorm_props.oN_attribute
        shape_key_names = get_valid_shape_key_names(context)
        has_any_dN = has_any_dN_attribute(context, shape_key_names)
        has_currentNtoC = context.object.dnorm_props.currentNtoC_attribute
        has_oNtoC = context.object.dnorm_props.oNtoC_attribute
        has_any_dNtoC = has_any_dNtoC_attribute(context, shape_key_names)
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and (has_oN or has_any_dN or has_currentNtoC or has_oNtoC or has_any_dNtoC)
    
    def execute(self, context):
        log = delete_all_attributes(context)
        
        context.object.dnorm_props.preview_material_targets = "None"

        output_string = "\nThe following attributes were deleted:"
        for entry in log:
            output_string += "\n- {}".format(entry)
        print(output_string)
        return {'FINISHED'}


# NORMAL COLOURS
class dNormsTools_OT_regenerate_currentNtoC(bpy.types.Operator):
    bl_idname = "dnorms_tools.regenerate_currentntoc"
    bl_label = "Regenerate CurrentNormals_AsColours"
    bl_description = "(Re)generate the CurrentNormals_AsColours attribute using the current face normals"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH"
    
    def execute(self, context):
        regenerate_currentNtoC(context, currentNtoC_attribute_name)
        
        print("\nThe attribute '{}' has been regenerated using the current mesh face normals.".format(currentNtoC_attribute_name))
        return {'FINISHED'}
    
    
class dNormsTools_OT_regenerate_oNtoC(bpy.types.Operator):
    bl_idname = "dnorms_tools.regenerate_ontoc"
    bl_label = "Regenerate OriginalNormals_AsColour"
    bl_description = "(Re)generate the OriginalNormals_AsColour attribute using the current OriginalNormals"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        has_oN = context.object.dnorm_props.oN_attribute
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and has_oN
    
    def execute(self, context):
        regenerate_oNtoC(context, oN_attribute_name, oNtoC_attribute_name)
        
        print("\nThe attribute '{}' has been regenerated using the current contents of '{}'.".format(oNtoC_attribute_name, oN_attribute_name))
        return {'FINISHED'}


class dNormsTools_OT_regenerate_dNtoC(bpy.types.Operator):
    bl_idname = "dnorms_tools.regenerate_dntoc"
    bl_label = "Regenerate a Delta's Normals-to-Colour Attribute"
    bl_description = "(Re)generate a morph normal delta's corresponding normals-to-colour attribute"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        key_name = context.object.dnorm_props.shape_keys_for_dNtoC
        try:
            potential_mesh = context.object.data
            dN_attribute_name = key_name + dN_attribute_suffix
            if dN_attribute_name in potential_mesh.attributes:
                dN_exists = True
            else:
                dN_exists = False
        except:
            dN_exists = False
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and dN_exists
    
    def execute(self, context):
        shape_key_name = context.object.dnorm_props.shape_keys_for_dNtoC
        regenerate_dNtoC(context, oN_attribute_name, shape_key_name, dN_attribute_suffix, dNtoC_attribute_suffix)
        
        dN_attribute_name = shape_key_name + dN_attribute_suffix
        dNtoC_attribute_name = shape_key_name + dNtoC_attribute_suffix
        print("\nThe attribute '{}' has been regenerated using the current contents of '{}'.".format(dNtoC_attribute_name, dN_attribute_name))
        return {'FINISHED'}


class dNormsTools_OT_regenerate_all_dNtoCs(bpy.types.Operator):
    bl_idname = "dnorms_tools.regenerate_all_dntocs"
    bl_label = "Regenerate all Deltas' Normals-to-Colour Attributes"
    bl_description = "(Re)generate all morph normal deltas' corresponding normals-to-colour attributes"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        shape_key_names = get_valid_shape_key_names(context)
        has_any_dN = has_any_dN_attribute(context, shape_key_names)
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and has_any_dN
    
    def execute(self, context):
        shape_key_names = get_valid_shape_key_names(context)
        regenerate_all_dNtoCs(context, oN_attribute_name, shape_key_names, dN_attribute_suffix, dNtoC_attribute_suffix)
        
        print("\nRegenerated all dNtoC attributes:")
        for shape_key_name in shape_key_names:
            dN_attribute_name = shape_key_name + dN_attribute_suffix
            dNtoC_attribute_name = shape_key_name + dNtoC_attribute_suffix
            print("- The attribute '{}' has been regenerated using the current contents of '{}'.".format(dNtoC_attribute_name, dN_attribute_name))
        return {'FINISHED'}


# PREVIEW MATERIAL
class dNormsTools_OT_display_preview_material(bpy.types.Operator):
    bl_idname = "dnorms_tools.display_preview_material"
    bl_label = "Display a Preview Material for the Attribute"
    bl_description = "Replace the mesh's active material by a simple display of the target attribute.\nOriginalNormals and dNs are not perfectly displayed as they contain negative values"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        valid_target_attribute = context.object.dnorm_props.preview_material_targets != "None"
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and valid_target_attribute
    
    def execute(self, context):
        target_attribute_name = context.object.dnorm_props.preview_material_targets
        preview_material = context.object.dnorm_props.preview_material
     
        preview_material, previous_material = generate_preview_material(context, target_attribute_name, preview_material)
        context.object.dnorm_props.preview_material = preview_material
        if (previous_material != preview_material):
            context.object.dnorm_props.previous_material = previous_material

        print("The preview material '{}' is now displaying the attribute '{}'.".format(preview_material, target_attribute_name))
        return {'FINISHED'}


class dNormsTools_OT_restore_previous_material(bpy.types.Operator):
    bl_idname = "dnorms_tools.restore_previous_material"
    bl_label = "Returns the Mesh to its Original Active Material"
    bl_description = "Replace the mesh's active previeww material by the material it originally had"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        has_previous_material = context.object.dnorm_props.previous_material
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and has_previous_material 
    
    def execute(self, context):
        previous_material = context.object.dnorm_props.previous_material
     
        restore_previous_material(context, previous_material)

        print("The mesh's active material is now '{}'.".format(previous_material))
        return {'FINISHED'}


# ATTRIBUTE TRANSFER
class dNormsTools_OT_attribute_transfer_vertex(bpy.types.Operator):
    bl_idname = "dnorms_tools.attribute_transfer_vertex"
    bl_label = "Transfer Attributes Between Meshes Based on Closest Vertex"
    bl_description = "..."
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        has_other_mesh = context.object.dnorm_props.other_mesh
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and has_other_mesh 
    
    def execute(self, context):
        other_mesh = context.object.dnorm_props.other_mesh
     
        test_vertex_search(context, other_mesh)

        print("Tested the Vertex Attribute Transfer function")
        return {'FINISHED'}


# UI
class dNormsTools_panel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_dNormsTools_panel"
    bl_label = "Normal Deltas Custom Attributes Tools"
    
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"


    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'MESH' and context.object.data.shape_keys != None

    def draw(self, context):
        obj = context.object
        props = obj.dnorm_props
        
        layout = self.layout


        # Section: general management
        general_attributes_row = layout.row()
        general_attributes_row.operator(dNormsTools_OT_add_missing_attributes.bl_idname, text="Create Missing Attributes", icon='MOD_LINEART')
        general_attributes_row.operator(dNormsTools_OT_delete_all_attributes.bl_idname, text="Delete All Attributes", icon='TRASH')

        preview_material_row = layout.row()
        preview_material_row.operator(dNormsTools_OT_display_preview_material.bl_idname, text="Display Preview Material for", icon='HIDE_OFF')
        preview_material_row.prop(data=props, property="preview_material_targets", text="", icon='GROUP_VCOL')
        preview_material_row.operator(dNormsTools_OT_restore_previous_material.bl_idname, text="Restore Original Material", icon='HIDE_ON')
        

        # Section: oN
        oN_box = layout.box()

        oN_label_row = oN_box.row()
        oN_label_row.label(text="Original Normals", icon='MESH_UVSPHERE')
        oN_domain_text, oN_domain_icon = fetch_domain_switch_info_for(obj, oN_attribute_name)
        oN_label_row.operator(dNormsTools_OT_switch_oN_domain.bl_idname, text="", icon=oN_domain_icon)
        
        oN_ops_row = oN_box.row()
        oN_ops_row.operator(dNormsTools_OT_oN_to_current_normals.bl_idname, text="Original to Current Normals", icon='EXPORT')
        oN_ops_row.operator(dNormsTools_OT_current_normals_to_oN.bl_idname, text="Current to Original Normals", icon='IMPORT')

        # TODO: move switch attribute domain to a lil corner button if possible?
        # TODO: vertex group mask for all functions??


        # Section: dN
        dN_box = layout.box()

        dN_label_row = dN_box.row()
        dN_label_row.label(text="Morph Normal Deltas", icon='ORIENTATION_NORMAL')
        dN_label_row.prop(data=props, property="shape_keys_for_dN", text="target", icon='SHAPEKEY_DATA')

        dN_key_name = obj.dnorm_props.shape_keys_for_dN
        dN_name = dN_key_name + dN_attribute_suffix
        dN_domain_text, dN_domain_icon = fetch_domain_switch_info_for(obj, dN_name)
        dN_label_row.operator(dNormsTools_OT_switch_dN_domain.bl_idname, text="", icon=dN_domain_icon)

        dN_current_row = dN_box.row()
        dN_current_row.operator(dNormsTools_OT_set_current_from_oN_plus_dN.bl_idname, text="Original + Delta to Current Normals", icon='EXPORT')
        dN_current_row.operator(dNormsTools_OT_set_dN_from_current_vs_oN.bl_idname, text="Current - Original Normals to Delta", icon='IMPORT')
        dN_box.operator(dNormsTools_OT_add_dN_to_current.bl_idname, text="Add Delta to Current Normals", icon='ADD')

        dN_ops_box = dN_box.box()
        dN_ops_box.operator(dNormsTools_OT_retarget_dN_to_current.bl_idname, text="Retarget Delta to Current Normals", icon='ORIENTATION_GIMBAL')

        

        
        

        dN_clear_box = dN_box.box()
        dN_clear_box.operator(dNormsTools_OT_clear_dN.bl_idname, text="Clear Delta", icon='X')
        dN_vg_row = dN_clear_box.row()
        dN_vg_column = dN_vg_row.column()
        dN_vg_column.operator(dNormsTools_OT_clear_dN_for_vg.bl_idname, text="Clear Only", icon='CLIPUV_HLT')
        dN_vg_column.operator(dNormsTools_OT_clear_dN_excluding_vg.bl_idname, text="Clear Excluding", icon='CLIPUV_DEHLT')
        dN_vg_row.prop(data=props, property="vertex_groups", text="", icon='GROUP_VERTEX')

        
        
        



        # Section: NtoC
        NtoC_box = layout.box()
        NtoC_label_row = NtoC_box.row()

        NtoC_label_row.label(text="Normals as Colour Attributes", icon='COLOR')

        currentNtoC_row = NtoC_box.row()
        currentNtoC_row.operator(dNormsTools_OT_regenerate_currentNtoC.bl_idname, text="Regenerate CurrentNormals_AsColour", icon='FILE_TICK')
        currentNtoC_domain_text, currentNtoC_domain_icon = fetch_domain_switch_info_for(obj, currentNtoC_attribute_name)
        currentNtoC_row.operator(dNormsTools_OT_switch_currentNtoC_domain.bl_idname, text="", icon=currentNtoC_domain_icon)
        
        oNtoC_row = NtoC_box.row()
        oNtoC_row.operator(dNormsTools_OT_regenerate_oNtoC.bl_idname, text="Regenerate OriginalNormals_AsColour", icon='FILE_TICK')
        oNtoC_domain_text, oNtoC_domain_icon = fetch_domain_switch_info_for(obj, oNtoC_attribute_name)
        oNtoC_row.operator(dNormsTools_OT_switch_oNtoC_domain.bl_idname, text="", icon=oNtoC_domain_icon)

        NtoC_box.operator(dNormsTools_OT_regenerate_all_dNtoCs.bl_idname, text="Regenerate All dNtoCs", icon='FILE_TICK')

        dNtoC_row = NtoC_box.row()
        dNtoC_row.operator(dNormsTools_OT_regenerate_dNtoC.bl_idname, text="Regenerate dNtoC for", icon='FILE_TICK')
        dNtoC_row.prop(data=props, property="shape_keys_for_dNtoC", text="", icon='SHAPEKEY_DATA')
        dNtoC_key_name = obj.dnorm_props.shape_keys_for_dNtoC
        dNtoC_name = dNtoC_key_name + dNtoC_attribute_suffix
        dNtoC_domain_text, dNtoC_domain_icon = fetch_domain_switch_info_for(obj, dNtoC_name)
        dNtoC_row.operator(dNormsTools_OT_switch_dNtoC_domain.bl_idname, text="", icon=dNtoC_domain_icon)

        layout.prop(props, "other_mesh")
        layout.operator(dNormsTools_OT_attribute_transfer_vertex.bl_idname, text="Test Vertex Function")
        




# (UN)REGISTRATION
def register_dnorm_tools():
    # Properties
    bpy.utils.register_class(dNormsTools_properties)
    types.Object.dnorm_props = props.PointerProperty(type=dNormsTools_properties)

    # Classes
    bpy.utils.register_class(dNormsTools_OT_oN_to_current_normals)
    bpy.utils.register_class(dNormsTools_OT_current_normals_to_oN)
    bpy.utils.register_class(dNormsTools_OT_add_dN_to_current)
    bpy.utils.register_class(dNormsTools_OT_set_dN_from_current_vs_oN)
    bpy.utils.register_class(dNormsTools_OT_set_current_from_oN_plus_dN)
    bpy.utils.register_class(dNormsTools_OT_retarget_dN_to_current)
    bpy.utils.register_class(dNormsTools_OT_clear_dN)
    bpy.utils.register_class(dNormsTools_OT_clear_dN_for_vg)
    bpy.utils.register_class(dNormsTools_OT_clear_dN_excluding_vg)
    bpy.utils.register_class(dNormsTools_OT_switch_oN_domain)
    bpy.utils.register_class(dNormsTools_OT_switch_dN_domain)
    bpy.utils.register_class(dNormsTools_OT_switch_currentNtoC_domain)
    bpy.utils.register_class(dNormsTools_OT_switch_oNtoC_domain)
    bpy.utils.register_class(dNormsTools_OT_switch_dNtoC_domain)
    bpy.utils.register_class(dNormsTools_OT_add_missing_attributes)
    bpy.utils.register_class(dNormsTools_OT_delete_all_attributes)
    bpy.utils.register_class(dNormsTools_OT_regenerate_currentNtoC)
    bpy.utils.register_class(dNormsTools_OT_regenerate_oNtoC)
    bpy.utils.register_class(dNormsTools_OT_regenerate_dNtoC)
    bpy.utils.register_class(dNormsTools_OT_regenerate_all_dNtoCs)
    bpy.utils.register_class(dNormsTools_OT_display_preview_material)
    bpy.utils.register_class(dNormsTools_OT_restore_previous_material)
    bpy.utils.register_class(dNormsTools_OT_attribute_transfer_vertex)
    bpy.utils.register_class(dNormsTools_panel)


def unregister_dnorm_tools():
    # Properties
    del types.Object.dnorm_props
    bpy.utils.unregister_class(dNormsTools_properties)

    # Classes
    bpy.utils.unregister_class(dNormsTools_OT_oN_to_current_normals)
    bpy.utils.unregister_class(dNormsTools_OT_current_normals_to_oN)
    bpy.utils.unregister_class(dNormsTools_OT_add_dN_to_current)
    bpy.utils.unregister_class(dNormsTools_OT_set_dN_from_current_vs_oN)
    bpy.utils.unregister_class(dNormsTools_OT_set_current_from_oN_plus_dN)
    bpy.utils.unregister_class(dNormsTools_OT_retarget_dN_to_current)
    bpy.utils.unregister_class(dNormsTools_OT_clear_dN)
    bpy.utils.unregister_class(dNormsTools_OT_clear_dN_for_vg)
    bpy.utils.unregister_class(dNormsTools_OT_clear_dN_excluding_vg)
    bpy.utils.unregister_class(dNormsTools_OT_switch_oN_domain)
    bpy.utils.unregister_class(dNormsTools_OT_switch_dN_domain)
    bpy.utils.unregister_class(dNormsTools_OT_switch_currentNtoC_domain)
    bpy.utils.unregister_class(dNormsTools_OT_switch_oNtoC_domain)
    bpy.utils.unregister_class(dNormsTools_OT_switch_dNtoC_domain)
    bpy.utils.unregister_class(dNormsTools_OT_add_missing_attributes)
    bpy.utils.unregister_class(dNormsTools_OT_delete_all_attributes)
    bpy.utils.unregister_class(dNormsTools_OT_regenerate_currentNtoC)
    bpy.utils.unregister_class(dNormsTools_OT_regenerate_oNtoC)
    bpy.utils.unregister_class(dNormsTools_OT_regenerate_dNtoC)
    bpy.utils.unregister_class(dNormsTools_OT_regenerate_all_dNtoCs)
    bpy.utils.unregister_class(dNormsTools_OT_display_preview_material)
    bpy.utils.unregister_class(dNormsTools_OT_restore_previous_material)
    bpy.utils.unregister_class(dNormsTools_OT_attribute_transfer_vertex)
    bpy.utils.unregister_class(dNormsTools_panel)



# FUNCTIONS

# GENERAL ATTRIBUTE ADD AND DELETE
def add_missing_attributes(context):
    obj = context.object
    mesh = obj.data

    log = []

    if currentNtoC_attribute_name not in mesh.attributes:
        mesh.attributes.new(currentNtoC_attribute_name, 'FLOAT_COLOR', 'CORNER')
        update_currentNtoC(context, currentNtoC_attribute_name)
        log.append(currentNtoC_attribute_name)

    if oN_attribute_name not in mesh.attributes:
        mesh.attributes.new(oN_attribute_name, 'FLOAT_VECTOR', 'CORNER')
        current_to_original_normals(context, oN_attribute_name)
        log.append(oN_attribute_name)

    if oNtoC_attribute_name not in mesh.attributes:
        mesh.attributes.new(oNtoC_attribute_name, 'FLOAT_COLOR', 'CORNER')
        update_oNtoC(context, oN_attribute_name, oNtoC_attribute_name)
        log.append(oNtoC_attribute_name)

    shape_key_names = get_valid_shape_key_names(context)
    for key_name in shape_key_names:
        dN_attribute_name = key_name + dN_attribute_suffix
        if dN_attribute_name not in mesh.attributes:
            mesh.attributes.new(dN_attribute_name, 'FLOAT_VECTOR', 'CORNER')
            log.append(dN_attribute_name)

        dNtoC_attribute_name = key_name + dNtoC_attribute_suffix
        if dNtoC_attribute_name not in mesh.attributes:
            mesh.attributes.new(dNtoC_attribute_name, 'FLOAT_COLOR', 'CORNER')
            update_dNtoC(context, oN_attribute_name, dN_attribute_name, dNtoC_attribute_name)
            log.append(dNtoC_attribute_name)
    
    obj.data.update()
    return log
    

def delete_all_attributes(context):
    obj = context.object
    mesh = obj.data

    log = []

    if currentNtoC_attribute_name in mesh.attributes:
        mesh.attributes.remove(mesh.attributes[currentNtoC_attribute_name])
        log.append(currentNtoC_attribute_name)

    if oN_attribute_name in mesh.attributes:
        mesh.attributes.remove(mesh.attributes[oN_attribute_name])
        log.append(oN_attribute_name)

    if oNtoC_attribute_name in mesh.attributes:
        mesh.attributes.remove(mesh.attributes[oNtoC_attribute_name])
        log.append(oNtoC_attribute_name)

    dN_attribute_names = get_valid_dN_attribute_names(context)
    for attribute_name in dN_attribute_names:
        if attribute_name in mesh.attributes:
            mesh.attributes.remove(mesh.attributes[attribute_name])
            log.append(attribute_name)

    NtoC_attribute_names = get_valid_NtoC_attribute_names(context)
    for attribute_name in NtoC_attribute_names:
        if attribute_name in mesh.attributes:
            mesh.attributes.remove(mesh.attributes[attribute_name])
            log.append(attribute_name)

    obj.data.update()
    return log
    

# PREVIEW MATERIAL
def generate_preview_material(context, target_attribute, preview_material):
    obj = context.object
    mesh = obj.data

    previous_material = obj.active_material

    if not preview_material:
        preview_material_name = "{}_{}_attribute_previewer".format(obj.name, mesh.name)
        preview_material = bpy.data.materials.new(name = preview_material_name)
        
        preview_material.use_nodes = True
        nodes = preview_material.node_tree.nodes
        links = preview_material.node_tree.links
        preview_material.node_tree.nodes.clear()
        
        output_node = nodes.new(type="ShaderNodeOutputMaterial")
        attribute_node = nodes.new(type="ShaderNodeAttribute")
        links.new(attribute_node.outputs["Vector"], output_node.inputs["Surface"])
    
    else:
        nodes = preview_material.node_tree.nodes
        attribute_node = nodes["Attribute"]

    attribute_node.attribute_name = target_attribute

    obj.active_material = preview_material
    obj.data.update()
        
    return preview_material, previous_material


def restore_previous_material(context, previous_material):
    obj = context.object
    mesh = obj.data

    obj.active_material = previous_material
    obj.data.update()




# ATTRIBUTE TRANSFER
def test_vertex_search(context, other_mesh):
    obj = context.object
    mesh = obj.data
    


## COPY BETWEEN MESHES

# import mathutils
# from mathutils import Vector

# test_point = Vector([0.5, 0.25, 1.5])


# # VERTEX SEARCH STUFF
# from mathutils.kdtree import KDTree
# tree_size = len(mesh.vertices)
# kd_tree = KDTree(tree_size)
# for vertex in mesh.vertices:
#     kd_tree.insert(vertex.co, vertex.index)
# kd_tree.balance()
# # TODO: check if they are in global space / work with other meshes.

# position, index, distance = kd_tree.find(test_point)
# print("\nClosest vertex:")
# print(position)
# print(index)
# print(distance)
# print(mesh.vertices[index])


# # FACE SEARCH STUFF
# from mathutils.bvhtree import BVHTree
# bhv_tree = BVHTree.FromObject(obj, context.evaluated_depsgraph_get())

# position, normal, index, distance = bhv_tree.find_nearest(test_point)
# print("\nClosest face:")
# print(position)
# print(normal)
# print(index)
# print(distance)
# print(mesh.polygons[index])
# print(mesh.polygons[index].vertices)
# print(mesh.polygons[index].loop_indices)

# #hit = bhv_tree.ray_cast(test_point, position - test_point)
# #print("\nRaycast hit:")
# #print(hit)

# vertices = []
# for i in mesh.polygons[index].vertices:
#     vertices.append(mesh.vertices[i].co)   
# #print(vertices)

# from mathutils.interpolate import poly_3d_calc
# weight = poly_3d_calc(vertices, position)

# print("\nResulting weight:")
# print(weight)