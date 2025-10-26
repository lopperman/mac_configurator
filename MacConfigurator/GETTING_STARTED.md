# Getting Started with Mac Configurator SwiftUI

## 🎉 Project Setup Complete!

Your Xcode project is ready to build and run.

## Quick Start

### 1. Open the Project

```bash
open MacConfigurator.xcodeproj
```

Or from Finder:
- Navigate to `MacConfigurator/` folder
- Double-click `MacConfigurator.xcodeproj`

### 2. Install Xcode (if needed)

If you only have Command Line Tools installed, you'll need the full Xcode:

1. Download from the Mac App Store: [Xcode](https://apps.apple.com/app/xcode/id497799835)
2. Open Xcode once after installation to complete setup
3. Run: `sudo xcode-select --switch /Applications/Xcode.app`

### 3. Build and Run

Once Xcode is open:

1. **Select the scheme**: "MacConfigurator" should already be selected in the toolbar
2. **Choose "My Mac" as the destination** (next to the scheme selector)
3. **Press ⌘R** or click the Play button to build and run

### 4. First Build

The first build may take a minute as it compiles all Swift files. Subsequent builds will be faster.

## Project Structure

```
MacConfigurator/
├── MacConfigurator.xcodeproj/      # Xcode project
│   ├── project.pbxproj            # Project settings ✅
│   └── xcshareddata/
│       └── xcschemes/
│           └── MacConfigurator.xcscheme ✅
│
└── MacConfigurator/                # Source code
    ├── MacConfiguratorApp.swift    # App entry point ✅
    ├── ContentView.swift           # Main UI ✅
    ├── Info.plist                  # App metadata ✅
    ├── MacConfigurator.entitlements ✅
    │
    ├── Models/                     # Data models ✅
    │   ├── SettingCategory.swift
    │   ├── ConfigProfile.swift
    │   └── Setting.swift
    │
    ├── Views/                      # UI components ✅
    │   ├── SettingsCategoryView.swift
    │   ├── NewProfileSheet.swift
    │   └── SettingsView.swift
    │
    ├── Services/                   # Business logic ✅
    │   ├── SettingsSchema.swift
    │   └── SettingsApplicator.swift
    │
    └── Resources/                  # Assets ✅
        ├── Assets.xcassets/
        └── settings_schema.json
```

## Expected Result

When you run the app, you'll see:

1. **Main Window** with:
   - Sidebar showing categories (Network, Audio, Dock, etc.)
   - Profile picker in toolbar
   - "Apply Settings" button

2. **Settings Interface**:
   - Select a category to view its settings
   - Toggle switches for boolean settings
   - Sliders for numeric values
   - Dropdowns for choices
   - Status indicators showing sync state

## Troubleshooting

### "No scheme" error
- Make sure you opened the `.xcodeproj` file, not a folder
- The scheme should be automatically selected

### Build errors about missing files
- Clean build folder: Product → Clean Build Folder (⇧⌘K)
- Rebuild: Product → Build (⌘B)

### "Code signing" errors
- Go to project settings → Signing & Capabilities
- Select your development team (or use "Sign to Run Locally")
- Make sure "Automatically manage signing" is checked

### App crashes on launch
- Check Console.app for error messages
- Ensure `settings_schema.json` is in Resources folder
- Verify all Swift files compile without errors

## Next Steps

### 1. Test Basic Functionality
- Create a new profile
- Switch between categories
- Adjust some settings
- Try the Apply Settings button

### 2. Implement Missing Features
- Real-time system value fetching (currently shows nil)
- Complete settings handlers
- Error handling and user feedback
- Profile deletion UI

### 3. Polish
- Add app icon
- Implement search
- Add keyboard shortcuts
- Create menu bar mode

### 4. Advanced
- Sandboxing configuration
- Code signing for distribution
- Add unit tests
- Localization

## Configuration

The app uses the same configuration directory as the Python CLI:

- **Config Location**: `~/MacConfigurator/`
- **Shared Schema**: `../shared/settings_schema.json` (also copied to Resources)
- **Profile Format**: `[ProfileName]_config.json`

You can create/edit profiles in either the CLI or GUI - they'll both see the same files!

## Development Tips

### Live Preview
SwiftUI supports live previews in Xcode. Look for the "Resume" button in the canvas (⌥⌘⏎).

### Hot Reload
Most UI changes update automatically while the app is running in debug mode.

### Debugging
- Set breakpoints by clicking line numbers
- Use `print()` statements (visible in Xcode console)
- View hierarchy debugger: Debug → View Debugging → Capture View Hierarchy

### Swift Documentation
- Option-click any symbol to see Quick Help
- ⌘-click to jump to definition
- ⌘/ to toggle comments

## Known Limitations

1. **System values not yet implemented** - Settings show configured values but not actual system state
2. **Apply settings partially implemented** - Basic handlers exist but need testing
3. **No error handling** - App may crash on invalid data
4. **Array/Dictionary settings** - Complex types show "Manage..." button but functionality not implemented
5. **No undo/redo** - Changes are immediately saved

## Resources

- [SwiftUI Documentation](https://developer.apple.com/documentation/swiftui/)
- [macOS App Development](https://developer.apple.com/macos/)
- [Python CLI Version](../python_app/README.md)
- [Main Project README](../README.md)

## Getting Help

If you encounter issues:

1. Check this guide's Troubleshooting section
2. Review Xcode console for error messages
3. Ensure all files are present and properly added to the project
4. Try cleaning and rebuilding

---

**Ready to build?** Run:
```bash
open MacConfigurator.xcodeproj
```

Then press ⌘R in Xcode!
