# Mac System Configurator

Manage and apply Mac system settings with ease through a beautiful command-line interface.

## Overview

This tool manages macOS system settings through configuration profiles. Create different profiles for different scenarios (Work, Home, Presentation, etc.) and switch between them effortlessly.

---

## 💻 Command-Line Interface

A fully-featured terminal application with a beautiful Rich-powered UI.

### Features
- ✅ Multiple configuration profiles
- ✅ JSON Schema-based settings validation
- ✅ Live system value comparison
- ✅ Rich terminal UI with tables and panels
- ✅ Generate AppleScript for startup execution
- ✅ Manage startup items, background apps, and system extensions
- ✅ Admin permission handling

### Quick Start

```bash
# Install dependencies
pip3 install rich jsonschema

# Run the configurator
python3 python_app/mac_configurator.py

# Or create an alias for quick access
echo "alias cfg='python3 $(pwd)/python_app/mac_configurator.py'" >> ~/.zshrc
source ~/.zshrc
cfg
```

📖 [Full CLI documentation →](python_app/README.md)

---

## Available Settings

Comprehensive set of macOS settings:

### 🌐 Network
- WiFi enabled/disabled (requires admin)

### 🔊 Audio
- Input muted
- Output volume (0-100)

### 📱 Dock
- Auto-hide
- Position (left/bottom/right)

### 📁 Finder
- Show hidden files
- Show all file extensions

### ⚙️ System
- Screenshot save location

### 🚀 Startup Items
- Block/allow applications from launching at login

### ⏱️ Background Apps
- Control background app permissions

### 🔌 System Extensions
- Enable/disable system extensions
- Manage widgets, Safari extensions, Quick Look plugins, etc.

---

## Configuration

### Configuration Directory

The app uses `~/MacConfigurator/` to store configuration profiles:

```
~/MacConfigurator/
├── Work_config.json
├── Home_config.json
├── Presentation_config.json
└── apply_Work_settings.scpt
```

### Settings Schema

Settings are defined in `shared/settings_schema.json` using JSON Schema format for validation.

### Configuration Format

Example `Work_config.json`:
```json
{
  "settings": {
    "audio_output_volume": 50,
    "dock_position": "bottom",
    "dock_autohide": false,
    "wifi_enabled": true
  }
}
```

---

## Project Structure

```
mac_configurator/
├── python_app/              # Python CLI application
│   ├── mac_configurator.py  # Main CLI script
│   ├── README.md            # CLI documentation
│   └── screenshots/         # CLI interface examples
│
└── shared/                  # Shared resources
    └── settings_schema.json # Settings definitions
```

---

## Development

### Adding New Settings

The schema-first approach:

1. **Update `shared/settings_schema.json`**
   ```json
   {
     "your_setting_key": {
       "type": "boolean",
       "title": "Your Setting Name",
       "description": "What this setting does",
       "category": "CategoryName",
       "handler": "YourHandler",
       "requires_admin": false
     }
   }
   ```

2. **Implement handler in Python**
   - Add getter/setter methods
   - Register in handler map

### Contributing

Contributions are welcome!

---

## Requirements

- macOS
- Python 3.7+
- `rich` library
- `jsonschema` library

---

## License

[View License](LICENSE)

---

## Screenshots

The configurator features a beautiful, color-coded Rich terminal interface:

### Main Menu
```
╭────────────────────────────────────────────────────────────────╮
│                   Mac System Configurator                      │
╰────────────────────────────────────────────────────────────────╯

Config directory: ~/MacConfigurator

    Available
    Configurations

┌───┬─────────────┐
│ # │ Config Name │
├───┼─────────────┤
│ 1 │ Work        │
│ 2 │ Home        │
│ 3 │ Presentation│
└───┴─────────────┘

┌─────┬──────────────────────────────┐
│ [1] │ Edit Config (select number)  │
│     │ Create New Config            │
│     │ Delete a Config              │
│ [e] │ Exit                         │
└─────┴──────────────────────────────┘

Select option: ▌
```

### Manage Settings - Category Selection
```
Manage Settings - Select Category

┌─────┬────────────────┐
│ [1] │ 🌐 Network     │
│ [2] │ 🔊 Audio       │
│ [3] │ 📱 Dock        │
│ [4] │ 📁 Finder      │
│ [5] │ ⚙️  System     │
└─────┴────────────────┘

Press Enter to return to main menu

Select category (): ▌
```

Categories are color-coded for easy identification.

### Finder Settings View
```
Finder Settings

┌────────┬──────────────────────┬────────────┬─────────┬────────┐
│ Option │ Setting              │ Configured │ Current │ Status │
├────────┼──────────────────────┼────────────┼─────────┼────────┤
│ [1]    │ Show Hidden Files    │ False      │ False   │   ✓    │
│ [2]    │ Show All Extensions  │ True       │ True    │   ✓    │
└────────┴──────────────────────┴────────────┴─────────┴────────┘

Press Enter to return to category menu

Select setting to edit (): ▌
```

Settings display shows:
- **Configured** (Yellow) = Your configured values
- **Current** (Magenta) = Current actual system values
- **✓** = Matched (settings in sync)
- **⚠** = Mismatched (configured value differs from system)
- **○** = Not configured (using system defaults)
- **🔒** = Requires admin privileges

### AppleScript Generation
```
┌───────────────────────┐
│ AppleScript Generated │
└───────────────────────┘

✓ Script saved to: ~/MacConfigurator/apply_Work_settings.scpt

To run manually:
  osascript ~/MacConfigurator/apply_Work_settings.scpt

To add to startup:
  1. Open System Settings > General > Login Items
  2. Click '+' under 'Open at Login'
  3. Select: ~/MacConfigurator/apply_Work_settings.scpt

Press Enter to continue...▌
```

---

## Roadmap

### Completed ✅
- [x] Core settings management
- [x] Multiple profiles
- [x] AppleScript generation
- [x] Startup items management
- [x] System extensions management

### Future Enhancements
- [ ] Additional system settings
- [ ] Configuration import/export
- [ ] Settings templates
- [ ] Automated testing framework

---

**Made with ❤️ for macOS**
