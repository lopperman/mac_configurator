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
        # Category icons and colors
        category_styles = {
            'Network': ('🌐', 'blue'),
            'Audio': ('🔊', 'magenta'),
            'Dock': ('📱', 'cyan'),
            'Finder': ('📁', 'green'),
            'System': ('⚙️', 'yellow')
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
            table.add_column("Configured", style="bright_yellow", width=15, header_style="bright_yellow bold")
            table.add_column("Current", style="bright_magenta", width=15, header_style="bright_magenta bold")
            table.add_column("Status", justify="center", width=8, header_style="bright_white bold")

            for idx, setting_key in enumerate(setting_keys, 1):
                setting_info = settings[setting_key]
                configured_value = self.config_manager.get_setting(setting_key)
                current_value = setting_info['get_current']()

                # Color-coded status with different symbols
                if configured_value == current_value:
                    status = "[bold green]✓[/bold green]"
                    configured_str = f"[dim]{configured_value}[/dim]"
                    current_str = f"[dim]{current_value}[/dim]"
                else:
                    status = "[bold yellow]⚠[/bold yellow]"
                    configured_str = f"[bold bright_yellow]{configured_value}[/bold bright_yellow]"
                    current_str = f"[bold bright_magenta]{current_value}[/bold bright_magenta]"

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

        # Show comparison in a mini table
        comparison_table = Table(show_header=True, box=box.SIMPLE, padding=(0, 1))
        comparison_table.add_column("Source", style="dim")
        comparison_table.add_column("Value", style="bold")

        comparison_table.add_row("Configured", f"[bright_yellow]{current_value}[/bright_yellow]")
        comparison_table.add_row("System", f"[bright_magenta]{system_value}[/bright_magenta]")

        self.console.print(comparison_table)

        new_value = None
        value_changed = False

        if setting_info['type'] == 'boolean':
            result = Confirm.ask(
                f"\n[cyan]Set {setting_info['name']} to[/cyan]",
                default=current_value if isinstance(current_value, bool) else True
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

            try:
                value = IntPrompt.ask(
                    f"\n[cyan]Set value ({min_val}-{max_val})[/cyan]",
                    default=current_value if isinstance(current_value, int) else min_val
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
            result = Prompt.ask(
                f"\n[cyan]Select {setting_info['name']}[/cyan]",
                choices=choices,
                default=current_value if current_value in choices else choices[0]
            )
            if result != current_value:
                self.config_manager.set_setting(setting_key, result)
                self.console.print(f"\n[bold green]✓ Saved[/bold green] → [bright_yellow]{result}[/bright_yellow]")
                new_value = result
                value_changed = True
            else:
                self.console.print(f"\n[dim italic]→ Value unchanged[/dim italic]")

        elif setting_info['type'] == 'string':
            result = Prompt.ask(
                f"\n[cyan]Enter {setting_info['name']}[/cyan]",
                default=str(current_value) if current_value else ""
            )
            if result != current_value:
                self.config_manager.set_setting(setting_key, result)
                self.console.print(f"\n[bold green]✓ Saved[/bold green] → [bright_yellow]{result}[/bright_yellow]")
                new_value = result
                value_changed = True
            else:
                self.console.print(f"\n[dim italic]→ Value unchanged[/dim italic]")

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
                self.console.print(f"  [dim]•[/dim] [bold bright_white]{setting_info['name']}[/bold bright_white] → [bright_yellow]{configured_value}[/bright_yellow] ", end="")

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
