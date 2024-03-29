import os
import signal
import toml
import gi
import json
import psutil
from subprocess import Popen, call, check_output as out
from collections import ChainMap
import threading

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio, GObject
from ..core.create_panel import *
from ..core.utils import Utils
from hyprpy import Hyprland
import numpy as np


class InvalidGioTaskError(Exception):
    pass


class AlreadyRunningError(Exception):
    pass


class BackgroundTaskbar(GObject.Object):
    __gtype_name__ = "BackgroundTaskbar"

    def __init__(self, function, finish_callback, **kwargs):
        super().__init__(**kwargs)

        self.function = function
        self.finish_callback = finish_callback
        self._current = None

    def start(self):
        if self._current:
            AlreadyRunningError("Task is already running")

        finish_callback = lambda self, task, nothing: self.finish_callback()

        task = Gio.Task.new(self, None, finish_callback, None)
        task.run_in_thread(self._thread_cb)

        self._current = task

    @staticmethod
    def _thread_cb(task, self, task_data, cancellable):
        try:
            retval = self.function()
            task.return_value(retval)
        except Exception as e:
            task.return_value(e)

    def finish(self):
        task = self._current
        self._current = None

        if not Gio.Task.is_valid(task, self):
            raise InvalidGioTaskError()

        value = task.propagate_value().value

        if isinstance(value, Exception):
            raise value

        return value


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
        # this instance does not update, this is just to initialize the var
        instance = Hyprland()
        self.all_pids = [i.pid for i in instance.get_windows() if i.wm_class]
        self.timeout_taskbar = None
        self.buttons_pid = {}
        self.buttons_address = {}
        self.has_taskbar_started = False
        self.stored_windows = []
        self.hyprinstance = Hyprland()
        self.window_created_now = None

    # Start the Dockbar application
    def do_start(self):
        # Set up a timeout to periodically check process IDs
        # GLib.timeout_add(300, self.check_pids)
        self.start_thread_hyprland()
        # Populate self.stored_windows during panel start
        instance = Hyprland()
        self.stored_windows = [i.pid for i in instance.get_windows() if i.pid != -1]

        # Read configuration from topbar toml
        with open(self.topbar_config, "r") as f:
            panel_toml = toml.load(f)

            # Iterate over panel configurations
            for p in panel_toml:
                # Check if the panel is positioned on the left side
                if "left" == p:
                    exclusive = panel_toml[p]["Exclusive"] == "True"
                    position = panel_toml[p]["position"]

                    # Create a left panel and associated components
                    self.left_panel = CreatePanel(
                        self, "LEFT", position, exclusive, 32, 0, "LeftBar"
                    )
                    self.dockbar = self.utils.CreateFromAppList(
                        self.dockbar_config, "v", "LeftBar", self.join_windows
                    )
                    self.add_launcher = Gtk.Button()
                    self.add_launcher.set_icon_name("tab-new-symbolic")
                    self.add_launcher.connect("clicked", self.dockbar_append)
                    self.dockbar.append(self.add_launcher)
                    self.left_panel.set_content(self.dockbar)
                    self.left_panel.present()

                # Check if the panel is positioned at the bottom
                if "bottom" == p:
                    exclusive = panel_toml[p]["Exclusive"] == "True"
                    position = panel_toml[p]["position"]

                    # Create a bottom panel and associated components
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

                    # Start the taskbar list for the bottom panel
                    # Remaining check pids will be handled later
                    self.Taskbar("h", "taskbar")

    def is_any_window_created_or_closed(self):
        # Create an instance of the Hyprland class
        instance = Hyprland()

        # Get the addresses of currently open windows
        updated_windows = [i.pid for i in instance.get_windows() if i.pid != -1]

        # Find the difference between the stored windows and the updated windows
        diff_created = np.setdiff1d(self.stored_windows, updated_windows)
        diff_updated = np.setdiff1d(updated_windows, self.stored_windows)

        # Combine the differences to check if any window was created or closed
        difference = [np.concatenate((diff_created, diff_updated))]

        # Check if there is any difference
        try:
            if difference[0].any():
                # Update the stored windows and return True if there is a difference
                self.stored_windows = updated_windows
                return True
        except Exception as e:
            print(e)
        else:
            # No change in windows, return False
            return False

    def on_hyprwatch_finished(self):
        # non working code
        try:
            retval = self.hyprwatch_task.finish()
            print(retval)
        except Exception as err:
            print(err)

    def start_thread_hyprland(self):
        self.hyprwatch_task = BackgroundTaskbar(
            self.HyprlandWatch, lambda: self.on_hyprwatch_finished
        )
        self.hyprwatch_task.start()

    def hyprland_instance_watch(self):
        self.hyprinstance.signal_window_destroyed.connect(
            self.hyprland_window_destroyed
        )

        self.hyprinstance.signal_window_created.connect(self.hyprland_window_created)

        self.hyprinstance.signal_active_window_changed.connect(
            self.hyprland_window_changed
        )

    def hyprland_window_changed(self, sender, **kwargs):
        # if no windows, window_created signal will conflict with window_changed
        # the issue will be no new button will be appended to the taskbar
        # necessary to check if the window list is empity
        if not len(self.hyprinstance.get_windows()) == 0:
            self.update_active_window_shell()

    def hyprland_window_created(self, sender, **kwargs):
        self.Taskbar("h", "taskbar")

    def hyprland_window_destroyed(self, sender, **kwargs):
        self.taskbar_remove()

    def HyprlandWatch(self):
        GLib.idle_add(self.hyprland_instance_watch)
        self.hyprinstance.watch()

    def Taskbar(self, orientation, class_style, update_button=False, callback=None):
        # Create an instance of Hyprland to access window information
        instance = self.hyprinstance

        # Filter windows to exclude those already in the taskbar
        all_windows = [
            i
            for i in instance.get_windows()
            if i.wm_class and i.wm_class not in self.taskbar_list
        ]

        # If no new windows, exit the function
        if not all_windows or all_windows == []:
            return True

        # Load configuration from dockbar_config file
        with open(self.dockbar_config, "r") as f:
            config = toml.load(f)

        # Extract desktop_file paths from the configuration
        launchers_desktop_file = [config[i]["desktop_file"] for i in config]

        for i in all_windows:
            wm_class = i.wm_class.lower()
            address = i.address.lower()
            initial_title = i.initial_title.lower()

            # some classes and initial titles has whitespaces which will lead to not found icons
            if " " in initial_title:
                initial_title = initial_title.split()[0]
            if " " in wm_class:
                wm_class = wm_class.split()[0]

            title = i.title
            pid = i.pid

            # Skip windows with wm_class found in launchers_desktop_file if update_button is False
            if wm_class in launchers_desktop_file and not update_button:
                continue

            # Skip windows with pid found in self.taskbar_list if update_button is False
            if pid in self.taskbar_list and not update_button:
                continue

            # Quick fix for nautilus initial class
            if "org.gnome.nautilus" in wm_class:
                initial_title = "nautilus"

            # Create a taskbar launcher button using utility function
            button = self.utils.create_taskbar_launcher(
                wm_class, address, title, initial_title, orientation, class_style
            )
            print(button.get_name())
            # Append the button to the taskbar
            self.taskbar.append(button)

            # Store button information in dictionaries for easy access
            self.buttons_pid[pid] = [button, initial_title, address]
            self.buttons_address[address] = [button, title]

            # Add the pid to the taskbar_list to keep track of added windows
            self.taskbar_list.append(pid)

        # Return True to indicate successful execution of the Taskbar function
        return True

    def update_taskbar(
        self,
        pid,
        wm_class,
        address,
        initial_title,
        title,
        orientation,
        class_style,
        callback=None,
    ):
        # Create a taskbar launcher button using utility function
        button = self.utils.create_taskbar_launcher(
            wm_class, address, title, initial_title, orientation, class_style
        )

        # Append the button to the taskbar
        self.taskbar.append(button)

        # Store button information in dictionaries for easy access
        self.buttons_pid[pid] = [button, initial_title, address]
        self.buttons_address[address] = [button, title]

        # Return True to indicate successful execution of the update_taskbar function
        return True

    def update_active_window_shell(self):
        instance = Hyprland()
        active_window = instance.get_active_window()
        initial_title = active_window.initial_title

        # Check if the active window has the title "zsh"
        if initial_title in ["zsh", "fish", "bash"]:
            address = active_window.address
            title = active_window.title
            wm_class = active_window.wm_class
            pid = active_window.pid

            # Quick fix for nautilus initial class
            if "org.gnome.nautilus" in wm_class.lower():
                initial_title = "nautilus"

            # Check if the address is in buttons_address
            if address in self.buttons_address:
                addr = self.buttons_address[address]
                btn = addr[0]
                btn_title = addr[1]

                # Check if the title has changed
                if title != btn_title:
                    self.taskbar.remove(btn)
                    self.update_taskbar(
                        pid, wm_class, address, initial_title, title, "h", "taskbar"
                    )

    def check_pids(self):
        # Create an instance of Hyprland
        instance = Hyprland()

        # *** Need a fix since this code depends on the Hyprshell plugin
        if not instance.get_workspace_by_name("OVERVIEW"):
            return True

        # do not check anything if no window closed or created
        if not self.is_any_window_created_or_closed():
            self.update_active_window_shell()
            return True

        try:
            # Get the active window and all PIDs of windows with wm_class
            active_window = instance.get_active_window()
            all_pids = [i.pid for i in instance.get_windows() if i.wm_class]

            # Check if the PIDs have changed
            if all_pids != self.all_pids:
                self.taskbar_remove()
                self.all_pids = all_pids
                self.Taskbar("h", "taskbar")
                return True
            self.update_active_window_shell()
        except Exception as e:
            print(e)

        # Return True to indicate successful execution of the check_pids function
        return True

    def taskbar_remove(self):
        # Create an instance of Hyprland
        instance = self.hyprinstance

        # Get all active PIDs and addresses with wm_class
        all_pids = [i.pid for i in instance.get_windows() if i.wm_class]
        all_addresses = [i.address for i in instance.get_windows() if i.wm_class]

        # Iterate over copied dictionary to avoid concurrent modification
        for pid in self.buttons_pid.copy():
            button = self.buttons_pid[pid][0]
            address = self.buttons_pid[pid][2]

            # Check if the PID or address is not in the current list of windows
            if pid not in all_pids and address not in all_addresses:
                try:
                    # Remove button and associated data
                    self.taskbar.remove(button)
                    self.taskbar_list.remove(pid)
                    del self.buttons_pid[pid]
                    del self.buttons_address[address]
                except ValueError:
                    pass

        # Return True to indicate successful execution of the taskbar_remove function
        return True

    # Append a window to the dockbar
    def dockbar_append(self, *_):
        w = self.instance.get_active_window()
        initial_title = w.initial_title.lower()
        wclass = w.wm_class.lower()
        wclass = "".join(wclass)
        icon = initial_title
        cmd = initial_title
        desktop_file = ""

        # Adjusting for special cases like zsh or bash
        if initial_title in ["zsh", "bash", "fish"]:
            title = w.title.split(" ")[0]
            cmd = f"kitty --hold {title}"
            icon = wclass

        # Handling icon mapping
        try:
            icon = self.panel_cfg["change_icon_title"][icon]
        except KeyError:
            print(f"Icon mapping not found for {icon}")

        try:
            for deskfile in os.listdir(self.webapps_applications):
                if (
                    deskfile.startswith("chrome")
                    or deskfile.startswith("msedge")
                    or deskfile.startswith("FFPWA-")
                ):
                    pass
                else:
                    continue
                webapp_path = os.path.join(self.webapps_applications, deskfile)
                # necessary initial title without lower()
                desktop_file_found = self.utils.search_str_inside_file(
                    webapp_path, w.initial_title
                )

                if desktop_file_found:
                    cmd = "gtk-launch {0}".format(deskfile)
                    icon = deskfile.split(".desktop")[0]
                    desktop_file = deskfile
                    break
        except Exception as e:
            print(e)

        # Update the dockbar configuration
        with open(self.dockbar_config, "r") as f:
            config = toml.load(f)
        new_data = {
            initial_title: {
                "cmd": cmd,
                "icon": icon,
                "wclass": wclass,
                "initial_title": initial_title,
                "desktop_file": desktop_file,
                "name": wclass,
            }
        }
        updated_data = ChainMap(new_data, config)
        with open(self.dockbar_config, "w") as f:
            toml.dump(updated_data, f)

        # Create and append button to the dockbar
        button = self.utils.CreateButton(
            icon, cmd, initial_title, wclass, initial_title
        )
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
                gotoworkspace = (
                    f"hyprctl dispatch workspace name:{activeworkspace}".split()
                )
                call(move_clients)
                call(gotoworkspace)

    # Initialize Hyprland instance
    def HyprlandInstance(self):
        return Hyprland()
