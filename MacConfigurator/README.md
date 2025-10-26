# Mac Configurator - SwiftUI App

A beautiful, native macOS application for managing system settings.

## Status

🚧 **In Development** - Core structure is in place, Xcode project setup needed.

## Features

- **Native macOS Interface**: Built with SwiftUI, matching System Settings design language
- **Category Navigation**: Sidebar navigation for easy access to all setting categories
- **Profile Management**: Create and switch between multiple configuration profiles
- **Real-time Sync**: See configured vs. actual system values at a glance
- **Visual Controls**: Toggles, sliders, pickers, and more for intuitive settings management

## Architecture

```
MacConfigurator/
├── MacConfigurator/
│   ├── MacConfiguratorApp.swift      # App entry point
│   ├── ContentView.swift             # Main view with navigation
│   │
│   ├── Models/
│   │   ├── SettingCategory.swift     # Setting categories enum
│   │   ├── ConfigProfile.swift       # Configuration profile model
│   │   └── Setting.swift             # Individual setting definitions
│   │
│   ├── Views/
│   │   ├── SettingsCategoryView.swift # Category detail view
│   │   ├── NewProfileSheet.swift     # New profile creation
│   │   └── SettingsView.swift        # App preferences
│   │
│   ├── Services/
│   │   ├── SettingsSchema.swift      # Schema loader
│   │   └── SettingsApplicator.swift  # System settings handler
│   │
│   └── Resources/
│       └── (Assets, icons, etc.)
│
└── MacConfigurator.xcodeproj
```

## Building

### Prerequisites
- macOS 13.0 (Ventura) or later
- Xcode 14.0+
- Swift 5.7+

### Steps

1. **Open in Xcode**
   ```bash
   open MacConfigurator.xcodeproj
   ```

2. **Configure signing** (if needed)
   - Select the project in Xcode
   - Go to "Signing & Capabilities"
   - Choose your development team

3. **Build and Run**
   - Press ⌘R or click the Run button

## Configuration

The app shares configuration files with the Python CLI version:

- **Configuration Directory**: `~/MacConfigurator/`
- **Settings Schema**: `../shared/settings_schema.json`
- **Profile Format**: JSON files named `[ProfileName]_config.json`

## Implementation Status

### ✅ Completed
- [x] Project structure
- [x] Core data models (Profile, Setting, Category)
- [x] Main app layout and navigation
- [x] Settings schema loader
- [x] Category-based settings views
- [x] Profile picker UI
- [x] Basic setting controls (toggles, sliders, pickers)

### 🚧 In Progress
- [ ] Complete Xcode project file (.xcodeproj)
- [ ] System handlers for all settings
- [ ] Real-time system value fetching
- [ ] Settings application logic
- [ ] Profile management (create, delete, rename)

### 📋 Planned
- [ ] Menu bar app mode
- [ ] Keyboard shortcuts
- [ ] Search/filter settings
- [ ] Import/export profiles
- [ ] App icon and assets
- [ ] Sandboxing and entitlements
- [ ] Code signing and notarization

## Key Components

### Models

**ConfigProfile** - Represents a configuration profile with settings
- Loads/saves JSON files from `~/MacConfigurator/`
- Stores settings as key-value pairs
- Supports multiple profiles

**Setting** - Individual setting definition
- Parsed from settings_schema.json
- Includes metadata (title, description, category)
- Type information (boolean, integer, string, etc.)

**SettingCategory** - Categories for organizing settings
- Network, Audio, Dock, Finder, System, etc.
- Icons and colors for visual identification

### Views

**ContentView** - Main app layout
- Three-pane design (sidebar + detail)
- Profile picker in toolbar
- Apply settings button

**SettingsCategoryView** - Category detail view
- Lists all settings for a category
- Shows configured vs. system values
- Visual sync indicators

**SettingRow** - Individual setting row
- Displays setting name, description, status
- Renders appropriate control based on type
- Real-time updates

### Services

**SettingsSchema** - Schema parser
- Loads settings_schema.json
- Parses setting definitions
- Provides settings by category

**SettingsApplicator** - System handler
- Applies settings to macOS
- Uses AppleScript, defaults, shell commands
- Handles system restarts (Dock, Finder)

## Development

### Adding New Settings

Settings are automatically loaded from `shared/settings_schema.json`. No code changes needed to add new settings - just update the schema and implement the handler in `SettingsApplicator.swift`.

### Testing

The app can be tested alongside the Python CLI version:
1. Create/edit profiles in the CLI
2. Open the GUI app to see the same profiles
3. Changes are immediately synced (both read from same files)

## Next Steps

1. **Create proper Xcode project**
   - Currently need to generate `.xcodeproj` file
   - Can be done via Xcode or command line

2. **Implement system value fetching**
   - Add methods to read current system state
   - Display in UI alongside configured values

3. **Add missing UI components**
   - Profile deletion
   - Complex setting types (arrays, dictionaries)
   - Settings search

4. **Polish and refinement**
   - App icon
   - Better error handling
   - Loading states
   - Animations

## Contributing

Contributions welcome! The app is designed to be extensible:
- Settings are schema-driven
- Views are modular and reusable
- SwiftUI makes UI changes easy

## License

Same as the parent project - see [LICENSE](../LICENSE)

---

[← Back to main project](../README.md)
