//
//  SettingsApplicator.swift
//  MacConfigurator
//
//  Applies settings to the system
//

import Foundation
import AppKit
import UserNotifications

class SettingsApplicator {
    static func apply(profile: ConfigProfile) async {
        // Apply each configured setting
        for (key, value) in profile.settings {
            guard let setting = SettingsSchema.shared.setting(for: key) else {
                continue
            }

            await applySetting(setting: setting, value: value)
        }

        // Show completion notification
        await MainActor.run {
            showNotification(title: "Settings Applied", message: "All configured settings have been applied")
        }
    }

    // Public method for applying individual settings
    static func applySetting(setting: Setting, value: SettingValue) async {
        await applySettingInternal(setting: setting, value: value)
    }

    private static func applySettingInternal(setting: Setting, value: SettingValue) async {
        // Map to appropriate handler based on setting.handler
        switch setting.handler {
        case "AudioInputHandler", "AudioOutputHandler":
            await applyAudioSetting(key: setting.key, value: value)
        case "DockHandler":
            await applyDockSetting(key: setting.key, value: value)
        case "FinderHandler":
            await applyFinderSetting(key: setting.key, value: value)
        case "WiFiHandler":
            await applyNetworkSetting(key: setting.key, value: value)
        case "SystemHandler":
            await applySystemSetting(key: setting.key, value: value)
        case "StartupItemsHandler":
            print("⚠️ Startup items not yet implemented in GUI")
        case "BackgroundAppsHandler":
            print("⚠️ Background apps not yet implemented in GUI")
        case "SystemExtensionsHandler":
            print("⚠️ System extensions not yet implemented in GUI")
        default:
            print("⚠️ Unknown handler: \(setting.handler)")
        }
    }

    // MARK: - Audio Settings

    private static func applyAudioSetting(key: String, value: SettingValue) async {
        switch key {
        case "audio_input_muted":
            if let muted = value.boolValue {
                executeAppleScript("""
                    set volume input volume (if \(muted) then 0 else 50)
                """)
            }

        case "audio_output_volume":
            if let volume = value.intValue {
                executeAppleScript("set volume output volume \(volume)")
            }

        default:
            break
        }
    }

    // MARK: - Dock Settings

    private static func applyDockSetting(key: String, value: SettingValue) async {
        switch key {
        case "dock_autohide":
            if let autohide = value.boolValue {
                executeDefaults("write com.apple.dock autohide -bool \(autohide)")
                restartDock()
            }

        case "dock_position":
            if let position = value.stringValue {
                executeDefaults("write com.apple.dock orientation -string \(position)")
                restartDock()
            }

        default:
            break
        }
    }

    // MARK: - Finder Settings

    private static func applyFinderSetting(key: String, value: SettingValue) async {
        switch key {
        case "finder_show_hidden", "finder_show_hidden_files":
            if let show = value.boolValue {
                executeDefaults("write com.apple.finder AppleShowAllFiles -bool \(show)")
                restartFinder()
            }

        case "finder_show_extensions", "finder_show_all_extensions":
            if let show = value.boolValue {
                executeDefaults("write NSGlobalDomain AppleShowAllExtensions -bool \(show)")
                restartFinder()
            }

        default:
            break
        }
    }

    // MARK: - Network Settings

    private static func applyNetworkSetting(key: String, value: SettingValue) async {
        switch key {
        case "wifi_enabled":
            if let enabled = value.boolValue {
                let state = enabled ? "on" : "off"
                executeCommand("networksetup -setairportpower en0 \(state)")
            }

        default:
            break
        }
    }

    // MARK: - System Settings

    private static func applySystemSetting(key: String, value: SettingValue) async {
        switch key {
        case "screenshot_location":
            if let path = value.stringValue {
                executeDefaults("write com.apple.screencapture location \(path)")
                executeCommand("killall SystemUIServer")
            }

        default:
            break
        }
    }

    // MARK: - Helpers

    private static func executeAppleScript(_ script: String) {
        let appleScript = NSAppleScript(source: script)
        var error: NSDictionary?
        appleScript?.executeAndReturnError(&error)

        if let error = error {
            print("⚠️ AppleScript error: \(error)")
        }
    }

    private static func executeDefaults(_ command: String) {
        executeCommand("defaults \(command)")
    }

    private static func executeCommand(_ command: String) {
        let task = Process()
        task.launchPath = "/bin/sh"
        task.arguments = ["-c", command]
        task.launch()
        task.waitUntilExit()
    }

    private static func restartDock() {
        executeCommand("killall Dock")
    }

    private static func restartFinder() {
        executeCommand("killall Finder")
    }

    @MainActor
    private static func showNotification(title: String, message: String) {
        let center = UNUserNotificationCenter.current()

        // Request permission first (will only prompt once)
        center.requestAuthorization(options: [.alert, .sound]) { granted, error in
            guard granted else { return }

            let content = UNMutableNotificationContent()
            content.title = title
            content.body = message
            content.sound = .default

            let request = UNNotificationRequest(
                identifier: UUID().uuidString,
                content: content,
                trigger: nil
            )

            center.add(request)
        }
    }
}
