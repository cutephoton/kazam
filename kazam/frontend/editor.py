# -*- coding: utf-8 -*-
#
#       preferences.py
#
#       Copyright 2012 David Klasinc <bigwhale@lubica.net>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 3 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

# make stubs: cat uifile | sed -n -E 's/^.*handler="([^"]+)".*$/def \1 (self, widget): pass/gp'
import os
import math
import logging
import cairo
logger = logging.getLogger("Editor")

from gi.repository import Gtk, Gdk, GObject, Pango

from kazam.utils import *
from kazam.backend.prefs import *
from enum import Enum

TOOL_CROP = 0
TOOL_ANNOTATE = 1
"""
class Tool(object):
    class Selection(Enum):
        Single     = 1
        Dual       = 2
        Multi      = 3

    class Draw(Enum):
        Individual = 1
        Path       = 2

    def __init__ (self, mode):
        self._points = []
        self.point_active_index = None
        self.point_mode = mode

    def add_point (self, position):
        pass

    def set_point (self, position):
        pass

    def get_point (self, point_index):
        pass

    def set_point_index (self, index):
        pass

    def on_down (self, position):
        if self.point_mode != Tool.Selection.Multi:
            self.point_active_index = 0

        return False

    def on_up (self, position):
        return False

    def on_move (self, position):
        return False

    def on_apply (self):
        return False

    def on_draw (self, cr):
        return False

    def on_draw_points (self, cr):
        return False
"""

class Rectangle(object):
    def __init__ (self, p1, p2):
        self.x1 = p1[0]
        self.y1 = p1[1]
        self.x2 = p2[0]
        self.y2 = p2[1]

    @property
    def p1 (self):
        return (self.x1, self.y1)
    @p1.setter
    def p1(self, value):
        self.x1 = value[0]
        self.y1 = value[1]
    @property
    def p2 (self):
        return (self.x2, self.y2)
    @p2.setter
    def p2(self, value):
        self.x2 = value[0]
        self.y2 = value[1]
    @property
    def topLeft (self):
        return (min(self.x1, self.x2), min(self.y1,self.y2))

    @property
    def bottomRight (self):
        return (max(self.x1, self.x2), max(self.y1,self.y2))

    @property
    def width (self):
        return abs(self.x1 - self.x2)

    @property
    def height (self):
        return abs(self.y1 - self.y2)

    @property
    def valid (self):
        return self.width>0 and self.height>0

    @property
    def area (self):
        return self.width*self.height

def withinRange(v, minv, maxv):
    return max(min(v,maxv),minv)

class Cropper (Gtk.DrawingArea):
    def __init__ (self):
        super().__init__()
        self.set_events(Gdk.EventMask.BUTTON_PRESS_MASK|Gdk.EventMask.BUTTON_RELEASE_MASK|Gdk.EventMask.BUTTON_RELEASE_MASK|Gdk.EventMask.POINTER_MOTION_MASK)

        self.connect("draw", self._draw)
        self.connect("button-press-event", self._button_down)
        self.connect("button-release-event", self._button_up)
        self.connect("motion-notify-event", self._motion)
        self._btnDown = False
        self.selection = None
        self.which = 0

    def _transformXY_ToNormalized(self,c):
        w = float(self.get_allocated_width())
        h = float(self.get_allocated_height())
        return (withinRange(c[0]/w, 0, 1), withinRange(c[1]/h,0,1))

    def _transformXY_FromNormalized(self,c):
        w = float(self.get_allocated_width())
        h = float(self.get_allocated_height())
        return (c[0]*w, c[1]*h)

    def _button_down(self, widget, event):
        logger.debug("down")
        self._btnDown = True
        p = self._transformXY_ToNormalized((event.x,event.y))
        self.selection = Rectangle(p,p)
        return True

    def _button_up(self, widget, event):
        logger.debug("up")
        self._btnDown = False
        p = self._transformXY_ToNormalized((event.x,event.y))
        self.selection.p2 = p
        if (self.selection.area < 0.00075):
            self.selection = None
        self.queue_draw()
        return True

    def _motion (self, widget, event):
        if self._btnDown:
            #logger.debug("move")
            p = self._transformXY_ToNormalized((event.x,event.y))
            self.selection.p2 = p
            self.queue_draw()
            return True
    def _draw (self, widget, ctx):
        #logger.debug("Draw CROP")

        w = float(self.get_allocated_width())
        h = float(self.get_allocated_height())

        if self.selection is not None and self.selection.valid:
            tl = self._transformXY_FromNormalized(self.selection.topLeft)
            br = self._transformXY_FromNormalized(self.selection.bottomRight)

            ctx.set_line_width (4)
            ctx.set_source_rgba (0.0, 0.0, 0.0, 0.25) # Solid color
            ctx.rectangle (tl[0],tl[1],br[0]-tl[0],br[1]-tl[1]) # Rectangle(x0, y0, x1, y1)
            ctx.stroke ()

            ctx.set_line_width (2)
            ctx.set_source_rgba (0.6, 0.0, 0.6, 0.75) # Solid color
            ctx.move_to (tl[0]+20, tl[1])
            ctx.line_to (tl[0],tl[1])
            ctx.line_to (tl[0],tl[1]+20)
            ctx.stroke ()

            ctx.set_line_width (2)
            ctx.set_source_rgba (0.6, 0.0, 0.6, 0.75) # Solid color
            ctx.move_to (br[0]-20, br[1])
            ctx.line_to (br[0],br[1])
            ctx.line_to (br[0],br[1]-20)
            ctx.stroke ()

class EditorDialog(GObject.GObject):
    #__gsignals__ = {
    #    "prefs-quit" : (GObject.SIGNAL_RUN_LAST,
    #                    None,
    #                    (),
    #        ),
    #    }
    __gsignals__ = {
        "editing-done"       : (GObject.SIGNAL_RUN_LAST, None, [GObject.TYPE_PYOBJECT],)
    }

    def __init__(self, pixbuf):
        GObject.GObject.__init__(self)
        logger.debug("Editor Init.")

        #self.moddified = pixbuf

        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(prefs.datadir, "ui", "editor.ui"))
        self.builder.connect_signals(self)
        for w in self.builder.get_objects():
            if issubclass(type(w), Gtk.Buildable):
                name = Gtk.Buildable.get_name(w)
                setattr(self, name, w)
            else:
                logger.debug("Unable to get name for '%s'" % w)
        self.create_surface(pixbuf)

        self.current_tool = TOOL_CROP
        self.output_image = None

        self.crop_layer = Cropper()
        self.drawing_layers.add_overlay(self.crop_layer)

        self.restore_UI()

    def create_surface (self, pixbuf):
        pix_w = pixbuf.get_width()
        pix_h = pixbuf.get_height()

        img = cairo.ImageSurface(0, pix_w, pix_h)
        img_cr = cairo.Context(img)
        Gdk.cairo_set_source_pixbuf(img_cr,pixbuf, 0, 0)
        img_cr.paint()

        self.screenPixbuf = pixbuf
        self.screenPixbufResult = pixbuf
        self.screenSurface = img
        self.screenWidth = pix_w
        self.screenHeight = pix_h

        self.aspectframe.set(0.5,0.5,pix_w/pix_h,False)

    def applyCrop (self):
        if (self.crop_layer.selection is not None):
            crop = self.crop_layer.selection

            w = crop.width * self.screenWidth
            h = crop.height * self.screenHeight
            left = crop.topLeft[0] * self.screenWidth
            top = crop.topLeft[1] * self.screenHeight

            #img_cr = cairo.Context(self.screenSurface)
            #Gdk.cairo_set_source_pixbuf(img_cr, self.screenPixbuf, 0, 0)
            #img_cr.paint()
            self.screenPixbufResult = Gdk.pixbuf_get_from_surface (self.screenSurface, left, top, w, h);
            #right = crop.topLeft[0] * self.screenWidth
            #bottom = crop.topLeft[1] * self.screenHeight
            #img = cairo.ImageSurface(0, w, h)
            #img_cr = cairo.Context(img)
            #Gdk.cairo_set_source_pixbuf(img_cr,pixbuf, -left, -top)
            #img_cr.paint()




    def open(self):
        self.window.show_all()
        return self.window.run()

    def destroy (self):
        self.window.destroy()

    def restore_UI(self):
        logger.debug("Restoring UI.")
        self.tool_change(TOOL_CROP)
        self.window.resize(prefs.capture_editor_w, prefs.capture_editor_h)
        logger.debug("Window: {}".format((prefs.capture_editor_w, prefs.capture_editor_h)))

    def btn_cancel_clicked_cb (self, widget):
        prefs.capture_editor_w, prefs.capture_editor_h = self.window.get_size()

        self.window.response(Gtk.ResponseType.CANCEL)

    def btn_accept_clicked_cb (self, widget):
        prefs.capture_editor_w, prefs.capture_editor_h = self.window.get_size()
        self.applyCrop()
        self.window.response(Gtk.ResponseType.OK)

    def tool_crop_toggled_cb (self, widget): pass
    #    if (widget.get_active()):
    #        self.tool_change(TOOL_CROP)
    def tool_annotate_toggled_cb (self, widget): pass
    #    if (widget.get_active()):
    #        self.tool_change(TOOL_ANNOTATE)
    def tool_change (self, toolid): pass
    #    self.current_tool = toolid
    #    self.tool_annotate.set_active(toolid == TOOL_CROP)
    #    self.tool_crop.set_active(toolid == TOOL_ANNOTATE)

    def tool_colorpicker_color_set_cb (self, widget): pass

    def crop_layer_draw_cb (self, widget, ctx):pass

    def drawing_draw_cb(self, widget, ctx):
        #logger.debug("Drawing callback: " + str(ctx))
        dst = (float(self.drawing.get_allocated_width()),float(self.drawing.get_allocated_height()))
        ctx.rectangle(0, 0, dst[0], dst[1])
        ctx.scale(dst[0]/float(self.screenWidth), dst[1]/float(self.screenHeight))
        ctx.set_source_surface(self.screenSurface, 0, 0)
        ctx.fill()

    def drawing_button_press_event_cb (self, widget): pass
    def drawing_button_press_event_cb (self, widget): pass
    def drawing_motion_notify_event_cb (self, widget): pass
