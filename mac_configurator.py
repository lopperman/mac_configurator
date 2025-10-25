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


def is_admin():
    """Check if current user has admin privileges"""
    try:
        # Check if user is in admin group (GID 80 on macOS)
        return 'admin' in [grp.getgrgid(g).gr_name for g in os.getgroups()]
    except:
        return False


class ConfigManager:
    """Manages configuration file operations"""

    def __init__(self, config_path='config.json'):
        self.config_path = Path(config_path)
        self.config = self.load_config()

    def load_config(self):
        """Load configuration from JSON file"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {"settings": {}}

    def save_config(self):
        """Save configuration to JSON file"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)

    def get_setting(self, key):
        """Get a specific setting value"""
        return self.config.get('settings', {}).get(key)

    def set_setting(self, key, value):
        """Set a specific setting value"""
        if 'settings' not in self.config:
            self.config['settings'] = {}
        self.config['settings'][key] = value
        self.save_config()


class WiFiHandler:
    """Handles WiFi-related operations"""

    @staticmethod
    def get_current_state():
        """Get current WiFi state (enabled/disabled)"""
        try:
            result = subprocess.run(
                ['networksetup', '-getairportpower', 'en0'],
                capture_output=True,
                text=True,
                check=True
            )
            # Output format: "Wi-Fi Power (en0): On" or "Wi-Fi Power (en0): Off"
            return 'On' in result.stdout
        except subprocess.CalledProcessError:
            print("Error: Could not get WiFi state")
            return None

    @staticmethod
    def set_state(enabled):
        """Set WiFi state (True=on, False=off)"""
        try:
            state = 'on' if enabled else 'off'
            subprocess.run(
                ['networksetup', '-setairportpower', 'en0', state],
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            print(f"Error: Could not set WiFi to {state}")
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


class MacConfigurator:
    """Main application class"""

    def __init__(self):
        self.console = Console()
        self.config_manager = ConfigManager()
        self.is_admin = is_admin()

        # Handlers
        self.wifi_handler = WiFiHandler()
        self.audio_input_handler = AudioInputHandler()
        self.audio_output_handler = AudioOutputHandler()
        self.dock_handler = DockHandler()
        self.finder_handler = FinderHandler()
        self.system_handler = SystemHandler()

        # Define settings structure organized by category
        self.categories = {
            'Network': {
                'wifi_enabled': {
                    'name': 'WiFi Enabled',
                    'type': 'boolean',
                    'get_current': self.wifi_handler.get_current_state,
                    'set_value': self.wifi_handler.set_state,
                    'requires_admin': True
                }
            },
            'Audio': {
                'audio_input_muted': {
                    'name': 'Input Muted',
                    'type': 'boolean',
                    'get_current': self.audio_input_handler.get_mute_state,
                    'set_value': self.audio_input_handler.set_mute_state,
                    'requires_admin': False
                },
                'audio_output_volume': {
                    'name': 'Output Volume',
                    'type': 'integer',
                    'min': 0,
                    'max': 100,
                    'get_current': self.audio_output_handler.get_volume,
                    'set_value': self.audio_output_handler.set_volume,
                    'requires_admin': False
                }
            },
            'Dock': {
                'dock_autohide': {
                    'name': 'Auto-hide Dock',
                    'type': 'boolean',
                    'get_current': self.dock_handler.get_autohide,
                    'set_value': self.dock_handler.set_autohide,
                    'requires_admin': False
                },
                'dock_position': {
                    'name': 'Dock Position',
                    'type': 'choice',
                    'choices': ['left', 'bottom', 'right'],
                    'get_current': self.dock_handler.get_position,
                    'set_value': self.dock_handler.set_position,
                    'requires_admin': False
                }
            },
            'Finder': {
                'finder_show_hidden': {
                    'name': 'Show Hidden Files',
                    'type': 'boolean',
                    'get_current': self.finder_handler.get_show_hidden_files,
                    'set_value': self.finder_handler.set_show_hidden_files,
                    'requires_admin': False
                },
                'finder_show_extensions': {
                    'name': 'Show All Extensions',
                    'type': 'boolean',
                    'get_current': self.finder_handler.get_show_extensions,
                    'set_value': self.finder_handler.set_show_extensions,
                    'requires_admin': False
                }
            },
            'System': {
                'screenshot_location': {
                    'name': 'Screenshot Location',
                    'type': 'string',
                    'get_current': self.system_handler.get_screenshot_location,
                    'set_value': self.system_handler.set_screenshot_location,
                    'requires_admin': False
                }
            }
        }

    def manage_settings(self):
        """Interactive settings manager with category navigation"""
        while True:
            self.console.clear()

            # Create categories table
            table = Table(title="Manage Settings - Select Category", box=box.ROUNDED, show_header=False)
            table.add_column("Option", style="cyan", width=8)
            table.add_column("Category", style="bright_white")

            category_list = list(self.categories.keys())
            for idx, category in enumerate(category_list, 1):
                table.add_row(f"[{idx}]", category)

            self.console.print(table)
            self.console.print("\n[dim]Press Enter to return to main menu[/dim]")

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
                    "[yellow]⚠[/yellow] You are not running as admin. Settings marked with [red]🔒[/red] will not be applied.",
                    border_style="yellow",
                    box=box.ROUNDED
                ))
                self.console.print()

            # Create settings table
            table = Table(title=f"{category_name} Settings", box=box.ROUNDED)
            table.add_column("Option", style="cyan", width=8)
            table.add_column("Setting", style="bright_white", width=25)
            table.add_column("Configured", style="yellow", width=15)
            table.add_column("Current", style="magenta", width=15)
            table.add_column("Status", justify="center", width=8)

            for idx, setting_key in enumerate(setting_keys, 1):
                setting_info = settings[setting_key]
                configured_value = self.config_manager.get_setting(setting_key)
                current_value = setting_info['get_current']()

                if configured_value == current_value:
                    status = "[green]✓[/green]"
                else:
                    status = "[yellow]⚠[/yellow]"

                # Add lock icon if requires admin and user is not admin
                setting_name = setting_info['name']
                if setting_info.get('requires_admin', False) and not self.is_admin:
                    setting_name = f"{setting_name} [red]🔒[/red]"

                table.add_row(
                    f"[{idx}]",
                    setting_name,
                    str(configured_value),
                    str(current_value),
                    status
                )

            self.console.print(table)
            self.console.print("\n[dim]Press Enter to return to category menu[/dim]")

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
        system_value = setting_info['get_current']()
        requires_admin = setting_info.get('requires_admin', False)

        self.console.print(f"\n[bold]{setting_info['name']}[/bold]")
        if requires_admin and not self.is_admin:
            self.console.print("[red]🔒 Requires admin privileges[/red]")
        self.console.print(f"  Configured: [yellow]{current_value}[/yellow]")
        self.console.print(f"  System:     [magenta]{system_value}[/magenta]")

        new_value = None
        value_changed = False

        if setting_info['type'] == 'boolean':
            result = Confirm.ask(
                f"\nSet {setting_info['name']} to",
                default=current_value if isinstance(current_value, bool) else True
            )
            if result != current_value:
                self.config_manager.set_setting(setting_key, result)
                self.console.print(f"[green]✓[/green] {setting_info['name']} set to [yellow]{result}[/yellow]")
                new_value = result
                value_changed = True
            else:
                self.console.print(f"[dim]Value unchanged[/dim]")

        elif setting_info['type'] == 'integer':
            min_val = setting_info.get('min', 0)
            max_val = setting_info.get('max', 100)

            try:
                value = IntPrompt.ask(
                    f"\nSet value ({min_val}-{max_val})",
                    default=current_value if isinstance(current_value, int) else min_val
                )
                if min_val <= value <= max_val:
                    if value != current_value:
                        self.config_manager.set_setting(setting_key, value)
                        self.console.print(f"[green]✓[/green] {setting_info['name']} set to [yellow]{value}[/yellow]")
                        new_value = value
                        value_changed = True
                    else:
                        self.console.print(f"[dim]Value unchanged[/dim]")
                else:
                    self.console.print(f"[red]✗[/red] Value must be between {min_val} and {max_val}")
            except (ValueError, KeyboardInterrupt):
                self.console.print("[yellow]Cancelled[/yellow]")

        elif setting_info['type'] == 'choice':
            choices = setting_info.get('choices', [])
            result = Prompt.ask(
                f"\nSelect {setting_info['name']}",
                choices=choices,
                default=current_value if current_value in choices else choices[0]
            )
            if result != current_value:
                self.config_manager.set_setting(setting_key, result)
                self.console.print(f"[green]✓[/green] {setting_info['name']} set to [yellow]{result}[/yellow]")
                new_value = result
                value_changed = True
            else:
                self.console.print(f"[dim]Value unchanged[/dim]")

        elif setting_info['type'] == 'string':
            result = Prompt.ask(
                f"\nEnter {setting_info['name']}",
                default=str(current_value) if current_value else ""
            )
            if result != current_value:
                self.config_manager.set_setting(setting_key, result)
                self.console.print(f"[green]✓[/green] {setting_info['name']} set to [yellow]{result}[/yellow]")
                new_value = result
                value_changed = True
            else:
                self.console.print(f"[dim]Value unchanged[/dim]")

        # Check if we should apply the setting now
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
                        else:
                            self.console.print("[red]✗ Failed[/red]")
                    else:
                        self.console.print("[dim]Skipped - use 'Apply Settings Now' from main menu to apply later[/dim]")

        self.console.input("\nPress Enter to continue...")

    def apply_settings(self):
        """Apply configured settings to the system"""
        self.console.clear()
        self.console.print(Panel.fit("[bold cyan]Applying Settings[/bold cyan]", box=box.DOUBLE))

        # Collect settings that need to be applied
        to_apply = []
        skipped_admin = []
        for category_name, settings in self.categories.items():
            for setting_key, setting_info in settings.items():
                configured_value = self.config_manager.get_setting(setting_key)
                current_value = setting_info['get_current']()

                if configured_value is not None and configured_value != current_value:
                    # Check if requires admin
                    if setting_info.get('requires_admin', False) and not self.is_admin:
                        skipped_admin.append((setting_key, setting_info, configured_value))
                    else:
                        to_apply.append((setting_key, setting_info, configured_value))

        # Show skipped admin settings warning
        if skipped_admin:
            self.console.print()
            self.console.print(Panel(
                f"[yellow]⚠ Skipping {len(skipped_admin)} setting(s) that require admin privileges:[/yellow]\n" +
                "\n".join([f"  • {info['name']}" for _, info, _ in skipped_admin]),
                border_style="yellow",
                box=box.ROUNDED
            ))

        if not to_apply and not skipped_admin:
            self.console.print("\n[green]✓[/green] All settings already match configured state!")
        elif not to_apply:
            self.console.print("\n[yellow]No settings to apply (all require admin or match current state)[/yellow]")
        else:
            self.console.print(f"\n[cyan]Applying {len(to_apply)} setting(s)...[/cyan]\n")

            # Apply settings with progress tracking
            for setting_key, setting_info, configured_value in to_apply:
                self.console.print(f"Applying [bold]{setting_info['name']}[/bold]: [yellow]{configured_value}[/yellow]...", end=" ")

                if setting_info['set_value'](configured_value):
                    self.console.print("[green]✓ Success[/green]")
                else:
                    self.console.print("[red]✗ Failed[/red]")

        self.console.print()
        self.console.input("Press Enter to continue...")

    def generate_applescript(self):
        """Generate an AppleScript that can be run at startup or ad-hoc"""
        self.console.clear()

        script_content = '''#!/usr/bin/osascript
# Mac System Configurator - Auto-apply Script
# This script applies configured system settings

do shell script "python3 ''' + str(Path.cwd() / 'mac_configurator.py') + ''' --apply" with administrator privileges
'''

        script_path = Path.cwd() / 'apply_settings.scpt'
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

    def run_interactive_menu(self):
        """Main interactive menu loop"""
        while True:
            self.console.clear()

            # Create main menu
            title = Text("Mac System Configurator", style="bold cyan", justify="center")
            self.console.print(Panel(title, box=box.DOUBLE, border_style="cyan"))

            table = Table(show_header=False, box=box.ROUNDED, padding=(0, 2))
            table.add_column("Option", style="cyan", width=8)
            table.add_column("Description", style="bright_white")

            table.add_row("[1]", "Manage Settings")
            table.add_row("[2]", "Apply Settings Now")
            table.add_row("[3]", "Generate AppleScript")
            table.add_row("[e]", "Exit")

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


def main():
    import sys

    # Check if running in --apply mode (for AppleScript)
    if len(sys.argv) > 1 and sys.argv[1] == '--apply':
        configurator = MacConfigurator()
        configurator.apply_settings()
    else:
        # Run interactive menu
        configurator = MacConfigurator()
        configurator.run_interactive_menu()


if __name__ == '__main__':
    main()
