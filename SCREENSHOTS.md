# How to Capture Screenshots

To add screenshots to the README, follow these steps:

## 1. Take Screenshots

Run the configurator and capture screenshots of:

1. **Main Menu** - `screenshots/main-menu.png`
   - Run: `python3 mac_configurator.py`
   - Take screenshot of the main menu

2. **Category Selection** - `screenshots/category-selection.png`
   - Select option 1 (Manage Settings)
   - Take screenshot of the category menu

3. **Settings View** - `screenshots/settings-view.png`
   - Select any category (e.g., Audio)
   - Take screenshot showing the settings table

4. **Admin Warning** - `screenshots/admin-warning.png` (optional)
   - Run without admin privileges to see the warning
   - Select a category with admin-required settings

5. **Edit Setting** - `screenshots/edit-setting.png`
   - Select a setting to edit
   - Take screenshot of the edit screen

6. **Apply Settings** - `screenshots/apply-settings.png`
   - From main menu, select option 2
   - Take screenshot of the apply screen with results

## 2. Screenshot Tools

On macOS, use:
- **Cmd + Shift + 4** - Select area to capture
- **Cmd + Shift + 4, then Space** - Capture specific window
- Or use the built-in Screenshot app

## 3. Terminal Recording (Alternative)

For better terminal screenshots, consider using:
- [Carbon](https://carbon.now.sh/) - Beautiful code/terminal screenshots
- [termshot](https://github.com/homeport/termshot) - Terminal screenshot tool
- Rich's built-in export: Add this to the code temporarily:
  ```python
  console.save_svg("output.svg", title="Mac Configurator")
  ```

## 4. Once Screenshots Are Added

The README already references them - just make sure the files exist in:
- `screenshots/main-menu.png`
- `screenshots/category-selection.png`
- `screenshots/settings-view.png`
- `screenshots/apply-settings.png`
