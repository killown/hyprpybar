import os
import toml
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio, Gdk
from gi.repository import Gtk
from gi.repository import Gtk4LayerShell as LayerShell
from subprocess import Popen
import math
import pulsectl
from hyprpy import Hyprland

class Utils(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.home = os.path.expanduser("~")
        self.config_path = os.path.join(self.home, ".config/hyprpanel")
        self.dockbar_config = os.path.join(self.config_path, "dockbar.toml")
        self.style_css_config = os.path.join(self.config_path, "style.css")
        self.workspace_list_config = os.path.join(self.config_path, "workspacebar.toml")
        self.topbar_config = os.path.join(self.config_path, "panel.toml")
        self.menu_config = os.path.join(self.config_path, "menu.toml")
        self.window_notes_config = os.path.join(self.config_path, "window-config.toml")
        self.cmd_config = os.path.join(self.config_path, "cmd.toml")
        self.psutil_store = {}
        self.panel_cfg = self.load_topbar_config()
        
    def run_app(self, cmd, wclass, cmd_mode=True):
        
        if wclass:
            instance = Hyprland()
            address_list = [i.address for i in instance.get_windows() if i.wm_class.lower() == wclass]
            print(address_list, wclass)
            if address_list:
                address = address_list[0]
                cmd = "hyprctl dispatch hyprshell:toggleoverview; hyprctl dispatch focuswindow address:{0};hyprctl dispatch fullscreen 1".format(address)
                for c in cmd.split(";"):
                    try:
                        Popen(c.split(), start_new_session=True)
                    except Exception as e:
                        print(e)
                return
        if "kitty --hold" in cmd and cmd_mode:
            try:
                Popen(cmd.split(), start_new_session=True)
            except Exception as e:
                print(e)
                print(e)
            return
        if ";" in cmd:
            for c in cmd.split(";"):
                try:
                    Popen(c.split(), start_new_session=True)
                except Exception as e:
                    print(e)
        else:
            try:
                Popen(cmd.split(), start_new_session=True)
            except Exception as e:
                print(e)
                
    def CreateFromAppList(self, config, orientation, class_style, callback=None):
        if orientation == "h":
            orientation = Gtk.Orientation.HORIZONTAL
        if orientation == "v":
            orientation = Gtk.Orientation.VERTICAL

        box = Gtk.Box(spacing=10, orientation=orientation)
        print(config)
        with open(config, "r") as f:
            config = toml.load(f)

            for app in config:
                wclass = None
                try:
                    wclass = config[app]["wclass"]
                except:
                    pass
                button = self.CreateButton(
                    config[app]["icon"], config[app]["cmd"], class_style, wclass
                )
                if callback is not None:
                    self.CreateGesture(button, 3, callback)
                box.append(button)
        return box
        
        
    def CreateButton(self, icon_name, cmd, Class_Style, wclass):
        box = Gtk.Box(spacing=0)
        icon = Gtk.Image(icon_name=icon_name)
        box.append(icon)
        box.add_css_class(Class_Style)
        button = Adw.ButtonContent()
        button.set_icon_name(icon_name)
        button.add_css_class(Class_Style + "Button")
        if cmd == "NULL":
            button.set_sensitive(False)
            return button
        self.CreateGesture(button, 1, lambda *_: self.run_app(cmd, wclass))
        self.CreateGesture(button, 3, lambda *_: self.dockbar_remove(icon_name))
        return button
        
    def load_topbar_config(self):
        with open(self.topbar_config, "r") as f:
            return toml.load(f)

    def CreateGesture(self, widget, mouse_button, callback):
        gesture = Gtk.GestureClick.new()
        gesture.connect("released", callback)
        gesture.set_button(mouse_button)
        widget.add_controller(gesture)
        
    def convert_size(self, size_bytes):
        if size_bytes == 0:
            return "0B"
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return "%s %s" % (s, size_name[i])
    
    
    def btn_background(self, class_style, icon_name):
        tbtn_title_b = Adw.ButtonContent()
        tbtn_title_b.set_icon_name(icon_name)
        tbtn_title_b.add_css_class(class_style)
        return tbtn_title_b
    
    def dockbar_remove(self, cmd):
        with open(self.dockbar_config, "r") as f:
            config = toml.load(f)
    

