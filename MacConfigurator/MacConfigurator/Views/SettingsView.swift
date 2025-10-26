//
//  SettingsView.swift
//  MacConfigurator
//
//  App preferences/settings
//

import SwiftUI

struct SettingsView: View {
    var body: some View {
        TabView {
            GeneralSettingsView()
                .tabItem {
                    Label("General", systemImage: "gearshape")
                }

            AboutView()
                .tabItem {
                    Label("About", systemImage: "info.circle")
                }
        }
        .frame(width: 500, height: 300)
    }
}

struct GeneralSettingsView: View {
    var body: some View {
        Form {
            Section {
                HStack {
                    Text("Configuration Directory:")
                    Spacer()
                    Text("~/MacConfigurator")
                        .foregroundStyle(.secondary)
                        .font(.system(.body, design: .monospaced))
                }

                Button("Open Configuration Folder") {
                    NSWorkspace.shared.open(ConfigProfile.configDirectory)
                }
            }

            Section {
                Toggle("Apply settings automatically on startup", isOn: .constant(false))
                    .disabled(true)

                Toggle("Show menu bar icon", isOn: .constant(false))
                    .disabled(true)
            }
        }
        .formStyle(.grouped)
        .frame(width: 450)
    }
}

struct AboutView: View {
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "gearshape.2.fill")
                .font(.system(size: 60))
                .foregroundStyle(.blue.gradient)

            Text("Mac Configurator")
                .font(.title)
                .fontWeight(.bold)

            Text("Version 1.0.0")
                .foregroundStyle(.secondary)

            Divider()
                .frame(width: 200)

            Text("Manage and apply Mac system settings with ease")
                .multilineTextAlignment(.center)
                .foregroundStyle(.secondary)
                .frame(width: 300)

            Link("View on GitHub", destination: URL(string: "https://github.com")!)
                .font(.footnote)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding()
    }
}

#Preview {
    SettingsView()
}
