//
//  SettingCategory.swift
//  MacConfigurator
//
//  Setting categories matching the Python app structure
//

import SwiftUI

enum SettingCategory: String, CaseIterable, Identifiable, Codable {
    case network = "Network"
    case audio = "Audio"
    case dock = "Dock"
    case finder = "Finder"
    case system = "System"
    case startup = "Startup"
    case backgroundApps = "Background Apps"
    case systemExtensions = "System Extensions"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .backgroundApps:
            return "Background Apps"
        case .systemExtensions:
            return "System Extensions"
        default:
            return rawValue
        }
    }

    var iconName: String {
        switch self {
        case .network: return "network"
        case .audio: return "speaker.wave.2"
        case .dock: return "dock.rectangle"
        case .finder: return "folder"
        case .system: return "gearshape"
        case .startup: return "power"
        case .backgroundApps: return "app.badge"
        case .systemExtensions: return "puzzlepiece.extension"
        }
    }

    var color: Color {
        switch self {
        case .network: return .blue
        case .audio: return .purple
        case .dock: return .cyan
        case .finder: return .indigo
        case .system: return .gray
        case .startup: return .green
        case .backgroundApps: return .orange
        case .systemExtensions: return .pink
        }
    }
}
