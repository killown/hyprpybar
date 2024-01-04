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

    # Start the Dockbar application
    def do_start(self):
        with open(self.topbar_config, "r") as f:
            panel_toml = toml.load(f)
            for p in panel_toml:
                if "bottom" == p:
                    exclusive = panel_toml[p]["Exclusive"] == "True"
                    position = panel_toml[p]["position"]
                    self.bottom_panel = CreatePanel(
                        self, "BOTTOM", position, exclusive, 32, 0, "BottomBar"
                    )
                    self.dockbar = self.utils.CreateFromAppList(
                        "horizontal", self.dockbar_config, "BottomBar"
                    )
                    self.bottom_panel.set_content(self.dockbar)
                    self.bottom_panel.present()

    # Append a window to the dockbar
    def dockbar_append(self, *_):
        w = self.instance.get_active_window()
        initial_title = w.initial_title.lower()
        icon = cmd = initial_title

        # Adjusting for special cases like zsh or bash
        if initial_title in ["zsh", "bash"]:
            title = w.title.split(" ")[0]
            cmd = f"kitty --hold {title}"
            icon = title

        # Handling icon mapping
        try:
            icon = self.panel_cfg["change_icon_title"][icon]
        except KeyError:
            print(f"Icon mapping not found for {icon}")

        # Update the dockbar configuration
        with open(self.dockbar_config, "r") as f:
            config = toml.load(f)
        new_data = {initial_title: {"cmd": cmd, "icon": icon}}
        updated_data = ChainMap(new_data, config)
        with open(self.dockbar_config, "w") as f:
            toml.dump(updated_data, f)

        # Create and append button to the dockbar
        button = self.utils.CreateButton(icon, cmd, initial_title)
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
