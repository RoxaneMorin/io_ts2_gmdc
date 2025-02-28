
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
    switch_dN_domain
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
    return ["None"]

def get_shape_key_names(self, context):
    obj = context.object
    if obj and obj.type == 'MESH' and obj.data.shape_keys:
        # Ignore the Basis and :: keys.
        return [(key.name, key.name, "") for key in obj.data.shape_keys.key_blocks[1:] if key.name != "::"]
    return [("None", "None", "No valid shape keys exist.")]

def get_vertex_group_names(self, context):
    groups = [("None", "None", "Do not use a vertex group.")]
    obj = context.object
    if obj and obj.type == 'MESH' and obj.vertex_groups:
        groups.extend([(vertex_group.name, vertex_group.name, "") for vertex_group in obj.vertex_groups])
    return groups


def get_has_oN_attribute(self):
    obj = self.id_data
    if obj and obj.type == 'MESH':
        mesh = obj.data
        return oN_attribute_name in mesh.attributes
    return False

def get_dN_attribute_names(self, context):
    obj = context.object
    if obj and obj.type == 'MESH':
        mesh = obj.data
        attributes = [(attribute.name, attribute.name, "") for attribute in mesh.attributes if dN_attribute_suffix in attribute.name]
        if len(attributes) > 0:
            return attributes
    return [("None", "None", "No valid attribute exists.")]


def get_has_oNtoC_attribute(self):
    obj = self.id_data
    if obj and obj.type == 'MESH':
        mesh = obj.data
        return oNtoC_attribute_name in mesh.attributes
    return False

def get_NtoC_attribute_names(self, context):
    obj = context.object
    if obj and obj.type == 'MESH':
        mesh = obj.data
        attributes = [(attribute.name, attribute.name, "") for attribute in mesh.attributes if dNtoC_attribute_suffix in attribute.name]
        if len(attributes) > 0:
            return attributes
    return [("None", "None", "No valid attribute exists.")]



# PROPERTIES
class dNormsTools_properties(types.PropertyGroup):
    shape_keys: props.EnumProperty(name="Shape Keys", items=get_shape_key_names)
    vertex_groups: props.EnumProperty(name="Vertex Groups", items=get_vertex_group_names)

    oN_attribute: props.BoolProperty(name="Original Normals Attribute", get=get_has_oN_attribute)
    dN_attributtes: props.EnumProperty(name="Morph Normal Deltas Attributes", items=get_dN_attribute_names)

    oNtoC_attribute: props.BoolProperty(name="Original Normals Colour Attribute", get=get_has_oNtoC_attribute)
    dNtoC_attributes: props.EnumProperty(name="Morph Normals Colour Attributes", items=get_NtoC_attribute_names)



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

        print("The current face normals have been replaced by those stored in the attribute '{}'.".format(oN_attribute_name))
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
        
        print("The current face normals have been copied into the attribute '{}'.".format(oN_attribute_name))
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
        dN_name = context.object.dnorm_props.dN_attributtes
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and dN_name != "None"
    
    def execute(self, context):
        dN_name = context.object.dnorm_props.dN_attributtes
        add_dN_to_current(context, dN_name)

        print("The values of the attribute '{}' have been added to the current face normals.".format(dN_name))
        return {'FINISHED'} 

class dNormsTools_OT_set_current_from_oN_plus_dN(bpy.types.Operator):
    bl_idname = "dnorms_tools.set_current_from_on_plus_dn"
    bl_label = "Copy the Sum of OriginalNormals and dN Attributes to Current Mesh Normals."
    bl_description = "Set the sums of the OriginalNormals and target morph normal delta attributes as this mesh's current face normals"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        has_oN = context.object.dnorm_props.oN_attribute
        dN_name = context.object.dnorm_props.dN_attributtes
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and has_oN and dN_name != "None"
    
    def execute(self, context):
        dN_name = context.object.dnorm_props.dN_attributtes
        original_plus_dN_to_current(context, dN_name, oN_attribute_name)

        print("The current face normals have been replaced by the sums of the attributes '{}' and '{}'.".format(oN_attribute_name, dN_name))
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
        dN_name = context.object.dnorm_props.dN_attributtes
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and has_oN and dN_name != "None"
    
    def execute(self, context):
        # TODO: allow for morphs that don't yet have a dN attribute.
        dN_name = context.object.dnorm_props.dN_attributtes
        set_dN_from_current_vs_original(context, dN_name, oN_attribute_name)

        print("Set the contents of the morph normal attribute '{}' to the deltas between '{}' and the current face normals.".format(dN_name, oN_attribute_name))
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
        dN_name = context.object.dnorm_props.dN_attributtes
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and has_oN and dN_name != "None"
    
    def execute(self, context):
        dN_name = context.object.dnorm_props.dN_attributtes
        retarget_dN_to_current_normals(context, dN_name, oN_attribute_name)

        print("Recalculated the '{}' attribute in proportion to the current face normals.".format(dN_name, oN_attribute_name))
        return {'FINISHED'} 


# CLEAR
class dNormsTools_OT_clear_dN(bpy.types.Operator):
    bl_idname = "dnorms_tools.clear_dn"
    bl_label = "Reset Target Morph Normals"
    bl_description = "Set all values of the target morph normal attribute to zero"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        dN_name = context.object.dnorm_props.dN_attributtes
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and dN_name != "None"
    
    def execute(self, context):
        dN_name = context.object.dnorm_props.dN_attributtes
        clear_dNorms(context, dN_name)
        
        print("Cleared the contents of the morph normal attribute '{}'.".format(dN_name))
        return {'FINISHED'}

class dNormsTools_OT_clear_dN_for_vg(bpy.types.Operator):
    bl_idname = "dnorms_tools.clear_dn_for_vg"
    bl_label = "Reset Target Morph Normals for Vertex Group"
    bl_description = "Set the values of the target morph normal attribute to zero for the given vertex group.\nVertex group values of less than one attenuate rather than nullify"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        dN_name = context.object.dnorm_props.dN_attributtes
        vertex_group_name = context.object.dnorm_props.vertex_groups
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and dN_name != "None" and vertex_group_name != "None"
    
    def execute(self, context):
        dN_name = context.object.dnorm_props.dN_attributtes
        vertex_group_name = context.object.dnorm_props.vertex_groups
        clear_dNorms_for_vertex_group(context, dN_name, vertex_group_name)
        
        print("Cleared the contents of the morph normal attribute '{}' for the vertex group '{}'.".format(dN_name, vertex_group_name))
        return {'FINISHED'}

class dNormsTools_OT_clear_dN_excluding_vg(bpy.types.Operator):
    bl_idname = "dnorms_tools.clear_dn_excluding_vg"
    bl_label = "Reset Target Morph Normals Excluding Vertex Group"
    bl_description = "Set the values of the target morph normal attribute to zero, excluding the vertex group.\nVertex group values of less than one are affected to various degrees"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        dN_name = context.object.dnorm_props.dN_attributtes
        vertex_group_name = context.object.dnorm_props.vertex_groups
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and dN_name != "None" and vertex_group_name != "None"
    
    def execute(self, context):
        dN_name = context.object.dnorm_props.dN_attributtes
        vertex_group_name = context.object.dnorm_props.vertex_groups
        clear_dNorms_excluding_vertex_group(context, dN_name, vertex_group_name)
        
        print("Cleared the contents of the morph normal attribute '{}', excluding the vertex group '{}'.".format(dN_name, vertex_group_name))
        return {'FINISHED'}


class dNormsTools_OT_switch_oN_domain(bpy.types.Operator):
    bl_idname = "dnorms_tools.change_on_domain"
    bl_label = "Change OriginalNormals Domain"
    bl_description = "Switches the domain of the OriginalNormals attribute from Vertex to Face Corner and vice versa."
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        has_oN = context.object.dnorm_props.oN_attribute
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and has_oN
    
    def execute(self, context):
        initial_domain = context.object.data.attributes[oN_attribute_name].domain
        resulting_domain = switch_dN_domain(context, oN_attribute_name)
        
        print("Changed the domain of the attribute '{}' from {} to {}.".format(oN_attribute_name, initial_domain, resulting_domain))
        return {'FINISHED'}


class dNormsTools_OT_switch_dN_domain(bpy.types.Operator):
    bl_idname = "dnorms_tools.change_dn_domain"
    bl_label = "Change dN Domain"
    bl_description = "Switches the domain of this moprh normal attribute from Vertex to Face Corner and vice versa."
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        dN_name = context.object.dnorm_props.dN_attributtes
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and dN_name != "None"
    
    def execute(self, context):
        dN_name = context.object.dnorm_props.dN_attributtes
        initial_domain = context.object.data.attributes[dN_name].domain
        resulting_domain = switch_dN_domain(context, dN_name)
        
        print("Changed the domain of the attribute '{}' from {} to {}.".format(dN_name, initial_domain, resulting_domain))
        return {'FINISHED'}


class dNormsTools_add_missing_attributes(bpy.types.Operator):
    bl_idname = "dnorms_tools.add_missing_attributes"
    bl_label = "Add Missing Attributes"
    bl_description = "Creates empty attributes for the shape keys that lack them, as well as OriginalNormals if necessary."
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        # TODO: only display if necessary, such as oN or any dN not existing.
        has_oN = context.object.dnorm_props.oN_attribute
        valid_shape_keys = context.object.dnorm_props.shape_keys
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and valid_shape_keys != "None"
    
    def execute(self, context):
        add_missing_attributes(context)
        
        #print("Changed the domain of the attribute '{}' from {} to {}.".format(dN_name, initial_domain, resulting_domain))
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


        # Section: oN
        oN_box = layout.box()

        oN_label_row = oN_box.row()
        oN_label_row.label(text="Original Normals", icon='MESH_UVSPHERE')
        if props.oN_attribute:
            oN_label_row.label(icon='CHECKBOX_HLT')
        else:
            oN_label_row.label(icon='CHECKBOX_DEHLT')

        oN_ops_row = oN_box.row()
        oN_ops_row.operator(dNormsTools_OT_oN_to_current_normals.bl_idname, text="Original to Current Normals", icon='EXPORT')
        oN_ops_row.operator(dNormsTools_OT_current_normals_to_oN.bl_idname, text="Current to Original Normals", icon='IMPORT')

        if context.object.dnorm_props.oN_attribute:
            if context.object.data.attributes[oN_attribute_name].domain == 'CORNER':
                text = "Switch Attribute Domain to Vertex"
                icon = 'NORMALS_VERTEX'
            else:
                text = "Switch Attribute Domain to Face Corner"
                icon = 'NORMALS_VERTEX_FACE'
        else:
            text="Switch Attribute Domain"
            icon = 'QUESTION'
        oN_box.operator(dNormsTools_OT_switch_oN_domain.bl_idname, text=text, icon=icon)
        

        # Section: dN
        dN_box = layout.box()

        dN_label_row = dN_box.row()
        dN_label_row.label(text="Morph Normal Deltas", icon='ORIENTATION_NORMAL')
        dN_label_row.prop(data=props, property="dN_attributtes", text="target")

        dN_current_row = dN_box.row()
        dN_current_row.operator(dNormsTools_OT_set_current_from_oN_plus_dN.bl_idname, text="Original + Delta to Current Normals", icon='EXPORT')
        dN_current_row.operator(dNormsTools_OT_set_dN_from_current_vs_oN.bl_idname, text="Current - Original Normals to Delta", icon='IMPORT')
        dN_box.operator(dNormsTools_OT_add_dN_to_current.bl_idname, text="Add Delta to Current Normals", icon='ADD')

        dN_ops_box = dN_box.box()
        dN_ops_box.operator(dNormsTools_OT_retarget_dN_to_current.bl_idname, text="Retarget Delta to Current Normals", icon='ORIENTATION_GIMBAL')

        dN_name = context.object.dnorm_props.dN_attributtes
        if dN_name != "None":
            if context.object.data.attributes[dN_name].domain == 'CORNER':
                text = "Switch Attribute Domain to Vertex"
                icon = 'NORMALS_VERTEX'
            else:
                text = "Switch Attribute Domain to Face Corner"
                icon = 'NORMALS_VERTEX_FACE'
        else:
            text="Switch Attribute Domain"
            icon = 'QUESTION'
        dN_ops_box.operator(dNormsTools_OT_switch_dN_domain.bl_idname, text=text, icon=icon)
        

        dN_clear_box = dN_box.box()
        dN_clear_box.operator(dNormsTools_OT_clear_dN.bl_idname, text="Clear Delta", icon='TRASH')
        dN_vg_row = dN_clear_box.row()
        dN_vg_column = dN_vg_row.column()
        dN_vg_column.operator(dNormsTools_OT_clear_dN_for_vg.bl_idname, text="Clear Only", icon='CLIPUV_HLT')
        dN_vg_column.operator(dNormsTools_OT_clear_dN_excluding_vg.bl_idname, text="Clear Excluding", icon='CLIPUV_DEHLT')
        dN_vg_row.prop(data=props, property="vertex_groups", text="", icon='GROUP_VERTEX')

        

        dN_box.operator(dNormsTools_add_missing_attributes.bl_idname, text="Add Missing Attributes")



        # Section: NtoC
        NtoC_box = layout.box()
        NtoC_label_row = NtoC_box.row()

        NtoC_label_row.label(text="Normals as Colour Attributes", icon='COLOR')



        #layout.prop(props, "oNtoC_attribute")
        #layout.prop(props, "dNtoC_attributes")

        #layout.prop(props, "shape_keys")



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
    bpy.utils.register_class(dNormsTools_add_missing_attributes)
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
    bpy.utils.unregister_class(dNormsTools_add_missing_attributes)
    bpy.utils.unregister_class(dNormsTools_panel)



# FUNCTIONS





def add_missing_attributes(context):
    obj = context.object
    mesh = obj.data

    if oN_attribute_name not in mesh.attributes:
        mesh.attributes.new(oN_attribute_name, 'FLOAT_VECTOR', 'CORNER')
        # Set from current?

    shape_key_names = get_valid_shape_key_names(context)
    for key_name in shape_key_names:
        dN_name = key_name + dN_attribute_suffix
        if dN_name not in mesh.attributes:
            mesh.attributes.new(dN_name, 'FLOAT_VECTOR', 'CORNER')

   #dN_attribute_suffix


