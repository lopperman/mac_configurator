//
//  NewProfileSheet.swift
//  MacConfigurator
//
//  Sheet for creating new configuration profiles
//

import SwiftUI

struct NewProfileSheet: View {
    @EnvironmentObject var appState: AppState
    @Environment(\.dismiss) var dismiss

    @State private var profileName = ""
    @State private var showError = false
    @State private var errorMessage = ""

    var body: some View {
        VStack(spacing: 20) {
            Text("Create New Profile")
                .font(.title2)
                .fontWeight(.semibold)

            Text("Enter a name for your configuration profile")
                .foregroundStyle(.secondary)

            TextField("Profile Name", text: $profileName)
                .textFieldStyle(.roundedBorder)
                .frame(width: 300)

            if showError {
                Text(errorMessage)
                    .foregroundColor(.red)
                    .font(.caption)
            }

            HStack {
                Button("Cancel") {
                    dismiss()
                }
                .keyboardShortcut(.cancelAction)

                Button("Create") {
                    createProfile()
                }
                .keyboardShortcut(.defaultAction)
                .disabled(profileName.isEmpty)
            }
        }
        .padding(30)
        .frame(width: 400)
    }

    private func createProfile() {
        // Validate name
        let trimmed = profileName.trimmingCharacters(in: .whitespaces)

        guard !trimmed.isEmpty else {
            showError(message: "Profile name cannot be empty")
            return
        }

        // Check for duplicates
        if appState.profiles.contains(where: { $0.name == trimmed }) {
            showError(message: "A profile with this name already exists")
            return
        }

        // Create and save profile
        let newProfile = ConfigProfile(name: trimmed)
        newProfile.save()

        appState.profiles.append(newProfile)
        appState.currentProfile = newProfile

        dismiss()
    }

    private func showError(message: String) {
        errorMessage = message
        showError = true
    }
}

#Preview {
    NewProfileSheet()
        .environmentObject(AppState())
}
