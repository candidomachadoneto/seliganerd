# Fotomatic

SwiftUI image search app for macOS. Requires Xcode 15 and macOS 14 or later.

## Building

1. Open Terminal and navigate to this directory:
   ```bash
   cd path/to/Fotomatic
   ```
2. Resolve Swift package dependencies and build:
   ```bash
   swift build -c release
   ```
3. To run in Xcode, create a new project from the package or open `Package.swift` directly.

The app fetches images from Google, Yandex and Pinterest simultaneously and displays them in a responsive grid.
