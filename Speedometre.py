# coding=ascii

"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

bl_info = {
    "name": "Speedometre",
    "description": "Addon for check object velocity",
    "author": "Deletrain Remi",
    "version": (0, 0, 1),
    "blender": (2, 82, 0),
    "location": "View3D",
    "wiki_url": "",
    "category": "Object"
}


# ==================================
#   Import modules
# ==================================

#   Windows
import os
import math

#   Blender
import bpy
import bpy_extras
import blf

from mathutils import Vector
from bpy import (utils, types)
from bpy.app import handlers
from bpy.types import (Operator, Panel, PropertyGroup, SpaceView3D)
from bpy.props import (StringProperty, BoolProperty, IntProperty, PointerProperty)


# ==================================
#   Callback
# ==================================

def draw_callback_px(self, context):

    # Compute speed
    speed = speedometre.speed
    if context.scene.Speedometre.toKmh:
        msg = '{0}km/h'.format(round(speed * 3.6, 3))
    else:
        speed = speedometre.speed
        msg = '{0}m/s'.format(round(speed, 3))

    # Get position
    bb = speedometre.obj.bound_box
    max_z = max(bb[1][2], bb[2][2], bb[5][2], bb[6][2])

    pos_3d = speedometre.obj.matrix_world.to_translation()
    pos_3d[2] += max_z * 2

    pos_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(context.region, context.space_data.region_3d, pos_3d)

    # Draw
    font_id = 0
    font_size = context.scene.Speedometre.fontPointSize
    blf.position(font_id, pos_2d[0] - ((len(msg) * font_size) * 0.25), pos_2d[1], 0)
    blf.size(font_id, font_size, 72)
    blf.draw(font_id, msg)


# ==================================
#	Speedometre
# ==================================

class Speedometre(object):

    def __init__(self, obj=None):
        
        self._obj = None
        self.last_pos = None
        self.delta_time = 1.0 / 24.0
        self.current_frame = 1.0
        self.speed = 0.0
        
        self.draw_handle = None
        self.callback = set()

        if obj:
            self.obj = obj

    @property
    def obj(self):

        """
        !@Brief Get Blender object
        
        @rtype: ToDo find class name
        @return: Blender Object.
        """
        
        return self._obj
    
    @obj.setter
    def obj(self, value):

        """
        !@Brief Set Blender object.
        
        @rtype: ToDo find class name
        @return: Blender Object.
        """

        self._obj = value
        self.last_pos = self._obj.matrix_world.to_translation()


speedometre = Speedometre()


# ==================================
#    UI
# ==================================

class SpeedometreSettings(PropertyGroup):

    toKmh : BoolProperty(name="Km/h", description="Swith speed to kilometer per hours", default=False)
    fontPointSize : IntProperty(name="FontSize", description="Font point size", default=20)

class SpeedometreData(PropertyGroup):

    objects : StringProperty(name="Objects", description="Object List", default="")


class Speedometre_Start(Operator):

    bl_idname = "speedometre.start"
    bl_label = "Start"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.object

    def invoke(self, context, event):
        return self.execute(context)

    def draw(self, context):
        row = self.layout

    def execute(self, context):
        
        def __get_speed(s, c):

            if not speedometre.obj:
                    return

            current_pos = speedometre.obj.matrix_world.to_translation()
            distance = current_pos - speedometre.last_pos
            speedometre.last_pos = current_pos
            delta_time = speedometre.delta_time * abs(speedometre.current_frame - c.scene.frame_current)
            speedometre.current_frame = c.scene.frame_current
            speedometre.speed = 0.0 if delta_time == 0.0 else distance.length / delta_time

        # Get object
        a_selected = context.selected_objects
        if len(a_selected) == 0:
            raise RuntimeError('No object selected !')
        speedometre.obj = a_selected[0]
        speedometre.current_frame = context.scene.frame_current
        speedometre.delta_time = 1.0 / context.scene.render.fps

        # Set callback
        args = (self, context)
        speedometre.draw_handle = SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')

        handlers.frame_change_post.append(__get_speed)
        speedometre.callback.add(len(handlers.frame_change_post) - 1)

        return {'FINISHED'}


class Speedometre_Stop(Operator):

    bl_idname = "speedometre.stop"
    bl_label = "Stop"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.object

    def invoke(self, context, event):
        return self.execute(context)

    def draw(self, context):
        row = self.layout

    def execute(self, context):
        if speedometre.draw_handle:
            SpaceView3D.draw_handler_remove(speedometre.draw_handle, 'WINDOW')
        speedometre.draw_handle = None

        for i in speedometre.callback:
            del handlers.frame_change_post[i]
        speedometre.callback = set()

        return {'FINISHED'}


class SpeedometrePanel:

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "QD Tools"
    bl_options = {"DEFAULT_CLOSED"}


class Speedometre_PT_main(SpeedometrePanel, Panel):

    bl_idname = "Speedometre_PT_main"
    bl_label = "Speedometre"

    def draw(self, context):

        self.layout.prop(context.scene.Speedometre, "toKmh")
        self.layout.prop(context.scene.Speedometre, "fontPointSize")
        self.layout.separator()
        self.layout.operator("wm.sm_start")
        self.layout.operator("wm.sm_stop")
        self.layout.separator()


# ==================================
#    Register | Unregister
# ==================================

CLASSES =  (SpeedometreSettings,
            Speedometre_Start,
            Speedometre_Stop,
            SpeedometrePanel,
            Speedometre_PT_main)

def register():
    for cls in CLASSES:
        try:
            utils.register_class(cls)
        except:
            print(f"{cls.__name__} already registred")
    types.Scene.Speedometre = PointerProperty(type=SpeedometreSettings)

def unregister():
    for cls in CLASSES:
        if hasattr(types, cls.__name__):
            utils.unregister_class(cls)
    del types.Scene.Speedometre
