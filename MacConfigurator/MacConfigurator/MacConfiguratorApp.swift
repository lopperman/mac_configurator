//
//  MacConfiguratorApp.swift
//  MacConfigurator
//
//  Created by Mac System Configurator
//

import SwiftUI

@main
struct MacConfiguratorApp: App {
    @StateObject private var appState = AppState()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(appState)
                .frame(minWidth: 900, minHeight: 600)
        }
        .windowStyle(.hiddenTitleBar)
        .windowResizability(.contentSize)
        .commands {
            CommandGroup(replacing: .newItem) { }
        }

        Settings {
            SettingsView()
                .environmentObject(appState)
        }
    }
}

/// Global application state
class AppState: ObservableObject {
    @Published var currentProfile: ConfigProfile?
    @Published var profiles: [ConfigProfile] = []
    @Published var selectedCategory: SettingCategory = .network

    init() {
        loadProfiles()
    }

    func loadProfiles() {
        // Load profiles from ~/MacConfigurator directory
        // This will be implemented with actual file reading
        profiles = ConfigProfile.loadAll()
        currentProfile = profiles.first
    }

    func saveCurrentProfile() {
        currentProfile?.save()
    }
}
