//
//  ContentView.swift
//  MacConfigurator
//
//  Main application view with sidebar navigation
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var appState: AppState
    @State private var searchText = ""

    var body: some View {
        NavigationSplitView {
            SidebarView(selectedCategory: $appState.selectedCategory)
        } detail: {
            if appState.currentProfile != nil {
                SettingsCategoryView(
                    category: appState.selectedCategory,
                    profile: Binding(
                        get: { appState.currentProfile ?? ConfigProfile(name: "Default") },
                        set: { appState.currentProfile = $0 }
                    )
                )
                .id(appState.selectedCategory)
            } else {
                EmptyProfileView()
            }
        }
        .navigationTitle("Mac Configurator")
        .toolbar {
            ToolbarItem(placement: .navigation) {
                ProfilePickerView()
            }

            ToolbarItem(placement: .primaryAction) {
                Button("Apply Settings") {
                    applySettings()
                }
                .buttonStyle(.borderedProminent)
            }
        }
    }

    private func applySettings() {
        guard let profile = appState.currentProfile else { return }
        Task {
            await SettingsApplicator.apply(profile: profile)
        }
    }
}

// MARK: - Sidebar

struct SidebarView: View {
    @Binding var selectedCategory: SettingCategory

    var body: some View {
        List(SettingCategory.allCases, selection: $selectedCategory) { category in
            Label {
                Text(category.displayName)
            } icon: {
                Image(systemName: category.iconName)
                    .foregroundColor(category.color)
            }
            .tag(category)
        }
        .listStyle(.sidebar)
        .navigationTitle("Categories")
    }
}

// MARK: - Profile Picker

struct ProfilePickerView: View {
    @EnvironmentObject var appState: AppState
    @State private var showingNewProfile = false

    var body: some View {
        Menu {
            ForEach(appState.profiles) { profile in
                Button(profile.name) {
                    appState.currentProfile = profile
                }
            }

            Divider()

            Button("New Profile...") {
                showingNewProfile = true
            }
        } label: {
            HStack {
                Text(appState.currentProfile?.name ?? "No Profile")
                    .font(.headline)
                Image(systemName: "chevron.down")
                    .font(.caption)
            }
        }
        .menuStyle(.borderlessButton)
        .sheet(isPresented: $showingNewProfile) {
            NewProfileSheet()
                .environmentObject(appState)
        }
    }
}

// MARK: - Empty State

struct EmptyProfileView: View {
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "gearshape.2")
                .font(.system(size: 60))
                .foregroundStyle(.secondary)

            Text("No Profile Selected")
                .font(.title2)
                .fontWeight(.semibold)

            Text("Create a new profile to get started")
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

#Preview {
    ContentView()
        .environmentObject(AppState())
}
