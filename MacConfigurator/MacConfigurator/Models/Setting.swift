//
//  Setting.swift
//  MacConfigurator
//
//  Individual setting definition
//

import Foundation

struct Setting: Identifiable {
    let id: String // Setting key
    let title: String
    let description: String
    let category: SettingCategory
    let type: SettingType
    let requiresAdmin: Bool
    let handler: String

    var key: String { id }
}

enum SettingType: Equatable {
    case boolean
    case integer(min: Int, max: Int)
    case choice([String])
    case string
    case array
    case dictionary
}

// MARK: - System Value

struct SettingState: Identifiable {
    let setting: Setting
    var configuredValue: SettingValue?
    var systemValue: SettingValue?

    var id: String { setting.id }

    var isInSync: Bool {
        guard let configured = configuredValue,
              let system = systemValue else {
            return configuredValue == nil
        }
        return configured == system
    }

    var isConfigured: Bool {
        configuredValue != nil
    }
}
