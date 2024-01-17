import os
import toml
import gi
import json
import psutil
from subprocess import Popen, call, check_output as out
from collections import ChainMap

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio, Gdk
from ..core.create_panel import *
from ..core.utils import Utils
from hyprpy import Hyprland

class Dockbar(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize Utils and set configuration paths
        self.utils = Utils()
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
        self.panel_cfg = self.utils.load_topbar_config()
        self.instance = self.HyprlandInstance()
        self.taskbar_list = [None]
        #this instance does not update, this is just to initialize the var
        instance = Hyprland()
        self.all_pids = [i.pid for i in instance.get_windows() if i.wm_class]
        self.timeout_taskbar = None
        self.buttons_pid = {}
        self.buttons_address = {}
        self.has_taskbar_started = False

    # Start the Dockbar application
    def do_start(self):
        GLib.timeout_add(300, self.check_pids)
        with open(self.topbar_config, "r") as f:
            panel_toml = toml.load(f)
            for p in panel_toml:
                if "left" == p:
                    exclusive = panel_toml[p]["Exclusive"] == "True"
                    position = panel_toml[p]["position"]
                    self.left_panel = CreatePanel(
                        self, "LEFT", position, exclusive, 32, 0, "LeftBar"
                    )
                    self.dockbar = self.utils.CreateFromAppList(self.dockbar_config,
                        "v", "LeftBar", self.join_windows
                    )
                    self.add_launcher = Gtk.Button()
                    self.add_launcher.set_icon_name("tab-new-symbolic")
                    self.add_launcher.connect("clicked", self.dockbar_append)
                    self.dockbar.append(self.add_launcher)
                    self.left_panel.set_content(self.dockbar)
                    self.left_panel.present()
                if "bottom" == p:
                    exclusive = panel_toml[p]["Exclusive"] == "True"
                    position = panel_toml[p]["position"]
                    self.bottom_panel = CreatePanel(
                        self, "BOTTOM", position, exclusive, 32, 0, "BottomBar"
                    )
                    self.add_launcher = Gtk.Button()
                    self.add_launcher.set_icon_name("tab-new-symbolic")
                    self.add_launcher.connect("clicked", self.dockbar_append)
                    self.taskbar = Gtk.Box()
                    self.taskbar.append(self.add_launcher)
                    self.taskbar.add_css_class("taskbar")
                    self.bottom_panel.set_content(self.taskbar)
                    self.bottom_panel.present()
                    #start the taskbar list first time, remaning check pids will do
                    self.Taskbar("h", "taskbar")           
                    
                    
    def Taskbar(self, orientation, class_style, update_button=False, callback=None):
        instance = Hyprland()
        all_windows = [i for i in instance.get_windows() if i.wm_class and not i.wm_class in self.taskbar_list]
        if not all_windows:
            return True
        with open(self.dockbar_config, "r") as f:
            config = toml.load(f)
        launchers_desktop_file = [config[i]["desktop_file"] for i in config]
        for i in all_windows:
            wm_class = i.wm_class.lower()
            address = i.address.lower()
            initial_title = i.initial_title.lower()
            title = i.title
            pid = i.pid
            if wm_class in launchers_desktop_file and update_button == False:
                continue
            if pid in self.taskbar_list and update_button == False:
                continue
            #quick fix for nautilus initial class
            if "org.gnome.nautilus" in wm_class:
                initial_title = "nautilus"
            button = self.utils.CreateTaskbarLauncher(wm_class, address, title, initial_title, orientation, class_style)
            self.taskbar.append(button)
            self.buttons_pid[pid] = [button, initial_title, address]
            self.buttons_address[address] = [button, title]
            self.taskbar_list.append(pid)                     
        return True
    

    def update_taskbar(self, pid, wm_class, address, initial_title, title, orientation, class_style, callback=None):
        button = self.utils.CreateTaskbarLauncher(wm_class, address, title, initial_title, orientation, class_style)
        self.taskbar.append(button)
        self.buttons_pid[pid] = [button, initial_title, address]
        self.buttons_address[address] = [button, title]                  
        return True

    
    def check_pids(self):   
        instance = Hyprland()
        if not instance.get_workspace_by_name("OVERVIEW"):
            return True
        #since I am lazy to verify what could possibly go wrong
        #then pass exception to always this function return true
        #so the glib.timeout won't stop to check
        try:
            active_window = instance.get_active_window()
            all_pids = [i.pid for i in instance.get_windows() if i.wm_class]
            if all_pids != self.all_pids:
                self.taskbar_remove()
                self.all_pids = all_pids
                self.Taskbar("h", "taskbar")
            return True
            initial_title = active_window.initial_title
            if initial_title == "zsh":
                address = active_window.address
                title = active_window.title
                wm_class = active_window.wm_class
                #quick fix for nautilus initial class
                if "org.gnome.nautilus" in wm_class.lower():
                    initial_title = "nautilus"
                pid = active_window.pid
                if address in self.buttons_address:
                    addr = self.buttons_address[address]
                    btn = addr[0]
                    btn_title = addr[1]
                    if title != btn_title :
                        self.taskbar.remove(btn)
                        self.update_taskbar(pid, wm_class, address, initial_title, title, "h", "taskbar")

        except:
            pass  
        return True
        

    def taskbar_remove(self):
        instance = Hyprland()
        all_pids = [i.pid for i in instance.get_windows() if i.wm_class]
        all_addresses = [i.address for i in instance.get_windows() if i.wm_class]
        for pid in self.buttons_pid.copy():
            button = self.buttons_pid[pid][0]
            address = self.buttons_pid[pid][2]
            if pid not in all_pids and address not in all_addresses:
                try:
                    self.taskbar.remove(button)
                    self.taskbar_list.remove(pid)
                except ValueError:
                    pass  
        return True

                
    # Append a window to the dockbar
    def dockbar_append(self, *_):
        w = self.instance.get_active_window()
        initial_title = w.initial_title.lower()
        wclass = w.wm_class.lower()
        icon = initial_title
        cmd = initial_title

        # Adjusting for special cases like zsh or bash
        if initial_title in ["zsh", "bash"]:
            title = w.title.split(" ")[0]
            cmd = f"kitty --hold {title}"
            icon = wclass

        # Handling icon mapping
        try:
            icon = self.panel_cfg["change_icon_title"][icon]
        except KeyError:
            print(f"Icon mapping not found for {icon}")
            
            
        try:
            for deskfile in  os.listdir(self.webapps_applications):
                if deskfile.startswith("chrome") or deskfile.startswith("msedge"):
                    pass
                else:
                    continue
                webapp_path = os.path.join(self.webapps_applications, deskfile)
                #necessary initial title without lower()
                desktop_file_found = self.utils.search_str_inside_file(webapp_path, w.initial_title)

                if desktop_file_found:
                    cmd = "gtk-launch {0}".format(deskfile)
                    icon = deskfile.split(".desktop")[0]
                    break
        except:
            pass
                

        # Update the dockbar configuration
        with open(self.dockbar_config, "r") as f:
            config = toml.load(f)
        new_data = {initial_title: {"cmd": cmd, "icon": icon, "wclass":wclass, "initial_title":initial_title}}
        updated_data = ChainMap(new_data, config)
        with open(self.dockbar_config, "w") as f:
            toml.dump(updated_data, f)
            

        # Create and append button to the dockbar
        button = self.utils.CreateButton(icon, cmd, initial_title, wclass, initial_title)
        self.dockbar.append(button)

    # Remove a command from the dockbar configuration
    def dockbar_remove(self, cmd):
        with open(self.dockbar_config, "r") as f:
            config = toml.load(f)
        del config[cmd]
        with open(self.dockbar_config, "w") as f:
            toml.dump(config, f)

    # Join multiple windows of the same class into one workspace
    def join_windows(self, *_):
        activewindow = out("hyprctl activewindow".split()).decode()
        wclass = activewindow.split("class: ")[-1].split("\n")[0]
        activeworkspace = activewindow.split("workspace: ")[-1].split(" ")[0]
        j = out("hyprctl -j clients".split()).decode()
        clients = json.loads(j)
        for client in clients:
            if wclass in client["class"]:
                move_clients = f"hyprctl dispatch movetoworkspace {activeworkspace},address:{client['address']}".split()
                gotoworkspace = f"hyprctl dispatch workspace name:{activeworkspace}".split()
                call(move_clients)
                call(gotoworkspace)

    # Launch a docked application
    def dock_launcher(self, cmd):
        processes = psutil.process_iter()
        for process in processes:
            if process.name() in cmd or cmd in process.name():
                call(f"hyprctl dispatch workspace name:{cmd}".split())
                return
        if ";" in cmd:
            for line in cmd.split(";"):
                try:
                    call(f"hyprctl dispatch workspace name:{cmd}".split())
                    Popen(line.split(), start_new_session=True)
                except Exception as e:
                    print(e)
        else:
            call(f"hyprctl dispatch workspace name:{cmd}".split())
            Popen(cmd.split(), start_new_session=True)

    # Initialize Hyprland instance
    def HyprlandInstance(self):
        return Hyprland()
