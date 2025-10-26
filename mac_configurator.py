#!/usr/bin/env python3
"""
Mac System Configurator
Interactive utility to manage and apply Mac system settings
"""

import json
import subprocess
import os
import grp
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.progress import track
from rich import box
from rich.text import Text

try:
    import jsonschema
except ImportError:
    print("Error: jsonschema package not found. Install with: pip install jsonschema")
    exit(1)


def is_admin():
    """Check if current user has admin privileges"""
    try:
        # Check if user is in admin group (GID 80 on macOS)
        return 'admin' in [grp.getgrgid(g).gr_name for g in os.getgroups()]
    except:
        return False


class UserConfigPathManager:
    """Manages user configuration path preferences"""

    def __init__(self, config_file='.userConfig'):
        self.config_file = Path(config_file)
        self.config_dir = self._load_or_create_config_path()

    def _get_default_config_dir(self):
        """Get the default configuration directory"""
        user_home = Path.home()
        return user_home / 'MacConfigurator'

    def _load_or_create_config_path(self):
        """Load config path from .userConfig or create with default"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    config_path = Path(config_data.get('config_directory', self._get_default_config_dir()))
            except (json.JSONDecodeError, KeyError):
                # If file is corrupted, use default
                config_path = self._get_default_config_dir()
        else:
            # Create .userConfig with default path
            config_path = self._get_default_config_dir()
            self._save_config_path(config_path)

        # Ensure the directory exists
        config_path.mkdir(parents=True, exist_ok=True)
        return config_path

    def _save_config_path(self, path):
        """Save config path to .userConfig"""
        with open(self.config_file, 'w') as f:
            json.dump({'config_directory': str(path)}, f, indent=2)

    def get_config_dir(self):
        """Get the current configuration directory"""
        return self.config_dir

    def set_config_dir(self, path):
        """Set a new configuration directory"""
        new_path = Path(path)
        new_path.mkdir(parents=True, exist_ok=True)
        self.config_dir = new_path
        self._save_config_path(new_path)

    def list_config_files(self):
        """List all config files in the config directory"""
        config_files = list(self.config_dir.glob('*_config.json'))
        # Extract config names from filenames
        configs = []
        for config_file in config_files:
            # Remove '_config.json' suffix to get config name
            name = config_file.stem.replace('_config', '')
            configs.append({'name': name, 'path': config_file})
        return sorted(configs, key=lambda x: x['name'])

    def get_config_path(self, config_name):
        """Get the full path for a config file by name"""
        return self.config_dir / f"{config_name}_config.json"

    def config_exists(self, config_name):
        """Check if a config file exists"""
        return self.get_config_path(config_name).exists()

    def validate_config_name(self, config_name):
        """Validate config name contains only safe filename characters"""
        import re
        # Allow alphanumeric, spaces, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9 _-]+$', config_name):
            return False, "Config name can only contain letters, numbers, spaces, hyphens, and underscores"
        if not config_name.strip():
            return False, "Config name cannot be empty"
        return True, ""

    def delete_config(self, config_name):
        """Delete a config file"""
        config_path = self.get_config_path(config_name)
        if config_path.exists():
            config_path.unlink()
            return True
        return False


class ConfigManager:
    """Manages configuration file operations with schema validation"""

    def __init__(self, config_path, schema_path=None):
        self.config_path = Path(config_path)
        # If no schema path provided, look for it next to the script
        if schema_path is None:
            script_dir = Path(__file__).parent
            self.schema_path = script_dir / 'settings_schema.json'
        else:
            self.schema_path = Path(schema_path)
        # Extract config name from path (remove '_config.json' suffix)
        self.config_name = self.config_path.stem.replace('_config', '')
        self.schema = self.load_schema()
        self.config = self.load_config()

    def load_schema(self):
        """Load settings schema from JSON file"""
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")

        with open(self.schema_path, 'r') as f:
            return json.load(f)

    def load_config(self):
        """Load configuration from JSON file and validate against schema"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = json.load(f)

            # Validate configuration against schema
            try:
                jsonschema.validate(instance=config, schema=self.schema)
            except jsonschema.ValidationError as e:
                print(f"Warning: Configuration validation error: {e.message}")
                print(f"Path: {' -> '.join(str(p) for p in e.path)}")
                print("Continuing with invalid configuration...")

            return config
        return {"settings": {}}

    def save_config(self):
        """Save configuration to JSON file after validation"""
        # Validate before saving
        try:
            jsonschema.validate(instance=self.config, schema=self.schema)
        except jsonschema.ValidationError as e:
            raise ValueError(f"Configuration validation failed: {e.message}")

        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)

    def get_setting(self, key):
        """Get a specific setting value (returns None if not explicitly configured)"""
        return self.config.get('settings', {}).get(key)

    def has_setting(self, key):
        """Check if a setting has been explicitly configured"""
        return key in self.config.get('settings', {})

    def set_setting(self, key, value):
        """Set a specific setting value with validation"""
        # Check if setting exists in schema
        if key not in self.schema.get('properties', {}).get('settings', {}).get('properties', {}):
            raise ValueError(f"Unknown setting: {key}")

        # Validate the value against the schema for this specific setting
        setting_schema = self.schema['properties']['settings']['properties'][key]
        try:
            jsonschema.validate(instance=value, schema=setting_schema)
        except jsonschema.ValidationError as e:
            raise ValueError(f"Invalid value for {key}: {e.message}")

        if 'settings' not in self.config:
            self.config['settings'] = {}
        self.config['settings'][key] = value
        self.save_config()

    def delete_setting(self, key):
        """Delete a configured setting (unset it)"""
        if 'settings' in self.config and key in self.config['settings']:
            del self.config['settings'][key]
            self.save_config()
            return True
        return False

    def get_all_configured_settings(self):
        """Get all explicitly configured settings"""
        return self.config.get('settings', {})

    def get_schema_for_setting(self, key):
        """Get the schema definition for a specific setting"""
        return self.schema.get('properties', {}).get('settings', {}).get('properties', {}).get(key)


class WiFiHandler:
    """Handles WiFi-related operations"""

    @staticmethod
    def _get_wifi_interface():
        """Detect the WiFi interface name"""
        try:
            # Try to list all network services and find WiFi
            result = subprocess.run(
                ['networksetup', '-listallhardwareports'],
                capture_output=True,
                text=True,
                check=True
            )

            # Parse output to find WiFi device
            lines = result.stdout.split('\n')
            for i, line in enumerate(lines):
                if 'Wi-Fi' in line or 'AirPort' in line:
                    # Next line after "Hardware Port: Wi-Fi" is "Device: enX"
                    if i + 1 < len(lines) and 'Device:' in lines[i + 1]:
                        device = lines[i + 1].split('Device:')[1].strip()
                        return device

            # Fallback to en0 if not found
            return 'en0'
        except subprocess.CalledProcessError:
            return 'en0'

    @staticmethod
    def get_current_state():
        """Get current WiFi state (enabled/disabled)"""
        try:
            interface = WiFiHandler._get_wifi_interface()
            result = subprocess.run(
                ['networksetup', '-getairportpower', interface],
                capture_output=True,
                text=True,
                check=True
            )
            # Output format: "Wi-Fi Power (en0): On" or "Wi-Fi Power (en0): Off"
            return 'On' in result.stdout
        except subprocess.CalledProcessError:
            # Silently fail - the UI will show N/A
            return None

    @staticmethod
    def set_state(enabled):
        """Set WiFi state (True=on, False=off)"""
        try:
            interface = WiFiHandler._get_wifi_interface()
            state = 'on' if enabled else 'off'
            subprocess.run(
                ['networksetup', '-setairportpower', interface, state],
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False


class AudioInputHandler:
    """Handles audio input (microphone) operations"""

    @staticmethod
    def get_mute_state():
        """Get current input mute state (True=muted, False=unmuted)"""
        try:
            result = subprocess.run(
                ['osascript', '-e', 'input volume of (get volume settings)'],
                capture_output=True,
                text=True,
                check=True
            )
            # Returns "0" if muted, otherwise a value > 0
            volume = int(result.stdout.strip())
            return volume == 0
        except (subprocess.CalledProcessError, ValueError):
            print("Error: Could not get audio input mute state")
            return None

    @staticmethod
    def set_mute_state(muted):
        """Set audio input mute state (True=mute, False=unmute)"""
        try:
            volume = '0' if muted else '50'  # Use 50 as default unmuted volume
            subprocess.run(
                ['osascript', '-e', f'set volume input volume {volume}'],
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            print(f"Error: Could not set audio input mute to {muted}")
            return False


class AudioOutputHandler:
    """Handles audio output (speaker) operations"""

    @staticmethod
    def get_volume():
        """Get current output volume (0-100)"""
        try:
            result = subprocess.run(
                ['osascript', '-e', 'output volume of (get volume settings)'],
                capture_output=True,
                text=True,
                check=True
            )
            return int(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError):
            print("Error: Could not get audio output volume")
            return None

    @staticmethod
    def set_volume(volume):
        """Set audio output volume (0-100)"""
        try:
            volume = max(0, min(100, volume))  # Clamp to 0-100
            subprocess.run(
                ['osascript', '-e', f'set volume output volume {volume}'],
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            print(f"Error: Could not set audio output volume to {volume}")
            return False


class DockHandler:
    """Handles Dock-related operations"""

    @staticmethod
    def get_autohide():
        """Get Dock autohide state"""
        try:
            result = subprocess.run(
                ['defaults', 'read', 'com.apple.dock', 'autohide'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip() == '1'
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def set_autohide(enabled):
        """Set Dock autohide state"""
        try:
            value = '1' if enabled else '0'
            subprocess.run(
                ['defaults', 'write', 'com.apple.dock', 'autohide', '-bool', str(enabled).lower()],
                check=True
            )
            subprocess.run(['killall', 'Dock'], check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def get_position():
        """Get Dock position (left/bottom/right)"""
        try:
            result = subprocess.run(
                ['defaults', 'read', 'com.apple.dock', 'orientation'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return 'bottom'

    @staticmethod
    def set_position(position):
        """Set Dock position"""
        try:
            if position not in ['left', 'bottom', 'right']:
                return False
            subprocess.run(
                ['defaults', 'write', 'com.apple.dock', 'orientation', position],
                check=True
            )
            subprocess.run(['killall', 'Dock'], check=True)
            return True
        except subprocess.CalledProcessError:
            return False


class FinderHandler:
    """Handles Finder-related operations"""

    @staticmethod
    def get_show_hidden_files():
        """Get show hidden files state"""
        try:
            result = subprocess.run(
                ['defaults', 'read', 'com.apple.finder', 'AppleShowAllFiles'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip().upper() == 'TRUE'
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def set_show_hidden_files(enabled):
        """Set show hidden files state"""
        try:
            subprocess.run(
                ['defaults', 'write', 'com.apple.finder', 'AppleShowAllFiles', '-bool', str(enabled).lower()],
                check=True
            )
            subprocess.run(['killall', 'Finder'], check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def get_show_extensions():
        """Get show all file extensions state"""
        try:
            result = subprocess.run(
                ['defaults', 'read', 'NSGlobalDomain', 'AppleShowAllExtensions'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip() == '1'
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def set_show_extensions(enabled):
        """Set show all file extensions state"""
        try:
            subprocess.run(
                ['defaults', 'write', 'NSGlobalDomain', 'AppleShowAllExtensions', '-bool', str(enabled).lower()],
                check=True
            )
            subprocess.run(['killall', 'Finder'], check=True)
            return True
        except subprocess.CalledProcessError:
            return False


class SystemHandler:
    """Handles system-level operations"""

    @staticmethod
    def get_screenshot_location():
        """Get screenshot save location"""
        try:
            result = subprocess.run(
                ['defaults', 'read', 'com.apple.screencapture', 'location'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            # Default location
            return str(Path.home() / 'Desktop')

    @staticmethod
    def set_screenshot_location(path):
        """Set screenshot save location"""
        try:
            # Ensure path exists
            Path(path).mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ['defaults', 'write', 'com.apple.screencapture', 'location', path],
                check=True
            )
            subprocess.run(['killall', 'SystemUIServer'], check=True)
            return True
        except (subprocess.CalledProcessError, OSError):
            return False


class StartupItemsHandler:
    """Handles login items / startup applications"""

    @staticmethod
    def get_login_items():
        """Get list of all login items with their details"""
        try:
            result = subprocess.run(
                ['osascript', '-e', 'tell application "System Events" to get the name of every login item'],
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout.strip():
                items = [item.strip() for item in result.stdout.strip().split(',')]
                return items
            return []
        except subprocess.CalledProcessError:
            return []

    @staticmethod
    def get_blocked_items():
        """This is a placeholder - the actual blocked list comes from config"""
        return []

    @staticmethod
    def set_blocked_items(blocked_list):
        """Apply the blocked items list by removing them from login items"""
        if not blocked_list:
            return True

        success = True
        current_items = StartupItemsHandler.get_login_items()

        for item_name in blocked_list:
            if item_name in current_items:
                try:
                    # Remove the login item
                    subprocess.run(
                        ['osascript', '-e', f'tell application "System Events" to delete login item "{item_name}"'],
                        check=True,
                        capture_output=True
                    )
                except subprocess.CalledProcessError:
                    success = False

        return success

    @staticmethod
    def remove_login_item(item_name):
        """Remove a specific login item"""
        try:
            subprocess.run(
                ['osascript', '-e', f'tell application "System Events" to delete login item "{item_name}"'],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError:
            return False


class BackgroundAppsHandler:
    """Handles background app permissions"""

    @staticmethod
    def get_background_items():
        """Get list of background items from sfltool"""
        try:
            result = subprocess.run(
                ['sfltool', 'dumpbtm'],
                capture_output=True,
                text=True,
                check=True
            )

            # Parse the output to extract app names and their status
            items = {}
            lines = result.stdout.split('\n')
            current_name = None
            current_disposition = None

            for line in lines:
                line = line.strip()
                if line.startswith('Name:'):
                    current_name = line.split(':', 1)[1].strip()
                elif line.startswith('Disposition:'):
                    current_disposition = line
                    if current_name and current_disposition:
                        # Parse disposition to check if enabled
                        enabled = 'enabled' in current_disposition.lower()
                        items[current_name] = enabled
                        current_name = None
                        current_disposition = None

            return items
        except subprocess.CalledProcessError:
            return {}

    @staticmethod
    def get_background_permissions():
        """Get the current background permissions state as a dict"""
        return BackgroundAppsHandler.get_background_items()

    @staticmethod
    def set_background_permissions(permissions_dict):
        """Set background permissions - Note: This requires TCC database access"""
        # This is complex and requires database manipulation or private APIs
        # For now, we'll return True but note that full implementation would need
        # to use the TCC database or System Events automation
        # This is a placeholder for future enhancement
        return True


class SystemExtensionsHandler:
    """Handles system extensions and app extensions"""

    @staticmethod
    def _get_friendly_name(bundle_path, bundle_id):
        """Extract friendly name from extension bundle"""
        import plistlib
        import re

        # Try to read Info.plist from the bundle
        if bundle_path and bundle_path.endswith('.appex'):
            info_plist_path = Path(bundle_path) / 'Contents' / 'Info.plist'
            try:
                if info_plist_path.exists():
                    with open(info_plist_path, 'rb') as f:
                        plist = plistlib.load(f)
                        # Try CFBundleDisplayName first, then CFBundleName
                        if 'CFBundleDisplayName' in plist:
                            return plist['CFBundleDisplayName']
                        elif 'CFBundleName' in plist:
                            name = plist['CFBundleName']
                            # Only return if it's not just the bundle ID
                            if name != bundle_id and '.' not in name:
                                return name
            except:
                pass

        # Try to extract from the .appex filename
        if bundle_path:
            # Get the .appex filename without extension
            appex_name = Path(bundle_path).stem
            # Don't use if it's the same as bundle_id
            if appex_name != bundle_id:
                # Clean up common suffixes but preserve the rest
                cleaned = appex_name
                for suffix in ['Extension', 'Appex', 'Plugin', 'Service']:
                    if cleaned.endswith(suffix):
                        cleaned = cleaned[:-len(suffix)]

                # Only add spaces if the name has camelCase (not already spaced or all caps)
                if cleaned and not ' ' in cleaned and not cleaned.isupper():
                    # Add space before capitals, but not at the start
                    friendly = re.sub(r'(?<!^)([A-Z])', r' \1', cleaned).strip()
                    if friendly:
                        return friendly
                elif cleaned:
                    return cleaned

        # Fall back to parsing bundle ID
        # e.g., com.apple.Safari.CacheDelete -> Safari Cache Delete
        parts = bundle_id.split('.')
        if len(parts) >= 2:
            # Get the last part
            last_part = parts[-1]
            # Add spaces before capitals for camelCase
            if last_part and not last_part.isupper() and not ' ' in last_part:
                friendly = re.sub(r'(?<!^)([A-Z])', r' \1', last_part).strip()
                return friendly
            return last_part

        return bundle_id

    @staticmethod
    def get_system_extensions():
        """Get list of all extensions with their details (system + app extensions)"""
        extensions = []

        # Get driver-level system extensions from systemextensionsctl
        try:
            result = subprocess.run(
                ['systemextensionsctl', 'list'],
                capture_output=True,
                text=True,
                check=True
            )

            lines = result.stdout.split('\n')
            parsing = False
            for line in lines:
                if 'enabled' in line and 'active' in line and 'teamID' in line:
                    parsing = True
                    continue

                if parsing and line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 6:
                        enabled = parts[0].strip() == '*'
                        active = parts[1].strip() == '*'
                        team_id = parts[2].strip()
                        bundle_info = parts[3].strip()
                        name = parts[4].strip()
                        state = parts[5].strip()

                        bundle_id = bundle_info.split()[0] if bundle_info else ''
                        version = ''
                        if '(' in bundle_info and ')' in bundle_info:
                            version = bundle_info.split('(')[1].split(')')[0]

                        # For system extensions, name is usually already friendly
                        friendly_name = name if name != bundle_id else SystemExtensionsHandler._get_friendly_name('', bundle_id)

                        extensions.append({
                            'name': name,
                            'friendly_name': friendly_name,
                            'bundle_id': bundle_id,
                            'version': version,
                            'team_id': team_id,
                            'enabled': enabled,
                            'active': active,
                            'type': 'System Extension',
                            'state': state,
                            'user_visible': True  # System extensions always show in System Settings
                        })
        except subprocess.CalledProcessError:
            pass

        # Get app extensions from pluginkit
        try:
            result = subprocess.run(
                ['pluginkit', '-m', '-v'],
                capture_output=True,
                text=True,
                check=True
            )

            lines = result.stdout.split('\n')
            for line in lines:
                if not line.strip():
                    continue

                # Format: [+]    bundle.id(version)	UUID	timestamp	path
                enabled = line.startswith('+')
                line_content = line.lstrip('+ \t')

                # Split by tabs
                parts = line_content.split('\t')
                if len(parts) >= 4:
                    bundle_info = parts[0].strip()
                    path = parts[3].strip() if len(parts) > 3 else ''

                    # Extract bundle ID and version
                    if '(' in bundle_info and ')' in bundle_info:
                        bundle_id = bundle_info.split('(')[0]
                        version = bundle_info.split('(')[1].split(')')[0]
                    else:
                        bundle_id = bundle_info
                        version = ''

                    # Extract human-readable name from bundle ID
                    name_parts = bundle_id.split('.')
                    name = name_parts[-1] if name_parts else bundle_id

                    # Get friendly name from bundle
                    friendly_name = SystemExtensionsHandler._get_friendly_name(path, bundle_id)

                    # Determine extension type from bundle ID or path
                    ext_type = 'App Extension'
                    user_visible = False  # Whether it shows in System Settings

                    if 'safari' in bundle_id.lower():
                        ext_type = 'Safari Extension'
                        user_visible = True
                    elif 'share' in bundle_id.lower() or 'ShareExtension' in path:
                        ext_type = 'Share Extension'
                        user_visible = True
                    elif 'finder' in bundle_id.lower() or 'FileProvider' in path:
                        ext_type = 'Finder Extension'
                        user_visible = True
                    elif 'widget' in bundle_id.lower() or 'Widget' in path:
                        ext_type = 'Widget'
                        user_visible = True
                    elif 'qlpreview' in bundle_id.lower() or 'QuickLook' in path or 'QLPreview' in path:
                        ext_type = 'Quick Look'
                        user_visible = True
                    elif 'spotlight' in bundle_id.lower() or 'SpotlightIndex' in path:
                        ext_type = 'Spotlight'
                        # Only some Spotlight extensions are user-visible
                        if not ('diagnostic' in bundle_id.lower() or 'system' in bundle_id.lower()):
                            user_visible = True
                    elif 'messages' in bundle_id.lower() or 'MessagesExtension' in path:
                        ext_type = 'Messages'
                        user_visible = True
                    elif 'photo' in bundle_id.lower() and 'edit' in bundle_id.lower():
                        ext_type = 'Photos Editing'
                        user_visible = True

                    # System/framework extensions are not user-visible
                    if any(x in bundle_id.lower() for x in ['diagnostic', 'framework', 'system.', 'coreservices', 'privateframework']):
                        user_visible = False

                    extensions.append({
                        'name': name,
                        'friendly_name': friendly_name,
                        'bundle_id': bundle_id,
                        'version': version,
                        'team_id': '',
                        'enabled': enabled,
                        'active': enabled,  # For app extensions, enabled = active
                        'type': ext_type,
                        'state': 'enabled' if enabled else 'disabled',
                        'path': path,
                        'user_visible': user_visible
                    })
        except subprocess.CalledProcessError:
            pass

        return extensions

    @staticmethod
    def enable_extension(bundle_id):
        """Enable a specific extension using pluginkit"""
        try:
            subprocess.run(
                ['pluginkit', '-e', 'use', '-i', bundle_id],
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            # Some extensions cannot be controlled (system extensions, protected extensions)
            return False

    @staticmethod
    def disable_extension(bundle_id):
        """Disable a specific extension using pluginkit"""
        try:
            subprocess.run(
                ['pluginkit', '-e', 'ignore', '-i', bundle_id],
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            # Some extensions cannot be controlled (system extensions, protected extensions)
            return False

    @staticmethod
    def get_extension_preferences():
        """Get extension preferences - placeholder that returns empty dict"""
        # This is just a placeholder since actual preferences come from config
        return {}

    @staticmethod
    def set_extension_preferences(preferences_dict):
        """Apply extension preferences by enabling/disabling extensions"""
        if not preferences_dict:
            return True

        success_count = 0
        fail_count = 0

        for bundle_id, should_enable in preferences_dict.items():
            if should_enable:
                if SystemExtensionsHandler.enable_extension(bundle_id):
                    success_count += 1
                else:
                    fail_count += 1
            else:
                if SystemExtensionsHandler.disable_extension(bundle_id):
                    success_count += 1
                else:
                    fail_count += 1

        # Return True if at least some succeeded, or if none were attempted
        return success_count > 0 or fail_count == 0


class MacConfigurator:
    """Main application class"""

    def __init__(self, config_name, path_manager):
        self.console = Console()
        self.config_name = config_name
        self.path_manager = path_manager
        config_path = path_manager.get_config_path(config_name)
        self.config_manager = ConfigManager(config_path)
        self.is_admin = is_admin()

        # Handlers
        self.wifi_handler = WiFiHandler()
        self.audio_input_handler = AudioInputHandler()
        self.audio_output_handler = AudioOutputHandler()
        self.dock_handler = DockHandler()
        self.finder_handler = FinderHandler()
        self.system_handler = SystemHandler()
        self.startup_items_handler = StartupItemsHandler()
        self.background_apps_handler = BackgroundAppsHandler()
        self.system_extensions_handler = SystemExtensionsHandler()

        # Handler mapping for dynamic lookup
        self.handler_map = {
            'WiFiHandler': self.wifi_handler,
            'AudioInputHandler': self.audio_input_handler,
            'AudioOutputHandler': self.audio_output_handler,
            'DockHandler': self.dock_handler,
            'FinderHandler': self.finder_handler,
            'SystemHandler': self.system_handler,
            'StartupItemsHandler': self.startup_items_handler,
            'BackgroundAppsHandler': self.background_apps_handler,
            'SystemExtensionsHandler': self.system_extensions_handler
        }

        # Handler method mapping for each setting
        self.handler_methods = {
            'wifi_enabled': ('get_current_state', 'set_state'),
            'audio_input_muted': ('get_mute_state', 'set_mute_state'),
            'audio_output_volume': ('get_volume', 'set_volume'),
            'dock_autohide': ('get_autohide', 'set_autohide'),
            'dock_position': ('get_position', 'set_position'),
            'finder_show_hidden': ('get_show_hidden_files', 'set_show_hidden_files'),
            'finder_show_extensions': ('get_show_extensions', 'set_show_extensions'),
            'screenshot_location': ('get_screenshot_location', 'set_screenshot_location'),
            'startup_items_blocked': ('get_blocked_items', 'set_blocked_items'),
            'background_app_permissions': ('get_background_permissions', 'set_background_permissions'),
            'system_extension_preferences': ('get_extension_preferences', 'set_extension_preferences')
        }

        # Build settings structure from schema
        self.categories = self._build_categories_from_schema()

    def _build_categories_from_schema(self):
        """Build categories structure from JSON schema"""
        categories = {}
        schema_settings = self.config_manager.schema.get('properties', {}).get('settings', {}).get('properties', {})

        for setting_key, setting_schema in schema_settings.items():
            category = setting_schema.get('category', 'Other')

            # Initialize category if not exists
            if category not in categories:
                categories[category] = {}

            # Get handler and methods
            handler_name = setting_schema.get('handler')
            handler = self.handler_map.get(handler_name)
            get_method, set_method = self.handler_methods.get(setting_key, (None, None))

            if not handler or not get_method or not set_method:
                print(f"Warning: Handler not found for setting: {setting_key}")
                continue

            # Map schema type to internal type
            schema_type = setting_schema.get('type')
            internal_type = schema_type

            # Build setting info
            setting_info = {
                'name': setting_schema.get('title', setting_key),
                'type': internal_type,
                'get_current': getattr(handler, get_method),
                'set_value': getattr(handler, set_method),
                'requires_admin': setting_schema.get('requires_admin', False)
            }

            # Add type-specific properties
            if schema_type == 'integer':
                if 'minimum' in setting_schema:
                    setting_info['min'] = setting_schema['minimum']
                if 'maximum' in setting_schema:
                    setting_info['max'] = setting_schema['maximum']
            elif 'enum' in setting_schema:
                # Choice/enum type
                setting_info['type'] = 'choice'
                setting_info['choices'] = setting_schema['enum']

            categories[category][setting_key] = setting_info

        return categories

    def manage_settings(self):
        """Interactive settings manager with category navigation"""
        # Category icons and colors
        category_styles = {
            'Network': ('🌐', 'blue'),
            'Audio': ('🔊', 'magenta'),
            'Dock': ('📱', 'cyan'),
            'Finder': ('📁', 'green'),
            'System': ('⚙️ ', 'yellow'),  # Extra space for alignment
            'Startup': ('🚀', 'bright_cyan'),
            'Background Apps': ('⏱️ ', 'bright_magenta'),  # Extra space for alignment
            'System Extensions': ('🔌', 'bright_yellow')
        }

        while True:
            self.console.clear()

            # Create categories table
            table = Table(title="[bold cyan]Manage Settings - Select Category[/bold cyan]", box=box.ROUNDED, show_header=False)
            table.add_column("Option", style="bright_cyan", width=8)
            table.add_column("Category", style="bright_white", width=30)

            category_list = list(self.categories.keys())
            for idx, category in enumerate(category_list, 1):
                icon, color = category_styles.get(category, ('•', 'white'))
                table.add_row(f"[{idx}]", f"{icon}  [{color}]{category}[/{color}]")

            self.console.print(table)
            self.console.print("\n[dim italic]Press Enter to return to main menu[/dim italic]")

            choice = Prompt.ask(
                f"\nSelect category",
                choices=[str(i) for i in range(1, len(category_list) + 1)],
                default="",
                show_choices=False
            )

            if not choice:
                break

            try:
                category_idx = int(choice) - 1
                category_name = category_list[category_idx]

                # Route to custom UI for special categories
                if category_name == 'Startup':
                    self._manage_startup_items()
                elif category_name == 'Background Apps':
                    self._manage_background_apps()
                elif category_name == 'System Extensions':
                    self._manage_system_extensions()
                else:
                    self._manage_category_settings(category_name)

            except (ValueError, IndexError):
                self.console.print("[red]Invalid selection[/red]")
                self.console.input("\nPress Enter to continue...")

    def _manage_category_settings(self, category_name):
        """Manage settings within a specific category"""
        while True:
            self.console.clear()

            settings = self.categories[category_name]
            setting_keys = list(settings.keys())

            # Show admin status if not admin
            if not self.is_admin:
                self.console.print(Panel(
                    "[bold yellow]⚠  Admin Privileges Required[/bold yellow]\n\n"
                    "You are not running as administrator. Settings marked with [red bold]🔒[/red bold] will not be applied.\n"
                    "[dim]To apply these settings, run the script with sudo or as an admin user.[/dim]",
                    border_style="yellow",
                    box=box.HEAVY
                ))
                self.console.print()

            # Create settings table with color-coded headers
            table = Table(title=f"[bold bright_white]{category_name} Settings[/bold bright_white]", box=box.ROUNDED)
            table.add_column("Option", style="bright_cyan bold", width=8)
            table.add_column("Setting", style="bright_white", width=25)
            table.add_column("Your Config", style="bright_yellow", width=15, header_style="bright_yellow bold")
            table.add_column("Live System", style="bright_magenta", width=15, header_style="bright_magenta bold")
            table.add_column("Status", justify="center", width=8, header_style="bright_white bold")

            for idx, setting_key in enumerate(setting_keys, 1):
                setting_info = settings[setting_key]
                configured_value = self.config_manager.get_setting(setting_key)
                is_configured = self.config_manager.has_setting(setting_key)
                current_value = setting_info['get_current']()

                # Handle None values from handler methods
                current_display = current_value if current_value is not None else "[dim italic]N/A[/dim italic]"

                # Color-coded status with different symbols
                if not is_configured:
                    # Not configured - show as inactive
                    status = "[dim]○[/dim]"
                    configured_str = "[dim italic]Not set[/dim italic]"
                    current_str = f"[dim]{current_display}[/dim]" if current_value is not None else current_display
                elif configured_value == current_value:
                    # Matches system
                    status = "[bold green]✓[/bold green]"
                    configured_str = f"[dim]{configured_value}[/dim]"
                    current_str = f"[dim]{current_display}[/dim]" if current_value is not None else current_display
                else:
                    # Differs from system
                    status = "[bold yellow]⚠[/bold yellow]"
                    configured_str = f"[bold bright_yellow]{configured_value}[/bold bright_yellow]"
                    current_str = f"[bold bright_magenta]{current_display}[/bold bright_magenta]" if current_value is not None else current_display

                # Add lock icon if requires admin and user is not admin
                setting_name = setting_info['name']
                if setting_info.get('requires_admin', False) and not self.is_admin:
                    setting_name = f"{setting_name} [red bold]🔒[/red bold]"

                table.add_row(
                    f"[{idx}]",
                    setting_name,
                    configured_str,
                    current_str,
                    status
                )

            self.console.print(table)
            self.console.print("\n[dim italic]Press Enter to return to category menu[/dim italic]")

            choice = Prompt.ask(
                "\nSelect setting to edit",
                choices=[str(i) for i in range(1, len(setting_keys) + 1)],
                default="",
                show_choices=False
            )

            if not choice:
                break

            try:
                setting_idx = int(choice) - 1
                setting_key = setting_keys[setting_idx]
                self._edit_setting(setting_key, settings[setting_key])
            except (ValueError, IndexError):
                self.console.print("[red]Invalid selection[/red]")
                self.console.input("\nPress Enter to continue...")

    def _edit_setting(self, setting_key, setting_info):
        """Edit a specific setting"""
        current_value = self.config_manager.get_setting(setting_key)
        is_configured = self.config_manager.has_setting(setting_key)
        system_value = setting_info['get_current']()
        requires_admin = setting_info.get('requires_admin', False)

        # Display setting header with color-coded info
        self.console.print()
        self.console.print(Panel(
            f"[bold bright_white]{setting_info['name']}[/bold bright_white]",
            border_style="cyan",
            box=box.ROUNDED
        ))

        if requires_admin and not self.is_admin:
            self.console.print("[red bold]🔒 Requires admin privileges[/red bold]")

        # Show comparison in a mini table with clear labels
        comparison_table = Table(show_header=True, box=box.SIMPLE, padding=(0, 1))
        comparison_table.add_column("Source", style="dim", width=20)
        comparison_table.add_column("Value", style="bold", width=30)

        configured_display = f"[bright_yellow]{current_value}[/bright_yellow]" if is_configured else "[dim italic]Not configured[/dim italic]"
        system_display = f"[bright_magenta]{system_value}[/bright_magenta]" if system_value is not None else "[dim italic]N/A[/dim italic]"

        comparison_table.add_row("Your Config", configured_display)
        comparison_table.add_row("Current System Value", system_display)

        self.console.print(comparison_table)

        # Add helpful note if not configured
        if not is_configured:
            self.console.print("[dim italic]Note: This setting is not configured. The system is currently using its own value.[/dim italic]")
        elif system_value is not None and current_value != system_value:
            self.console.print(f"[yellow]⚠ Your configured value differs from the current system value.[/yellow]")

        # If configured value differs from system, offer to apply immediately
        if is_configured and system_value is not None and current_value != system_value:
            self.console.print()
            if requires_admin and not self.is_admin:
                self.console.print("[yellow]⚠ This setting requires admin privileges and cannot be applied.[/yellow]")
            else:
                if Confirm.ask("[cyan]Apply this setting now?[/cyan]", default=False):
                    self.console.print(f"Applying [bold]{setting_info['name']}[/bold]...", end=" ")
                    if setting_info['set_value'](current_value):
                        self.console.print("[green]✓ Success[/green]")

                        # Show refreshed status
                        self.console.print()
                        self.console.print("[bold cyan]━━━ Current Status ━━━[/bold cyan]")

                        # Re-read system value
                        updated_system = setting_info['get_current']()

                        status_table = Table(show_header=True, box=box.SIMPLE, padding=(0, 1))
                        status_table.add_column("Source", style="dim", width=20)
                        status_table.add_column("Value", style="bold", width=30)

                        config_display = f"[bright_yellow]{current_value}[/bright_yellow]"
                        system_display = f"[bright_magenta]{updated_system}[/bright_magenta]" if updated_system is not None else "[dim italic]N/A[/dim italic]"

                        status_table.add_row("Your Config", config_display)
                        status_table.add_row("Current System Value", system_display)

                        self.console.print(status_table)

                        if current_value == updated_system:
                            self.console.print("[bold green]✓ Config and system are now in sync![/bold green]")
                        else:
                            self.console.print("[yellow]⚠ Applied but values still differ - the setting may take time to update[/yellow]")

                        self.console.input("\nPress Enter to continue...")
                        return
                    else:
                        self.console.print("[red]✗ Failed[/red]")

        # Option to delete/unset if currently configured
        if is_configured:
            self.console.print()
            if Confirm.ask("[red]Delete this configured setting (unset)?[/red]", default=False):
                if self.config_manager.delete_setting(setting_key):
                    self.console.print("\n[bold green]✓ Setting deleted[/bold green] - no longer configured")
                    self.console.input("\nPress Enter to continue...")
                    return
                else:
                    self.console.print("\n[bold red]✗ Failed to delete setting[/bold red]")
                    self.console.input("\nPress Enter to continue...")
                    return

        new_value = None
        value_changed = False

        if setting_info['type'] == 'boolean':
            # Use configured value if available, otherwise use system value, otherwise True
            default_value = current_value if isinstance(current_value, bool) else (system_value if isinstance(system_value, bool) else True)
            result = Confirm.ask(
                f"\n[cyan]Set {setting_info['name']} to[/cyan]",
                default=default_value
            )
            if result != current_value:
                self.config_manager.set_setting(setting_key, result)
                self.console.print(f"\n[bold green]✓ Saved[/bold green] → [bright_yellow]{result}[/bright_yellow]")
                new_value = result
                value_changed = True
            else:
                self.console.print(f"\n[dim italic]→ Value unchanged[/dim italic]")

        elif setting_info['type'] == 'integer':
            min_val = setting_info.get('min', 0)
            max_val = setting_info.get('max', 100)

            # Use configured value if available, otherwise use system value, otherwise min
            default_value = current_value if isinstance(current_value, int) else (system_value if isinstance(system_value, int) else min_val)

            try:
                value = IntPrompt.ask(
                    f"\n[cyan]Set value ({min_val}-{max_val})[/cyan]",
                    default=default_value
                )
                if min_val <= value <= max_val:
                    if value != current_value:
                        self.config_manager.set_setting(setting_key, value)
                        self.console.print(f"\n[bold green]✓ Saved[/bold green] → [bright_yellow]{value}[/bright_yellow]")
                        new_value = value
                        value_changed = True
                    else:
                        self.console.print(f"\n[dim italic]→ Value unchanged[/dim italic]")
                else:
                    self.console.print(f"\n[bold red]✗ Error:[/bold red] Value must be between {min_val} and {max_val}")
            except (ValueError, KeyboardInterrupt):
                self.console.print("\n[yellow]⚠ Cancelled[/yellow]")

        elif setting_info['type'] == 'choice':
            choices = setting_info.get('choices', [])
            # Use configured value if valid, otherwise use system value if valid, otherwise first choice
            if current_value in choices:
                default_value = current_value
            elif system_value in choices:
                default_value = system_value
            else:
                default_value = choices[0] if choices else None

            result = Prompt.ask(
                f"\n[cyan]Select {setting_info['name']}[/cyan]",
                choices=choices,
                default=default_value
            )
            if result != current_value:
                self.config_manager.set_setting(setting_key, result)
                self.console.print(f"\n[bold green]✓ Saved[/bold green] → [bright_yellow]{result}[/bright_yellow]")
                new_value = result
                value_changed = True
            else:
                self.console.print(f"\n[dim italic]→ Value unchanged[/dim italic]")

        elif setting_info['type'] == 'string':
            # Use configured value if available, otherwise use system value, otherwise empty string
            if current_value:
                default_value = str(current_value)
            elif system_value:
                default_value = str(system_value)
            else:
                default_value = ""

            result = Prompt.ask(
                f"\n[cyan]Enter {setting_info['name']}[/cyan]",
                default=default_value
            )
            if result != current_value:
                self.config_manager.set_setting(setting_key, result)
                self.console.print(f"\n[bold green]✓ Saved[/bold green] → [bright_yellow]{result}[/bright_yellow]")
                new_value = result
                value_changed = True
            else:
                self.console.print(f"\n[dim italic]→ Value unchanged[/dim italic]")

        # Check if we should apply the setting now
        applied = False
        if value_changed:
            new_system_value = setting_info['get_current']()
            if new_value != new_system_value:
                # Check if user has admin rights if required
                if requires_admin and not self.is_admin:
                    self.console.print()
                    self.console.print("[yellow]⚠ This setting requires admin privileges and will not be applied until you run as admin.[/yellow]")
                else:
                    self.console.print()
                    if Confirm.ask(f"[cyan]Apply this setting to system now? (y/n, press Enter to skip)[/cyan]", default=False):
                        self.console.print(f"Applying [bold]{setting_info['name']}[/bold]...", end=" ")
                        if setting_info['set_value'](new_value):
                            self.console.print("[green]✓ Success[/green]")
                            applied = True
                        else:
                            self.console.print("[red]✗ Failed[/red]")
                    else:
                        self.console.print("[dim]Skipped - use 'Apply Settings Now' from main menu to apply later[/dim]")

        # Show refreshed status after save/apply
        if value_changed or applied:
            self.console.print()
            self.console.print("[bold cyan]━━━ Current Status ━━━[/bold cyan]")

            # Re-read values from system
            updated_config = self.config_manager.get_setting(setting_key)
            updated_system = setting_info['get_current']()

            status_table = Table(show_header=True, box=box.SIMPLE, padding=(0, 1))
            status_table.add_column("Source", style="dim", width=20)
            status_table.add_column("Value", style="bold", width=30)

            config_display = f"[bright_yellow]{updated_config}[/bright_yellow]" if updated_config is not None else "[dim italic]Not configured[/dim italic]"
            system_display = f"[bright_magenta]{updated_system}[/bright_magenta]" if updated_system is not None else "[dim italic]N/A[/dim italic]"

            status_table.add_row("Your Config", config_display)
            status_table.add_row("Current System Value", system_display)

            self.console.print(status_table)

            if updated_config == updated_system:
                self.console.print("[bold green]✓ Config and system are now in sync![/bold green]")
            elif applied:
                self.console.print("[yellow]⚠ Applied but values still differ - the setting may take time to update[/yellow]")

        self.console.input("\nPress Enter to continue...")

    def apply_settings(self):
        """Apply configured settings to the system"""
        self.console.clear()
        self.console.print(Panel.fit(f"[bold cyan]Applying Settings - {self.config_name}[/bold cyan]", box=box.DOUBLE))

        # Collect settings that need to be applied
        # Only apply settings that are explicitly configured (not None)
        to_apply = []
        skipped_admin = []
        for category_name, settings in self.categories.items():
            for setting_key, setting_info in settings.items():
                configured_value = self.config_manager.get_setting(setting_key)

                # Skip if not configured
                if configured_value is None:
                    continue

                # Special handling for array/object types (startup items, background apps, system extensions)
                if setting_key == 'startup_items_blocked':
                    # Always apply if there are blocked items
                    if configured_value:
                        to_apply.append((setting_key, setting_info, configured_value))
                    continue
                elif setting_key == 'background_app_permissions':
                    # Always apply if there are configured permissions
                    if configured_value:
                        to_apply.append((setting_key, setting_info, configured_value))
                    continue
                elif setting_key == 'system_extension_preferences':
                    # Always apply if there are configured preferences
                    if configured_value:
                        to_apply.append((setting_key, setting_info, configured_value))
                    continue

                # For regular settings, check if different from current
                current_value = setting_info['get_current']()
                if configured_value != current_value:
                    # Check if requires admin
                    if setting_info.get('requires_admin', False) and not self.is_admin:
                        skipped_admin.append((setting_key, setting_info, configured_value))
                    else:
                        to_apply.append((setting_key, setting_info, configured_value))

        # Show skipped admin settings warning
        if skipped_admin:
            self.console.print()
            self.console.print(Panel(
                f"[bold yellow]⚠  Skipped - Admin Required[/bold yellow]\n\n" +
                f"The following {len(skipped_admin)} setting(s) require admin privileges:\n\n" +
                "\n".join([f"  [red]🔒[/red] {info['name']}" for _, info, _ in skipped_admin]) +
                "\n\n[dim]Run with sudo or as admin to apply these settings.[/dim]",
                border_style="yellow",
                box=box.HEAVY
            ))

        if not to_apply and not skipped_admin:
            self.console.print()
            self.console.print(Panel(
                "[bold green]✓  All Settings Match[/bold green]\n\nNo changes needed - all settings already match configured state!",
                border_style="green",
                box=box.ROUNDED
            ))
        elif not to_apply:
            self.console.print()
            self.console.print("[yellow italic]No settings to apply (all require admin or match current state)[/yellow italic]")
        else:
            self.console.print(f"\n[bold bright_cyan]→ Applying {len(to_apply)} setting(s)...[/bold bright_cyan]\n")

            # Apply settings with progress tracking
            success_count = 0
            fail_count = 0

            for setting_key, setting_info, configured_value in to_apply:
                # Format the value display based on type
                if isinstance(configured_value, list):
                    value_display = f"{len(configured_value)} item(s)"
                elif isinstance(configured_value, dict):
                    value_display = f"{len(configured_value)} permission(s)"
                else:
                    value_display = str(configured_value)

                self.console.print(f"  [dim]•[/dim] [bold bright_white]{setting_info['name']}[/bold bright_white] → [bright_yellow]{value_display}[/bright_yellow] ", end="")

                if setting_info['set_value'](configured_value):
                    self.console.print("[bold green]✓[/bold green]")
                    success_count += 1
                else:
                    self.console.print("[bold red]✗[/bold red]")
                    fail_count += 1

            # Summary
            self.console.print()
            if fail_count == 0:
                self.console.print(Panel(
                    f"[bold green]✓  Successfully Applied All Settings[/bold green]\n\n{success_count} setting(s) updated",
                    border_style="green",
                    box=box.ROUNDED
                ))
            else:
                self.console.print(Panel(
                    f"[bold yellow]⚠  Partial Success[/bold yellow]\n\n"
                    f"[green]✓ Success:[/green] {success_count} setting(s)\n"
                    f"[red]✗ Failed:[/red] {fail_count} setting(s)",
                    border_style="yellow",
                    box=box.ROUNDED
                ))

        self.console.print()
        self.console.input("Press Enter to continue...")

    def generate_applescript(self):
        """Generate an AppleScript that can be run at startup or ad-hoc"""
        self.console.clear()

        script_content = f'''#!/usr/bin/osascript
# Mac System Configurator - Auto-apply Script
# This script applies configured system settings for: {self.config_name}

do shell script "python3 {str(Path.cwd() / 'mac_configurator.py')} --apply '{self.config_name}'" with administrator privileges
'''

        script_path = self.path_manager.get_config_dir() / f'apply_{self.config_name}_settings.scpt'
        with open(script_path, 'w') as f:
            f.write(script_content)

        # Make it executable
        os.chmod(script_path, 0o755)

        self.console.print(Panel.fit("[bold green]AppleScript Generated[/bold green]", box=box.DOUBLE))
        self.console.print(f"\n[green]✓[/green] Script saved to: [cyan]{script_path}[/cyan]")
        self.console.print("\n[bold]To run manually:[/bold]")
        self.console.print(f"  [dim]osascript {script_path}[/dim]")
        self.console.print("\n[bold]To add to startup:[/bold]")
        self.console.print("  1. Open [cyan]System Settings > General > Login Items[/cyan]")
        self.console.print("  2. Click [cyan]'+'[/cyan] under [cyan]'Open at Login'[/cyan]")
        self.console.print(f"  3. Select: [cyan]{script_path}[/cyan]")

        self.console.print()
        self.console.input("Press Enter to continue...")

    def _manage_startup_items(self):
        """Manage startup items with custom UI"""
        while True:
            self.console.clear()

            # Get current login items and blocked list from config
            current_items = self.startup_items_handler.get_login_items()
            blocked_items = self.config_manager.get_setting('startup_items_blocked') or []

            # Create table showing all login items
            table = Table(title="[bold bright_white]Startup Items Management[/bold bright_white]", box=box.ROUNDED)
            table.add_column("Option", style="bright_cyan bold", width=8)
            table.add_column("Application Name", style="bright_white", width=35)
            table.add_column("Status", style="bright_yellow", width=15)
            table.add_column("Action", style="bright_magenta", width=15)

            for idx, item_name in enumerate(current_items, 1):
                is_blocked = item_name in blocked_items
                status = "[red]Blocked[/red]" if is_blocked else "[green]Allowed[/green]"
                action = "[dim]Remove block[/dim]" if is_blocked else "Block from startup"
                table.add_row(f"[{idx}]", item_name, status, action)

            self.console.print(table)

            if blocked_items:
                self.console.print(f"\n[dim]Currently blocking {len(blocked_items)} item(s) from startup[/dim]")

            self.console.print("\n[dim italic]Select an item to toggle its blocked status, or press Enter to return[/dim italic]")

            choice = Prompt.ask(
                "\nSelect item",
                choices=[str(i) for i in range(1, len(current_items) + 1)],
                default="",
                show_choices=False
            )

            if not choice:
                break

            try:
                item_idx = int(choice) - 1
                item_name = current_items[item_idx]

                if item_name in blocked_items:
                    # Remove from blocked list
                    blocked_items.remove(item_name)
                    self.config_manager.set_setting('startup_items_blocked', blocked_items)
                    self.console.print(f"\n[green]✓ Removed '{item_name}' from blocked list[/green]")
                else:
                    # Add to blocked list and remove from login items
                    blocked_items.append(item_name)
                    self.config_manager.set_setting('startup_items_blocked', blocked_items)

                    # Ask if user wants to remove it now
                    if Confirm.ask(f"\n[cyan]Remove '{item_name}' from startup now?[/cyan]", default=True):
                        if self.startup_items_handler.remove_login_item(item_name):
                            self.console.print(f"[green]✓ Removed '{item_name}' from startup[/green]")
                        else:
                            self.console.print(f"[red]✗ Failed to remove '{item_name}'[/red]")
                    else:
                        self.console.print("[dim]Will be removed next time settings are applied[/dim]")

                self.console.input("\nPress Enter to continue...")

            except (ValueError, IndexError):
                self.console.print("[red]Invalid selection[/red]")
                self.console.input("\nPress Enter to continue...")

    def _manage_background_apps(self):
        """Manage background app permissions with custom UI"""
        while True:
            self.console.clear()

            # Get current background items and configured permissions
            current_permissions = self.background_apps_handler.get_background_items()
            configured_permissions = self.config_manager.get_setting('background_app_permissions') or {}

            if not current_permissions:
                self.console.print(Panel(
                    "[yellow]No background items found.[/yellow]\n\n"
                    "Background app management requires macOS 13+ and may need additional permissions.",
                    border_style="yellow",
                    box=box.ROUNDED
                ))
                self.console.input("\nPress Enter to return...")
                break

            # Create table showing all background apps
            table = Table(title="[bold bright_white]Background App Permissions[/bold bright_white]", box=box.ROUNDED)
            table.add_column("Option", style="bright_cyan bold", width=8)
            table.add_column("Application Name", style="bright_white", width=35)
            table.add_column("System Status", style="bright_magenta", width=15)
            table.add_column("Your Config", style="bright_yellow", width=15)

            app_names = sorted(current_permissions.keys())
            for idx, app_name in enumerate(app_names, 1):
                system_enabled = current_permissions[app_name]
                system_status = "[green]Enabled[/green]" if system_enabled else "[red]Disabled[/red]"

                if app_name in configured_permissions:
                    config_enabled = configured_permissions[app_name]
                    config_status = "[green]Enabled[/green]" if config_enabled else "[red]Disabled[/red]"
                else:
                    config_status = "[dim italic]Not set[/dim italic]"

                table.add_row(f"[{idx}]", app_name, system_status, config_status)

            self.console.print(table)
            self.console.print("\n[yellow]Note:[/yellow] Changing background app permissions requires system-level access.")
            self.console.print("[dim]This feature stores your preferences but may not be able to apply them directly.[/dim]")
            self.console.print("\n[dim italic]Select an app to configure, or press Enter to return[/dim italic]")

            choice = Prompt.ask(
                "\nSelect app",
                choices=[str(i) for i in range(1, len(app_names) + 1)],
                default="",
                show_choices=False
            )

            if not choice:
                break

            try:
                app_idx = int(choice) - 1
                app_name = app_names[app_idx]
                current_setting = configured_permissions.get(app_name, current_permissions[app_name])

                self.console.print(f"\n[bold]Configuring: {app_name}[/bold]")
                new_value = Confirm.ask(
                    "[cyan]Allow to run in background?[/cyan]",
                    default=current_setting
                )

                # Update config
                if app_name not in configured_permissions:
                    configured_permissions = dict(configured_permissions)

                configured_permissions[app_name] = new_value
                self.config_manager.set_setting('background_app_permissions', configured_permissions)

                self.console.print(f"\n[green]✓ Saved preference for '{app_name}'[/green]")
                self.console.input("\nPress Enter to continue...")

            except (ValueError, IndexError):
                self.console.print("[red]Invalid selection[/red]")
                self.console.input("\nPress Enter to continue...")

    def _manage_system_extensions(self):
        """Manage system extensions with custom UI"""
        # Filter menu
        show_filter = 'all'  # all, enabled, disabled

        while True:
            self.console.clear()

            # Get current system extensions and configured preferences
            all_extensions = self.system_extensions_handler.get_system_extensions()
            configured_preferences = self.config_manager.get_setting('system_extension_preferences') or {}

            if not all_extensions:
                self.console.print(Panel(
                    "[yellow]No extensions found.[/yellow]\n\n"
                    "Extensions include system extensions, Safari extensions, share extensions, and more.",
                    border_style="yellow",
                    box=box.ROUNDED
                ))
                self.console.input("\nPress Enter to return...")
                break

            # Apply filter
            if show_filter == 'enabled':
                current_extensions = [e for e in all_extensions if e['enabled']]
            elif show_filter == 'disabled':
                current_extensions = [e for e in all_extensions if not e['enabled']]
            else:
                current_extensions = all_extensions

            # Show summary
            enabled_count = sum(1 for e in all_extensions if e['enabled'])
            self.console.print(f"[dim]Total: {len(all_extensions)} extensions ({enabled_count} enabled, {len(all_extensions) - enabled_count} disabled)[/dim]")
            self.console.print(f"[dim]Filter: {show_filter.title()} | Showing: {len(current_extensions)} extension(s)[/dim]\n")

            # Limit display to first 50 for performance
            display_extensions = current_extensions[:50]
            if len(current_extensions) > 50:
                self.console.print(f"[yellow]Showing first 50 of {len(current_extensions)} extensions[/yellow]\n")

            # Create table showing extensions
            table = Table(title="[bold bright_white]Extensions Management[/bold bright_white]", box=box.ROUNDED)
            table.add_column("#", style="bright_cyan bold", width=5)
            table.add_column("Name", style="bright_white", width=35, no_wrap=False)
            table.add_column("Type", style="dim", width=13)
            table.add_column("Visibility", style="dim", width=8)
            table.add_column("Status", style="bright_magenta", width=7)
            table.add_column("Pref", style="bright_yellow", width=7)

            for idx, ext in enumerate(display_extensions, 1):
                # Use friendly_name if available, otherwise fall back to name
                display_name = ext.get('friendly_name', ext['name'])
                ext_type = ext.get('type', 'Unknown')
                is_system_ext = ext_type == 'System Extension'
                is_user_visible = ext.get('user_visible', False)

                # Truncate type if needed
                type_display = ext_type[:11] if not is_system_ext else ext_type[:11] + " 🔒"

                # Visibility indicator
                if is_user_visible:
                    visibility = "[green]User[/green]"
                else:
                    visibility = "[dim]Hidden[/dim]"

                enabled = ext['enabled']

                # Determine system status
                system_status = "[green]✓ On[/green]" if enabled else "[dim]✗ Off[/dim]"

                # Get user preference
                bundle_id = ext['bundle_id']
                if bundle_id in configured_preferences:
                    user_pref = configured_preferences[bundle_id]
                    pref_display = "[green]Allow[/green]" if user_pref else "[red]Block[/red]"
                else:
                    pref_display = "[dim]-[/dim]"

                table.add_row(f"{idx}", display_name, type_display, visibility, system_status, pref_display)

            self.console.print(table)
            self.console.print("\n[dim]🔒 = System Extension (requires System Settings to enable/disable)[/dim]")
            self.console.print("[dim]User = Visible in System Settings | Hidden = System/diagnostic extension[/dim]")
            self.console.print("\n[bold]Options:[/bold]")
            self.console.print("  [cyan]1-50[/cyan]    Select extension number to configure")
            self.console.print("  [cyan]f[/cyan]      Filter (all/enabled/disabled)")
            self.console.print("  [cyan]Enter[/cyan]  Return to main menu")

            choice = Prompt.ask("\nYour choice", default="")

            if not choice:
                break
            elif choice.lower() == 'f':
                # Cycle through filters
                if show_filter == 'all':
                    show_filter = 'enabled'
                elif show_filter == 'enabled':
                    show_filter = 'disabled'
                else:
                    show_filter = 'all'
                continue

            try:
                ext_idx = int(choice) - 1
                if 0 <= ext_idx < len(display_extensions):
                    ext = display_extensions[ext_idx]
                    bundle_id = ext['bundle_id']
                    current_pref = configured_preferences.get(bundle_id, ext['enabled'])

                    # Show extension details
                    self.console.print()
                    friendly_name = ext.get('friendly_name', ext['name'])
                    ext_type = ext.get('type', 'Unknown')
                    is_system_extension = ext_type == 'System Extension'

                    detail_text = f"[bold]{friendly_name}[/bold]\n\n"
                    detail_text += f"[dim]Type:[/dim] {ext_type}\n"
                    detail_text += f"[dim]Bundle ID:[/dim] {bundle_id}\n"
                    if ext['version']:
                        detail_text += f"[dim]Version:[/dim] {ext['version']}\n"
                    if ext.get('team_id'):
                        detail_text += f"[dim]Team ID:[/dim] {ext['team_id']}\n"
                    detail_text += f"[dim]Current Status:[/dim] {'Enabled' if ext['enabled'] else 'Disabled'}\n"

                    if is_system_extension:
                        detail_text += f"\n[yellow]⚠ Driver-level System Extension[/yellow]\n"
                        detail_text += f"[dim]Cannot be controlled programmatically[/dim]"

                    self.console.print(Panel(detail_text, border_style="cyan", box=box.ROUNDED))

                    # Warn if system extension
                    if is_system_extension:
                        self.console.print("\n[yellow]This is a driver-level system extension.[/yellow]")
                        self.console.print("[dim]To enable/disable, you must use:[/dim]")
                        self.console.print("[dim]System Settings > General > Login Items & Extensions[/dim]")
                        self.console.print()
                        if not Confirm.ask("[cyan]Save preference anyway (for documentation)?[/cyan]", default=False):
                            self.console.input("\nPress Enter to continue...")
                            continue

                    # Ask for preference
                    new_pref = Confirm.ask(
                        "\n[cyan]Allow this extension?[/cyan]",
                        default=current_pref
                    )

                    # Update config
                    configured_preferences = dict(configured_preferences)
                    configured_preferences[bundle_id] = new_pref
                    self.config_manager.set_setting('system_extension_preferences', configured_preferences)

                    self.console.print(f"\n[green]✓ Saved preference[/green]")

                    # Offer to apply immediately if preference differs from system
                    if new_pref != ext['enabled']:
                        self.console.print()

                        # Don't even offer to apply for system extensions
                        if is_system_extension:
                            self.console.print("[yellow]Preference saved (documentation only)[/yellow]")
                            self.console.print("[dim]To apply: System Settings > General > Login Items & Extensions[/dim]")
                        elif Confirm.ask("[cyan]Apply this change now?[/cyan]", default=True):
                            self.console.print(f"Applying change...", end=" ")

                            if new_pref:
                                success = self.system_extensions_handler.enable_extension(bundle_id)
                            else:
                                success = self.system_extensions_handler.disable_extension(bundle_id)

                            if success:
                                self.console.print("[green]✓ Applied[/green]")
                                self.console.print("[dim]Note: Extension may take a moment to update. Restart the app if needed.[/dim]")
                            else:
                                self.console.print("[red]✗ Failed[/red]")
                                self.console.print("[yellow]This extension cannot be controlled programmatically.[/yellow]")
                        else:
                            self.console.print("[dim]Preference saved. Use 'Apply Settings Now' from main menu to apply later.[/dim]")

                    self.console.input("\nPress Enter to continue...")
                else:
                    self.console.print("[red]Invalid number[/red]")
                    self.console.input("\nPress Enter to continue...")

            except (ValueError, IndexError):
                self.console.print("[red]Invalid input[/red]")
                self.console.input("\nPress Enter to continue...")

    def run_interactive_menu(self):
        """Main interactive menu loop"""
        while True:
            self.console.clear()

            # Create main menu with config name
            title = Text(f"Mac System Configurator - {self.config_name}", style="bold cyan", justify="center")
            self.console.print(Panel(title, box=box.DOUBLE, border_style="cyan"))

            table = Table(show_header=False, box=box.ROUNDED, padding=(0, 2))
            table.add_column("Option", style="cyan", width=8)
            table.add_column("Description", style="bright_white")

            table.add_row("[1]", "Manage Settings")
            table.add_row("[2]", "Apply Settings Now")
            table.add_row("[3]", "Generate AppleScript")
            table.add_row(r"\[e]", "Exit")

            self.console.print(table)

            choice = Prompt.ask(
                "\n[bold]Select option[/bold]",
                choices=["1", "2", "3", "e"],
                show_choices=False
            )

            if choice == '1':
                self.manage_settings()
            elif choice == '2':
                self.apply_settings()
            elif choice == '3':
                self.generate_applescript()
            elif choice == 'e':
                self.console.print("\n[cyan]Goodbye![/cyan]\n")
                break


class ConfigSelector:
    """Handles config file selection and management"""

    def __init__(self):
        self.console = Console()
        self.path_manager = UserConfigPathManager()

    def run(self):
        """Main config selection menu"""
        while True:
            self.console.clear()

            # List available configs
            configs = self.path_manager.list_config_files()

            # Create title
            title = Text("Mac System Configurator", style="bold cyan", justify="center")
            self.console.print(Panel(title, box=box.DOUBLE, border_style="cyan"))

            if not configs:
                # No configs exist - only show create and exit
                self.console.print()
                self.console.print(Panel(
                    "[yellow]No configurations found.[/yellow]\n\n"
                    "Create your first configuration to get started.",
                    border_style="yellow",
                    box=box.ROUNDED
                ))
                self.console.print()

                table = Table(show_header=False, box=box.ROUNDED, padding=(0, 2))
                table.add_column("Option", style="cyan", width=8)
                table.add_column("Description", style="bright_white")
                table.add_row("[1]", "Create New Config")
                table.add_row(r"\[e]", "Exit")
                self.console.print(table)

                choice = Prompt.ask(
                    "\n[bold]Select option[/bold]",
                    choices=["1", "e"],
                    show_choices=False
                )

                if choice == '1':
                    self._create_config()
                elif choice == 'e':
                    self.console.print("\n[cyan]Goodbye![/cyan]\n")
                    break
            else:
                # Show available configs and options
                self.console.print()
                self.console.print(f"[dim]Config directory: {self.path_manager.get_config_dir()}[/dim]")
                self.console.print()

                # List configs
                config_table = Table(title="[bold]Available Configurations[/bold]", box=box.ROUNDED)
                config_table.add_column("#", style="cyan", width=5)
                config_table.add_column("Config Name", style="bright_white")

                for idx, config in enumerate(configs, 1):
                    config_table.add_row(str(idx), config['name'])

                self.console.print(config_table)
                self.console.print()

                # Options menu
                table = Table(show_header=False, box=box.ROUNDED, padding=(0, 2))
                table.add_column("Option", style="cyan", width=8)
                table.add_column("Description", style="bright_white")

                # Dynamically show the correct range based on number of configs
                if len(configs) == 1:
                    config_range = "[1]"
                else:
                    config_range = f"[1-{len(configs)}]"

                table.add_row(config_range, "Edit Config (select number)")
                table.add_row("[c]", "Create New Config")
                table.add_row("[d]", "Delete a Config")
                table.add_row(r"\[e]", "Exit")
                self.console.print(table)

                choice = Prompt.ask(
                    "\n[bold]Select option[/bold]",
                    show_choices=False
                )

                if choice.isdigit():
                    config_idx = int(choice) - 1
                    if 0 <= config_idx < len(configs):
                        self._edit_config(configs[config_idx]['name'])
                    else:
                        self.console.print("[red]Invalid config number[/red]")
                        self.console.input("\nPress Enter to continue...")
                elif choice.lower() == 'c':
                    self._create_config()
                elif choice.lower() == 'd':
                    self._delete_config(configs)
                elif choice.lower() == 'e':
                    self.console.print("\n[cyan]Goodbye![/cyan]\n")
                    break

    def _create_config(self):
        """Create a new configuration"""
        self.console.print()
        self.console.print(Panel(
            "[bold cyan]Create New Configuration[/bold cyan]",
            border_style="cyan",
            box=box.ROUNDED
        ))
        self.console.print()

        while True:
            config_name = Prompt.ask("[cyan]Enter configuration name[/cyan]")

            # Validate name
            valid, error_msg = self.path_manager.validate_config_name(config_name)
            if not valid:
                self.console.print(f"[red]✗ {error_msg}[/red]")
                continue

            # Check if already exists
            if self.path_manager.config_exists(config_name):
                self.console.print(f"[red]✗ Config '{config_name}' already exists[/red]")
                continue

            # Create the config file
            config_path = self.path_manager.get_config_path(config_name)
            config_manager = ConfigManager(config_path)
            config_manager.save_config()  # Save empty config

            self.console.print(f"\n[green]✓ Created config: {config_name}[/green]")
            self.console.input("\nPress Enter to continue...")
            break

    def _delete_config(self, configs):
        """Delete a configuration"""
        self.console.print()
        self.console.print(Panel(
            "[bold red]Delete Configuration[/bold red]",
            border_style="red",
            box=box.ROUNDED
        ))
        self.console.print()

        # Show configs to delete
        config_table = Table(box=box.ROUNDED)
        config_table.add_column("#", style="cyan", width=5)
        config_table.add_column("Config Name", style="bright_white")

        for idx, config in enumerate(configs, 1):
            config_table.add_row(str(idx), config['name'])

        self.console.print(config_table)
        self.console.print()

        choice = Prompt.ask(
            "[yellow]Select config number to delete (or press Enter to cancel)[/yellow]",
            default=""
        )

        if not choice:
            return

        if choice.isdigit():
            config_idx = int(choice) - 1
            if 0 <= config_idx < len(configs):
                config_name = configs[config_idx]['name']

                # Confirm deletion
                if Confirm.ask(f"\n[red]Are you sure you want to delete '{config_name}'?[/red]", default=False):
                    if self.path_manager.delete_config(config_name):
                        self.console.print(f"\n[green]✓ Deleted config: {config_name}[/green]")
                    else:
                        self.console.print(f"\n[red]✗ Failed to delete config[/red]")
                else:
                    self.console.print("\n[dim]Cancelled[/dim]")
            else:
                self.console.print("[red]Invalid config number[/red]")
        else:
            self.console.print("[red]Invalid input[/red]")

        self.console.input("\nPress Enter to continue...")

    def _edit_config(self, config_name):
        """Edit a configuration"""
        configurator = MacConfigurator(config_name, self.path_manager)
        configurator.run_interactive_menu()


def main():
    import sys

    # Initialize path manager
    path_manager = UserConfigPathManager()

    # Check if running in --apply mode (for AppleScript)
    if len(sys.argv) > 1 and sys.argv[1] == '--apply':
        # In apply mode, check if a config name is provided
        if len(sys.argv) > 2:
            config_name = sys.argv[2]
        else:
            # Default to first available config, or error if none exist
            configs = path_manager.list_config_files()
            if not configs:
                print("Error: No configurations found. Create a config first.")
                sys.exit(1)
            config_name = configs[0]['name']

        configurator = MacConfigurator(config_name, path_manager)
        configurator.apply_settings()
    else:
        # Run config selector
        selector = ConfigSelector()
        selector.run()


if __name__ == '__main__':
    main()
