# Hyprpanel
##### _Gtk4/Adwaita panel made for hyprland_

Hyprpanel doesn't implement systray and taskbar, and there are no plans to implement them.

### How to Install

```
git clone https://github.com/killown/hyprpybar
cd hyprpybar
sh install
mkdir ~/.config/hyprpanel; cp config/* ~/.config/hyprpanel
```
 [<img src="https://github.com/killown/hyprpybar/assets/24453/04e99ccc-7351-4184-9407-184e1e85b474" width="100%">](https://www.youtube.com/watch?v=UYnr8RLHP7c "Youtube Video")

The info panel is intended to be used with https://github.com/killown/hyprshell plugin

### Current features
- Dockbar
- Information panel with numerous features
- Top panel with a GNOME appearance
- Custom CSS customizations
- Panel for workspace navigation
- Bar with various positions: on top (exclusive) or in the background behind all windows
- Easily create custom menus using TOML
- Configuration for custom gesture actions for mouse buttons and scrolling
- Configuration for custom gestures for the top left and top right panels, offering more command possibilities
- Lightweight with low CPU usage, as it doesn't monitor Bluetooth, network, and other functionalities
- Adjust sound volume using the mouse wheel in the top bar.

#### Info from focused window
- CPU
- MEM
- Disk
- take notes of every window
- pid
- current workspace

#### Create custom output in the top bar using toml

```
[some_name]
refresh = 1000 #in ms
position = "center" #left center right
cmd = "command" #command or script
css_class = "css_class" #to customize the widget look

```

#### Create new menus in the top bar using toml

```
[[MyMenu.item_1]]
cmd = "command"
name = "Menu Label"

[[MyMenu.item_2]]
cmd = "command"
name = "Menu Label"
submenu = "submenu_name"

```

## License

Hyprpanel is licensed under the MIT license. [See LICENSE for more information](https://github.com/killown/hyprpybar/blob/main/LICENSE).
