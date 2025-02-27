
import bpy
from bpy import context, types, props
from mathutils import Vector

from .dnorm_tools import (
    original_to_current_normals,
    current_to_original_normals,
    add_dN_to_current,
    original_plus_dN_to_current,
    retarget_dN_to_current_normals
    )



# GLOBAL PARAMETERS
oN_attribute_name = "OriginalNormals"
oN_attribute_name = "OriginalNormals"
currentNtoC_attribute_name = "CurrentNormals_AsColours"
oNtoC_attribute_name = "OriginalNormals_AsColours"
dN_attribute_suffix = "_dN"
dNtoC_attribute_suffix = "_NtoC"



# HELPERS
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





class dNormsTools_OT_clear_dN(bpy.types.Operator):
    bl_idname = "dnorms_tools.clear_dn"
    bl_label = "Reset Target Morph Normals"
    bl_description = "Set all values of the target morph normal attribute to zero"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        dN_name = context.object.dnorm_props.dN_attributtes
        return bpy.context.object.mode == "OBJECT" and context.view_layer.objects.active.type == "MESH" and dN_name != "None"
    
    def dN_name(self, context):
        dN_name = context.object.dnorm_props.dN_attributtes
        clear_dNorms(context, dN_name)
        
        print("Reset the contents of the morph normal attribute '{}'.".format(dN_name))
        return {'FINISHED'}


class dNormsTools_OT_clear_dN_for_vg(bpy.types.Operator):
    bl_idname = "dnorms_tools.clear_dn_for_vg"
    bl_label = "Reset Target Morph Normals for Vertex Group"
    bl_description = "Set the values of the target morph normal attribute to zero for the given vertex group.\nVertex group values of less than one attenuate rather than nullify."
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
        
        print("Reset the contents of the morph normal attribute '{}' for the vertex group '{}'.".format(dN_name, vertex_group_name))
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
        
        print("Reset the contents of the morph normal attribute '{}', excluding the vertex group '{}'.".format(dN_name, vertex_group_name))
        return {'FINISHED'}


class dNormsTools_OT_set_dN_from_current_vs_oN(bpy.types.Operator):
    bl_idname = "dnorms_tools.set_dn_from_current_vs_on"
    bl_label = "Save Delta Between Current and Original Normals to Target Morph Normals."
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
        set_dN_from_current_vs_original(context, dN_name)

        print("Set the contents of the morph normal attribute '{}' to the deltas between '{}' and the current face normals.".format(dN_name, oN_attribute_name))
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

        oN_opps_row = oN_box.row()
        oN_opps_row.operator(dNormsTools_OT_oN_to_current_normals.bl_idname, text="Original to Current Normals")
        oN_opps_row.operator(dNormsTools_OT_current_normals_to_oN.bl_idname, text="Current to Original Normals")
        
        

        # Section: dN
        dN_box = layout.box()

        dN_label_row = dN_box.row()
        dN_label_row.label(text="Morph Normal Deltas", icon='ORIENTATION_NORMAL')
        dN_label_row.prop(data=props, property="dN_attributtes", text="target")

        dN_current_box = dN_box.box()
        dN_current_box.operator(dNormsTools_OT_add_dN_to_current.bl_idname, text="Add Delta to Current Normals")
        dN_current_box.operator(dNormsTools_OT_set_current_from_oN_plus_dN.bl_idname, text="Original + Delta to Current Normals")



        dN_box.operator(dNormsTools_OT_retarget_dN_to_current.bl_idname, text="Retarget Delta to Current Normals")


        dN_box.operator(dNormsTools_OT_set_dN_from_current_vs_oN.bl_idname, text="Set from Delta Between Original and Current Normals")

        

        



        dN_clear_box = dN_box.box()
        dN_clear_box.operator(dNormsTools_OT_clear_dN.bl_idname, text="Clear Target Morph Normals")
        dN_vg_row = dN_clear_box.row()
        dN_vg_column = dN_vg_row.column()
        dN_vg_column.operator(dNormsTools_OT_clear_dN_for_vg.bl_idname, text="Clear Only", icon='CLIPUV_HLT')
        dN_vg_column.operator(dNormsTools_OT_clear_dN_excluding_vg.bl_idname, text="Clear Excluding", icon='CLIPUV_DEHLT')
        dN_vg_row.prop(data=props, property="vertex_groups", text="", icon='GROUP_VERTEX')


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
    bpy.utils.register_class(dNormsTools_OT_clear_dN)
    bpy.utils.register_class(dNormsTools_OT_clear_dN_for_vg)
    bpy.utils.register_class(dNormsTools_OT_clear_dN_excluding_vg)
    bpy.utils.register_class(dNormsTools_OT_add_dN_to_current)
    bpy.utils.register_class(dNormsTools_OT_set_dN_from_current_vs_oN)
    bpy.utils.register_class(dNormsTools_OT_set_current_from_oN_plus_dN)
    bpy.utils.register_class(dNormsTools_OT_retarget_dN_to_current)
    bpy.utils.register_class(dNormsTools_panel)


def unregister_dnorm_tools():
    # Properties
    del types.Object.dnorm_props
    bpy.utils.unregister_class(dNormsTools_properties)

    # Classes
    bpy.utils.unregister_class(dNormsTools_OT_oN_to_current_normals)
    bpy.utils.unregister_class(dNormsTools_OT_current_normals_to_oN)
    bpy.utils.unregister_class(dNormsTools_OT_clear_dN)
    bpy.utils.unregister_class(dNormsTools_OT_clear_dN_for_vg)
    bpy.utils.unregister_class(dNormsTools_OT_clear_dN_excluding_vg)
    bpy.utils.unregister_class(dNormsTools_OT_add_dN_to_current)
    bpy.utils.unregister_class(dNormsTools_OT_set_dN_from_current_vs_oN)
    bpy.utils.unregister_class(dNormsTools_OT_set_current_from_oN_plus_dN)
    bpy.utils.unregister_class(dNormsTools_OT_retarget_dN_to_current)
    bpy.utils.unregister_class(dNormsTools_panel)



# FUNCTIONS



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
                mesh.attributes[dN_name].data[vertex.index].vector = tuple(new_dN)
            except:
                pass

    elif dN_attribute.domain == 'CORNER':
        for loop in mesh.loops:
            try:
                vertex_dN = dN_attribute.data[loop.index].vector
                dN_weight = 1 - vertex_group.weight(loop.vertex_index)
                new_dN = [value * dN_weight for value in vertex_dN]
                mesh.attributes[dN_name].data[loop.index].vector = tuple(new_dN)
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
                mesh.attributes[dN_name].data[vertex.index].vector = tuple(new_dN)
            except:
                mesh.attributes[dN_name].data[vertex.index].vector = tuple([0.0, 0.0, 0.0])

    elif dN_attribute.domain == 'CORNER':
        for loop in mesh.loops:
            try:
                vertex_dN = dN_attribute.data[loop.index].vector
                dN_weight = vertex_group.weight(loop.vertex_index)
                new_dN = [value * dN_weight for value in vertex_dN]
                mesh.attributes[dN_name].data[loop.index].vector = tuple(new_dN)
            except:
                mesh.attributes[dN_name].data[loop.index].vector = tuple([0.0, 0.0, 0.0])
    
    obj.data.update()


def set_dN_from_current_vs_original(context, dN_name):
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
            delta = current_normal - original_normal
            mesh.attributes[dN_name].data[loop.index].vector = delta       

    elif oN_attribute.domain == 'CORNER':
        for loop in mesh.loops:
            current_normal = mesh.corner_normals[loop.index].vector
            original_normal = oN_attribute.data[loop.index].vector
            delta = current_normal - original_normal
            mesh.attributes[dN_name].data[loop.index].vector = delta

    obj.data.update()





