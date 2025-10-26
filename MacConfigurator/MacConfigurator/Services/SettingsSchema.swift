//
//  SettingsSchema.swift
//  MacConfigurator
//
//  Loads and parses settings_schema.json
//

import Foundation

class SettingsSchema {
    static let shared = SettingsSchema()

    private(set) var settings: [Setting] = []

    private init() {
        loadSchema()
    }

    private func loadSchema() {
        // Load from shared/settings_schema.json
        guard let schemaURL = Bundle.main.url(forResource: "settings_schema", withExtension: "json"),
              let data = try? Data(contentsOf: schemaURL),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let properties = json["properties"] as? [String: Any],
              let settingsObj = properties["settings"] as? [String: Any],
              let settingProps = settingsObj["properties"] as? [String: Any] else {
            // If schema not found in bundle, try loading from shared directory
            loadSchemaFromShared()
            return
        }

        parseSettings(from: settingProps)
    }

    private func loadSchemaFromShared() {
        // Fallback: load from shared directory in project
        let projectRoot = URL(fileURLWithPath: #file)
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()

        let schemaURL = projectRoot.appendingPathComponent("shared/settings_schema.json")

        guard let data = try? Data(contentsOf: schemaURL),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let properties = json["properties"] as? [String: Any],
              let settingsObj = properties["settings"] as? [String: Any],
              let settingProps = settingsObj["properties"] as? [String: Any] else {
            print("⚠️ Could not load settings schema")
            return
        }

        parseSettings(from: settingProps)
    }

    private func parseSettings(from properties: [String: Any]) {
        settings = properties.compactMap { key, value -> Setting? in
            guard let dict = value as? [String: Any],
                  let title = dict["title"] as? String,
                  let description = dict["description"] as? String,
                  let categoryStr = dict["category"] as? String,
                  let category = SettingCategory(rawValue: categoryStr),
                  let handler = dict["handler"] as? String,
                  let typeStr = dict["type"] as? String else {
                return nil
            }

            let requiresAdmin = dict["requires_admin"] as? Bool ?? false
            let type = parseType(typeStr: typeStr, dict: dict)

            return Setting(
                id: key,
                title: title,
                description: description,
                category: category,
                type: type,
                requiresAdmin: requiresAdmin,
                handler: handler
            )
        }
    }

    private func parseType(typeStr: String, dict: [String: Any]) -> SettingType {
        switch typeStr {
        case "boolean":
            return .boolean
        case "integer":
            let min = dict["minimum"] as? Int ?? 0
            let max = dict["maximum"] as? Int ?? 100
            return .integer(min: min, max: max)
        case "string":
            if let enumValues = dict["enum"] as? [String] {
                return .choice(enumValues)
            }
            return .string
        case "array":
            return .array
        case "object":
            return .dictionary
        default:
            return .string
        }
    }

    // MARK: - Public API

    func settings(for category: SettingCategory) -> [Setting] {
        settings.filter { $0.category == category }
    }

    func setting(for key: String) -> Setting? {
        settings.first { $0.key == key }
    }
}
