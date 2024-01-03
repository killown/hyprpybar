# Hyprpanel
##### _Gtk4/Adwaita panel made for hyprland_

### How to Install

```
git clone https://github.com/killown/hyprpybar
cd hyprpybar
sh install
mkdir ~/.config/hyprpanel; cp config/* ~/.config/hyprpanel
```
 [<img src="https://github.com/killown/hyprpybar/assets/24453/04e99ccc-7351-4184-9407-184e1e85b474" width="50%">](https://www.youtube.com/watch?v=UYnr8RLHP7c "Youtube Video")

The info panel is intended to be used with https://github.com/killown/hyprshell plugin

### Current features
- Dockbar
- info panel with lots of features
- top panel with gnome look
- css cutomizations
- right panel for workspaces navigation
- bar with all positions, on top (exclusive) or (background) behind all windows
- Easily create custom menus with toml
- config for custom gesture actions for mouse buttons and scrolling
- config for custom gestures for top left and top right panel giving more possibilities of commands
- Lightweight, low cpu usage, since it's not watching for bluetooth, network and some more stuff
- increase and decrease sound volume with mouse wheel in the top bar

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

```

## License

Hyprpanel is licensed under the MIT license. [See LICENSE for more information](https://github.com/killown/hyprpybar/blob/main/LICENSE).
