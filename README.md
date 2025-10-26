# Mac System Configurator

Manage and apply Mac system settings with ease - available in both CLI and native macOS GUI versions.

## Overview

This project provides tools to manage macOS system settings through configuration profiles. Create different profiles for different scenarios (Work, Home, Presentation, etc.) and switch between them effortlessly.

Both versions share the same configuration format and settings schema, so you can use whichever interface you prefer.

---

## 📱 Native macOS App (SwiftUI)

**Status:** 🚧 In Development

A beautiful, native macOS application built with SwiftUI.

### Features (Planned)
- Native macOS interface matching System Settings design
- Sidebar navigation by category
- Real-time sync indicators
- Visual settings controls (toggles, sliders, pickers)
- Profile management with quick switching
- Live preview of settings changes
- Menu bar integration (optional)

### Getting Started

The SwiftUI app is located in the `MacConfigurator/` directory.

To build and run:
1. Open `MacConfigurator/MacConfigurator.xcodeproj` in Xcode
2. Build and run (⌘R)

The GUI app shares configuration files with the CLI version in `~/MacConfigurator/`.

📖 [More details →](MacConfigurator/README.md)

---

## 💻 Command-Line Interface (Python)

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

Both versions support the same comprehensive set of macOS settings:

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

### Shared Configuration Directory

Both apps use `~/MacConfigurator/` to store configuration profiles:

```
~/MacConfigurator/
├── Work_config.json
├── Home_config.json
├── Presentation_config.json
└── apply_Work_settings.scpt
```

### Settings Schema

Settings are defined in `shared/settings_schema.json` using JSON Schema format. This ensures consistent validation across both CLI and GUI versions.

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
mac_start/
├── python_app/              # Python CLI application
│   ├── mac_configurator.py  # Main CLI script
│   ├── README.md            # CLI documentation
│   └── screenshots/         # CLI interface examples
│
├── MacConfigurator/         # SwiftUI macOS app
│   ├── MacConfigurator/     # App source code
│   │   ├── Models/          # Data models
│   │   ├── Views/           # SwiftUI views
│   │   ├── Services/        # System handlers
│   │   └── Resources/       # Assets and resources
│   └── MacConfigurator.xcodeproj
│
└── shared/                  # Shared resources
    └── settings_schema.json # Settings definitions
```

---

## Development

### Adding New Settings

Both apps use the schema-first approach:

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

2. **Implement handler in Python** (for CLI)
   - Add getter/setter methods
   - Register in handler map

3. **Implement handler in Swift** (for GUI)
   - Add to SettingsApplicator
   - Settings automatically appear in UI

### Contributing

Contributions are welcome! Whether you prefer Python or Swift, you can contribute to either version.

---

## Requirements

### CLI (Python)
- macOS
- Python 3.7+
- `rich` library
- `jsonschema` library

### GUI (SwiftUI)
- macOS 13.0 (Ventura) or later
- Xcode 14.0+
- Swift 5.7+

---

## License

[View License](LICENSE)

---

## Which Version Should I Use?

**Use the CLI if you:**
- Prefer terminal-based workflows
- Want to automate with scripts
- Need it to work on older macOS versions
- Want a lightweight solution

**Use the GUI if you:**
- Prefer native macOS applications
- Want visual controls and animations
- Like the System Settings aesthetic
- Prefer point-and-click over typing

**Use both if you:**
- Want the best of both worlds
- Like switching between terminal and GUI
- Want to try different interfaces

Both versions share the same configuration files, so you can seamlessly switch between them!

---

## Screenshots

### CLI Interface
![CLI Main Menu](python_app/screenshots/main_menu.png)

### GUI Interface
🚧 Coming soon

---

## Roadmap

### CLI (Python) ✅
- [x] Core settings management
- [x] Multiple profiles
- [x] AppleScript generation
- [x] Startup items management
- [x] System extensions management

### GUI (SwiftUI) 🚧
- [x] Project structure
- [x] Core models and views
- [ ] Complete Xcode project setup
- [ ] Settings handlers implementation
- [ ] Profile management UI
- [ ] Menu bar app mode
- [ ] App icon and assets
- [ ] First release

---

**Made with ❤️ for macOS**
