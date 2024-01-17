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
import psutil

class Utils(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.home = os.path.expanduser("~")
        self.webapps_applications = os.path.join(self.home, ".local/share/applications")
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
        self.icon_theme_list = Gtk.IconTheme().get_icon_names()
        
    def run_app(self, cmd, wclass=None, initial_title=None, cmd_mode=True):
        if wclass:
            instance = Hyprland()
            address_list = []
            if not initial_title:
                address_list = [i.address for i in instance.get_windows() if i.wm_class.lower() == wclass]
            if initial_title:
                address_list = [i.address for i in instance.get_windows() if i.wm_class.lower() == wclass and i.initial_title.lower() == initial_title]
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
        box.add_css_class("box_from_dockbar")
        with open(config, "r") as f:
            config = toml.load(f)

            for app in config:
                wclass = None
                initial_title = None
                try:
                    wclass = config[app]["wclass"]
                except:
                    pass
                button = self.CreateButton(
                    config[app]["icon"], config[app]["cmd"], class_style, wclass, initial_title
                )
                if callback is not None:
                    self.CreateGesture(button, 3, callback)
                box.append(button)
        return box


    def search_local_desktop(self, initial_title):
        for deskfile in os.listdir(self.webapps_applications):
            if deskfile.startswith("chrome") or deskfile.startswith("msedge"):
                pass
            else:
                continue
            webapp_path = os.path.join(self.webapps_applications, deskfile)
            #necessary initial title without lower()
            desktop_file_found = self.search_str_inside_file(webapp_path, initial_title)
            if desktop_file_found:
                cmd = "gtk-launch {0}".format(deskfile)
                icon = deskfile.split(".desktop")[0]
                break
        if deskfile:
            return deskfile
        else:
            return None
    
    
    def search_desktop(self, wm_class):
        all_apps = Gio.AppInfo.get_all()
        desktop_files = [i.get_id().lower() for i in all_apps if wm_class in i.get_display_name().lower()]
        if desktop_files:
            return desktop_files[0]
        else:
            return None
    
    def CreateTaskbarLauncher(self, wmclass, address, title, initial_title, orientation, class_style, callback=None):
        if orientation == "h":
            orientation = Gtk.Orientation.HORIZONTAL
        if orientation == "v":
            orientation = Gtk.Orientation.VERTICAL
        cmd = None
        processes = psutil.process_iter()
        instance = Hyprland()
        pid = [i.pid for i in instance.get_windows() if i.address == address]
        if pid:
            process_id = pid[0]
            if -1 != process_id:
                cmd = "hyprctl dispatch hyprshell:toggleoverview; hyprctl dispatch focuswindow address:{0};hyprctl dispatch fullscreen 1".format(address)
            
        icon = wmclass
        all_apps = Gio.AppInfo.get_all()
        
        desk_local = self.search_local_desktop(initial_title)
        desk = self.search_desktop(wmclass)
        if cmd is None:
            print(wmclass, address, initial_title, desk_local, desk, "cmd is none caralho")
            if not wmclass in desk_local:
                cmd = "gtk-launch {}".format(desk)
            else:
                cmd = "gtk-launch {}".format(desk_local)
        if desk_local:
            desk_local = desk_local.split(".desktop")[0]
        if desk_local is None:       
            if desk:
                desk = desk.split(".desktop")[0]
        for i in all_apps:
            if desk_local is not None and "-Default" in desk_local:
                icon = desk_local
                break
            id =  i.get_id().lower()
            name = i.get_name().lower()
            if desk:
                if initial_title in name:
                   icon = i.get_icon()
                   break
            else:
                if wmclass in id:
                    icon = i.get_icon()
                    
        if initial_title == "zsh":
            label = title.split(" ")[0]
            icon_exist = [i for i in self.icon_theme_list if label in i]
            try:
                icon = icon_exist[-1]
            except IndexError:
                pass        
        
        initial_title = " ".join(i.capitalize() for i in initial_title.split())
        button = self.create_clicable_image(icon, cmd, class_style, wmclass, title, initial_title)
        if callback is not None:
            self.CreateGesture(button, 3, callback)
        return button
        
        
    def search_str_inside_file(self, file_path, word):
        with open(file_path, 'r') as file:
            content = file.read()
            if word in content.lower():
                return True
            else:
                return False
            
    def create_clicable_image(self, icon, cmd, Class_Style, wclass, title, initial_title):
        box  = Gtk.Box.new( Gtk.Orientation.HORIZONTAL, spacing=6)
        box.add_css_class(Class_Style)
        image = None
        #panel.toml has filters for missing icons
        try:
            icon = self.panel_cfg["change_icon_title"][icon]
        except:
            print(icon, "errrrouuu")
            pass
        if type(icon) is str:
            image = Gtk.Image.new_from_icon_name(icon)
        else:
            image = Gtk.Image.new_from_gicon(icon)
        image.add_css_class("icon_from_popover_launcher")
        image.set_icon_size(Gtk.IconSize.LARGE)
        image.props.margin_end = 5
        image.set_halign(Gtk.Align.END)
        label = Gtk.Label.new()
        #zsh use titles instead of initial title
        use_this_title = initial_title
        if "zsh" == initial_title.lower():
            use_this_title = title
           
        desktop_local_file = self.search_local_desktop(initial_title) 
        if desktop_local_file:
            icon = desktop_local_file.split(".desktop")[0]            
                    
        label.set_label(use_this_title)
        label.add_css_class("clicable_image_label")
        box.append(image)
        box.append(label)
        box.add_css_class("box_from_clicable_image")
        self.CreateGesture(box, 1, lambda *_: self.run_app(cmd, wclass, initial_title))
        return box
        
                    
    def CreateButton(self, icon_name, cmd, Class_Style, wclass, initial_title=None):
        box = Gtk.Box(spacing=6)
        box.add_css_class(Class_Style)
        button = Adw.ButtonContent()
        button.set_icon_name(icon_name)
        button.add_css_class("{}-buttons".format(Class_Style))
        button.add_css_class("hvr-grow")
        if cmd == "NULL":
            button.set_sensitive(False)
            return button
        self.CreateGesture(button, 1, lambda *_: self.run_app(cmd, wclass, initial_title))
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
    

