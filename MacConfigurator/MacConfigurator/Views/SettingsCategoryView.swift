//
//  SettingsCategoryView.swift
//  MacConfigurator
//
//  Displays settings for a specific category
//

import SwiftUI

struct SettingsCategoryView: View {
    let category: SettingCategory
    @Binding var profile: ConfigProfile

    @State private var settingStates: [SettingState] = []

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // Category Header
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Image(systemName: category.iconName)
                            .font(.title)
                            .foregroundColor(category.color)

                        Text(category.displayName)
                            .font(.largeTitle)
                            .fontWeight(.bold)
                    }

                    Text("Configure \(category.displayName.lowercased()) settings for your Mac")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                .padding(.bottom, 10)

                // Settings List
                VStack(spacing: 16) {
                    ForEach(settingStates) { state in
                        SettingRow(state: state, profile: $profile)
                    }
                }
            }
            .padding(30)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .background(Color(NSColor.controlBackgroundColor))
        .onAppear {
            loadSettings()
        }
    }

    private func loadSettings() {
        let settings = SettingsSchema.shared.settings(for: category)
        settingStates = settings.map { setting in
            SettingState(
                setting: setting,
                configuredValue: profile.value(for: setting.key),
                systemValue: nil // Will be loaded async
            )
        }
    }
}

// MARK: - Setting Row

struct SettingRow: View {
    let state: SettingState
    @Binding var profile: ConfigProfile

    @State private var isApplying = false
    @State private var showSuccess = false

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(state.setting.title)
                            .font(.headline)

                        if state.setting.requiresAdmin {
                            Image(systemName: "lock.fill")
                                .font(.caption)
                                .foregroundColor(.orange)
                        }

                        Spacer()

                        StatusIndicator(state: state)
                    }

                    Text(state.setting.description)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Spacer()

                SettingControl(state: state, profile: $profile, onChange: {
                    // Auto-save profile when value changes
                    profile.save()
                })

                // Apply Now button
                if state.isConfigured {
                    Button(action: {
                        applyNow()
                    }) {
                        if isApplying {
                            ProgressView()
                                .scaleEffect(0.7)
                                .frame(width: 20, height: 20)
                        } else if showSuccess {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundColor(.green)
                        } else {
                            Text("Apply")
                        }
                    }
                    .buttonStyle(.bordered)
                    .disabled(isApplying)
                }
            }

            Divider()
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(8)
    }

    private func applyNow() {
        guard let value = state.configuredValue else { return }

        isApplying = true

        Task {
            await SettingsApplicator.applySetting(setting: state.setting, value: value)

            await MainActor.run {
                isApplying = false
                showSuccess = true

                // Hide success checkmark after 2 seconds
                Task {
                    try? await Task.sleep(nanoseconds: 2_000_000_000)
                    showSuccess = false
                }
            }
        }
    }
}

// MARK: - Status Indicator

struct StatusIndicator: View {
    let state: SettingState

    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: iconName)
                .foregroundColor(color)
                .font(.caption)

            Text(statusText)
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
    }

    private var iconName: String {
        if !state.isConfigured {
            return "circle"
        }
        return state.isInSync ? "checkmark.circle.fill" : "exclamationmark.triangle.fill"
    }

    private var color: Color {
        if !state.isConfigured {
            return .secondary
        }
        return state.isInSync ? .green : .orange
    }

    private var statusText: String {
        if !state.isConfigured {
            return "Not configured"
        }
        return state.isInSync ? "In sync" : "Out of sync"
    }
}

// MARK: - Setting Control

struct SettingControl: View {
    let state: SettingState
    @Binding var profile: ConfigProfile
    let onChange: () -> Void

    var body: some View {
        switch state.setting.type {
        case .boolean:
            BooleanControl(state: state, profile: $profile, onChange: onChange)

        case .integer(let min, let max):
            IntegerControl(state: state, min: min, max: max, profile: $profile, onChange: onChange)

        case .choice(let options):
            ChoiceControl(state: state, options: options, profile: $profile, onChange: onChange)

        case .string:
            StringControl(state: state, profile: $profile, onChange: onChange)

        case .array, .dictionary:
            ComplexControl(state: state, profile: $profile)
        }
    }
}

// MARK: - Control Implementations

struct BooleanControl: View {
    let state: SettingState
    @Binding var profile: ConfigProfile
    let onChange: () -> Void

    var body: some View {
        Toggle("", isOn: Binding(
            get: { state.configuredValue?.boolValue ?? false },
            set: { newValue in
                profile.setValue(.bool(newValue), for: state.setting.key)
                onChange()
            }
        ))
        .toggleStyle(.switch)
    }
}

struct IntegerControl: View {
    let state: SettingState
    let min: Int
    let max: Int
    @Binding var profile: ConfigProfile
    let onChange: () -> Void

    var body: some View {
        HStack {
            Slider(
                value: Binding(
                    get: { Double(state.configuredValue?.intValue ?? min) },
                    set: { newValue in
                        profile.setValue(.int(Int(newValue)), for: state.setting.key)
                        onChange()
                    }
                ),
                in: Double(min)...Double(max)
            )
            .frame(width: 200)

            Text("\(state.configuredValue?.intValue ?? min)")
                .font(.system(.body, design: .monospaced))
                .frame(width: 40)
        }
    }
}

struct ChoiceControl: View {
    let state: SettingState
    let options: [String]
    @Binding var profile: ConfigProfile
    let onChange: () -> Void

    var body: some View {
        Picker("", selection: Binding(
            get: { state.configuredValue?.stringValue ?? options.first ?? "" },
            set: { newValue in
                profile.setValue(.string(newValue), for: state.setting.key)
                onChange()
            }
        )) {
            ForEach(options, id: \.self) { option in
                Text(option.capitalized).tag(option)
            }
        }
        .pickerStyle(.menu)
        .frame(width: 150)
    }
}

struct StringControl: View {
    let state: SettingState
    @Binding var profile: ConfigProfile
    let onChange: () -> Void

    var body: some View {
        TextField("Value", text: Binding(
            get: { state.configuredValue?.stringValue ?? "" },
            set: { newValue in
                profile.setValue(.string(newValue), for: state.setting.key)
                onChange()
            }
        ))
        .textFieldStyle(.roundedBorder)
        .frame(width: 200)
    }
}

struct ComplexControl: View {
    let state: SettingState
    @Binding var profile: ConfigProfile

    var body: some View {
        Button("Manage...") {
            // Open detail view for complex types
        }
    }
}
