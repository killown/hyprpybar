import os
import toml
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio, Gdk
from ..core.create_panel import *
from subprocess import Popen
from ..core.utils import Utils


class Dockbar(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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
    def do_start(self):
        with open(self.topbar_config, "r") as f:
            panel_toml = toml.load(f)
            for p in panel_toml:
                if "bottom" == p:
                    exclusive = True
                    if panel_toml[p]["Exclusive"] == "False":
                        exclusive = False
                    position = panel_toml[p]["position"]
                    self.bottom_panel = CreatePanel(self,
                        "BOTTOM", position, exclusive, 32, 0, "BottomBar"
                    )
                    self.dockbar = self.utils.CreateFromAppList(
                    "horizontal", self.dockbar_config, "BottomBar"
                    )   
                    self.bottom_panel.set_content(self.dockbar)     
                    self.bottom_panel.present()
        
    def dockbar_append(self, *_):
        w = self.instance.get_active_window()
        initial_title = w.initial_title.lower()
        icon = initial_title
        cmd = initial_title
        if initial_title == "zsh" or initial_title == "bash":
            title = w.title.split(" ")[0]
            cmd = "kitty --hold {0}".format(title)
            icon = title
        try:
            # some classes does not correspond the icon name, quick fix
            icon = self.panel_cfg["change_icon_title"][icon]
        except Exception as e:
            print(e)

        with open(self.dockbar_config, "r") as f:
            config = toml.load(f)

        new_data = {initial_title: {"cmd": cmd, "icon": icon}}

        updated_data = ChainMap(new_data, config)

        with open(self.dockbar_config, "w") as f:
            toml.dump(updated_data, f)

        button = self.CreateButton(icon, cmd, initial_title)
        self.dockbar.append(button)

    def dockbar_remove(self, cmd):
        with open(self.dockbar_config, "r") as f:
            config = toml.load(f)

        del config[cmd]
        with open(self.dockbar_config, "w") as f:
            toml.dump(config, f)
            
    def dock_launcher(self, cmd):
        processes = psutil.process_iter()
        for process in processes:
            if process.name() in cmd or cmd in process.name():
                call("hyprctl dispatch workspace name:{0}".format(cmd).split())
                return

        if ";" in cmd:
            for line in cmd.split(";"):
                try:
                    call("hyprctl dispatch workspace name:{0}".format(cmd).split())
                    Popen(line.split(), start_new_session=True)

                except Exception as e:
                    print(e)
        else:
            call("hyprctl dispatch workspace name:{0}".format(cmd).split())
            Popen(cmd.split(), start_new_session=True)
