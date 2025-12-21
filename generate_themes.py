import json
import os
import colorsys

def adjust_color_brightness(hex_color, factor):
    # Remove hash
    hex_color = hex_color.lstrip('#')
    
    # Convert to RGB
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    # Convert to HSV
    h, s, v = colorsys.rgb_to_hsv(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)
    
    # Adjust Value (brightness)
    v = max(0, min(1, v * factor))
    
    # Convert back to RGB
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    
    # Convert back to Hex
    return '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))

colors = {
    "Electric Blue": "#2979FF",
    "Neon Cyan": "#00E5FF",
    "Emerald Green": "#2ECC71",
    "Mint Green": "#00C896",
    "Lime Green": "#AEEA00",
    "Amber Yellow": "#FFC107",
    "Golden Orange": "#FF9800",
    "Deep Orange": "#FF5722",
    "Coral Red": "#FF5252",
    "Crimson Red": "#D32F2F",
    "Hot Pink": "#FF4081",
    "Rose Pink": "#F06292",
    "Magenta": "#E040FB",
    "Royal Purple": "#7E57C2",
    "Indigo Blue": "#3F51B5",
    "Midnight Blue": "#1A237E",
    "Teal": "#009688",
    "Ocean Blue": "#0288D1",
    "Steel Blue": "#607D8B",
    "Slate Gray": "#455A64",
    "Cyber Yellow": "#FFD300",
    "Neon Green": "#39FF14",
    "Violet Glow": "#8F00FF",
    "Turquoise Glow": "#1DE9B6"
}

# Ensure themes directory exists
if not os.path.exists("themes"):
    os.makedirs("themes")

base_theme_structure = {
  "CTk": {
    "fg_color": ["#fcfcfc", "#2b2b2b"]
  },
  "CTkTopLevel": {
    "fg_color": ["#fcfcfc", "#2b2b2b"]
  },
  "CTkFrame": {
    "corner_radius": 6,
    "border_width": 0,
    "fg_color": ["#eeeeee", "#333333"],
    "top_fg_color": ["#dcdcdc", "#242424"],
    "border_color": ["#979da2", "#565b5e"]
  },
  "CTkButton": {
    "corner_radius": 6,
    "border_width": 0,
    "fg_color": ["{color}", "{color}"],
    "hover_color": ["{hover}", "{hover}"],
    "border_color": ["#3E454A", "#949A9F"],
    "text_color": ["#DCE4EE", "#DCE4EE"],
    "text_color_disabled": ["#F5F6F8", "#F5F6F8"]
  },
  "CTkLabel": {
    "corner_radius": 0,
    "fg_color": "transparent",
    "text_color": ["#000000", "#DCE4EE"]
  },
  "CTkEntry": {
    "corner_radius": 6,
    "border_width": 2,
    "fg_color": ["#F9F9FA", "#343638"],
    "border_color": ["#979DA2", "#565B5E"],
    "text_color": ["#000000", "#DCE4EE"],
    "placeholder_text_color": ["#525659", "#AAB0B5"]
  },
  "CTkCheckBox": {
    "corner_radius": 6,
    "border_width": 3,
    "fg_color": ["{color}", "{color}"],
    "border_color": ["#3E454A", "#949A9F"],
    "hover_color": ["{color}", "{color}"],
    "checkmark_color": ["#DCE4EE", "#DCE4EE"],
    "text_color": ["#000000", "#DCE4EE"],
    "text_color_disabled": ["#525659", "#AAB0B5"]
  },
  "CTkSwitch": {
    "corner_radius": 1000,
    "border_width": 3,
    "button_length": 0,
    "fg_color": ["#939BA2", "#4A4D50"],
    "progress_color": ["{color}", "{color}"],
    "button_color": ["#3E454A", "#949A9F"],
    "button_hover_color": ["#3E454A", "#949A9F"],
    "text_color": ["#000000", "#DCE4EE"],
    "text_color_disabled": ["#525659", "#AAB0B5"]
  },
  "CTkRadioButton": {
    "corner_radius": 1000,
    "border_width_checked": 6,
    "border_width_unchecked": 3,
    "fg_color": ["{color}", "{color}"],
    "border_color": ["#3E454A", "#949A9F"],
    "hover_color": ["{color}", "{color}"],
    "text_color": ["#000000", "#DCE4EE"],
    "text_color_disabled": ["#525659", "#AAB0B5"]
  },
  "CTkProgressBar": {
    "corner_radius": 1000,
    "border_width": 0,
    "fg_color": ["#939BA2", "#4A4D50"],
    "progress_color": ["{color}", "{color}"],
    "border_color": ["#979DA2", "#565B5E"]
  },
  "CTkSlider": {
    "corner_radius": 1000,
    "button_corner_radius": 1000,
    "border_width": 6,
    "button_length": 0,
    "fg_color": ["#939BA2", "#4A4D50"],
    "progress_color": ["{color}", "{color}"],
    "button_color": ["#3E454A", "#949A9F"],
    "button_hover_color": ["#3E454A", "#949A9F"]
  },
  "CTkOptionMenu": {
    "corner_radius": 6,
    "fg_color": ["{color}", "{color}"],
    "button_color": ["{hover}", "{hover}"],
    "button_hover_color": ["{hover}", "{hover}"],
    "text_color": ["#DCE4EE", "#DCE4EE"],
    "text_color_disabled": ["#F5F6F8", "#F5F6F8"]
  },
  "CTkScrollableFrame": {
    "label_fg_color": ["#979DA2", "#565B5E"]
  },
  "CTkComboBox": {
    "corner_radius": 6,
    "border_width": 2,
    "fg_color": ["#F9F9FA", "#343638"],
    "border_color": ["#979DA2", "#565B5E"],
    "button_color": ["#979DA2", "#565B5E"],
    "button_hover_color": ["#6E7174", "#7A848D"],
    "text_color": ["#000000", "#DCE4EE"],
    "text_color_disabled": ["#525659", "#AAB0B5"]
  },
  "CTkScrollbar": {
    "corner_radius": 1000,
    "border_spacing": 4,
    "border_width": 0,
    "fg_color": "transparent",
    "button_color": ["#757575", "#555555"],
    "button_hover_color": ["#606060", "#444444"]
  },
  "CTkSegmentedButton": {
    "corner_radius": 6,
    "border_width": 3,
    "fg_color": ["#979DA2", "#565B5E"],
    "selected_color": ["{color}", "{color}"],
    "selected_hover_color": ["{color}", "{color}"],
    "unselected_color": ["#979DA2", "#565B5E"],
    "unselected_hover_color": ["#6E7174", "#7A848D"],
    "text_color": ["#DCE4EE", "#DCE4EE"],
    "text_color_disabled": ["#F5F6F8", "#F5F6F8"]
  },
  "CTkTextbox": {
    "corner_radius": 6,
    "border_width": 0,
    "fg_color": ["#F9F9FA", "#1D1E1E"],
    "border_color": ["#979DA2", "#565B5E"],
    "text_color": ["#000000", "#DCE4EE"],
    "scrollbar_button_color": ["#757575", "#555555"],
    "scrollbar_button_hover_color": ["#606060", "#444444"]
  },
  "DropdownMenu": {
    "fg_color": ["#F9F9FA", "#292929"],
    "hover_color": ["{color}", "{color}"],
    "text_color": ["#000000", "#DCE4EE"]
  },
  "CTkFont": {
      "macOS": {
          "family": "SF Display",
          "size": 13,
          "weight": "normal"
      },
      "Windows": {
          "family": "Roboto",
          "size": 13,
          "weight": "normal"
      },
      "Linux": {
          "family": "Roboto",
          "size": 13,
          "weight": "normal"
      }
  }
}

for name, hex_val in colors.items():
    safe_name = name.lower().replace(" ", "_").replace("—_","").split("_—")[0].strip() # Handle potential copy paste artifacts if any, though input list is clean
    
    hover = adjust_color_brightness(hex_val, 0.8)
    
    # Create theme dict by replacing placeholders
    theme_json = json.dumps(base_theme_structure).replace('"{color}"', f'"{hex_val}"').replace('"{hover}"', f'"{hover}"')
    
    file_name = f"themes/{safe_name}.json"
    with open(file_name, 'w') as f:
        f.write(theme_json)

print("Themes generated!")
