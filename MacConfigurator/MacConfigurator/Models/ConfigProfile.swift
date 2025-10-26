//
//  ConfigProfile.swift
//  MacConfigurator
//
//  Configuration profile model
//

import Foundation

struct ConfigProfile: Identifiable, Codable {
    let id: UUID
    var name: String
    var settings: [String: SettingValue]

    init(id: UUID = UUID(), name: String, settings: [String: SettingValue] = [:]) {
        self.id = id
        self.name = name
        self.settings = settings
    }

    // MARK: - File Management

    static var configDirectory: URL {
        let home = FileManager.default.homeDirectoryForCurrentUser
        return home.appendingPathComponent("MacConfigurator")
    }

    var fileURL: URL {
        Self.configDirectory.appendingPathComponent("\(name)_config.json")
    }

    static func loadAll() -> [ConfigProfile] {
        let configDir = configDirectory

        // Ensure directory exists
        try? FileManager.default.createDirectory(at: configDir, withIntermediateDirectories: true)

        guard let files = try? FileManager.default.contentsOfDirectory(
            at: configDir,
            includingPropertiesForKeys: nil
        ) else {
            return [Self.createDefault()]
        }

        let profiles = files
            .filter { $0.pathExtension == "json" && $0.lastPathComponent.hasSuffix("_config.json") }
            .compactMap { url -> ConfigProfile? in
                try? Self.load(from: url)
            }

        return profiles.isEmpty ? [Self.createDefault()] : profiles
    }

    static func load(from url: URL) throws -> ConfigProfile {
        let data = try Data(contentsOf: url)
        let decoder = JSONDecoder()
        var profile = try decoder.decode(ConfigProfile.self, from: data)

        // Extract name from filename if needed
        let filename = url.deletingPathExtension().lastPathComponent
        if filename.hasSuffix("_config") {
            profile.name = String(filename.dropLast(7)) // Remove "_config"
        }

        return profile
    }

    func save() {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]

        guard let data = try? encoder.encode(self) else { return }

        try? FileManager.default.createDirectory(
            at: Self.configDirectory,
            withIntermediateDirectories: true
        )

        try? data.write(to: fileURL)
    }

    static func createDefault() -> ConfigProfile {
        let profile = ConfigProfile(name: "Default")
        profile.save()
        return profile
    }

    // MARK: - Setting Management

    func value(for key: String) -> SettingValue? {
        settings[key]
    }

    mutating func setValue(_ value: SettingValue?, for key: String) {
        if let value = value {
            settings[key] = value
        } else {
            settings.removeValue(forKey: key)
        }
    }
}

// MARK: - Setting Value

enum SettingValue: Codable, Equatable {
    case bool(Bool)
    case int(Int)
    case string(String)
    case array([String])
    case dictionary([String: Bool])

    var boolValue: Bool? {
        if case .bool(let value) = self { return value }
        return nil
    }

    var intValue: Int? {
        if case .int(let value) = self { return value }
        return nil
    }

    var stringValue: String? {
        if case .string(let value) = self { return value }
        return nil
    }

    var arrayValue: [String]? {
        if case .array(let value) = self { return value }
        return nil
    }

    var dictionaryValue: [String: Bool]? {
        if case .dictionary(let value) = self { return value }
        return nil
    }
}
