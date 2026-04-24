# IDE Integration

Integrating an Expo/React Native project with an IDE (Android Studio, VS Code, etc.) so you get both npm script runners and proper native file support.

## Android Studio

When working with Expo/React Native projects in Android Studio, you typically want two things: the ability to easily run the npm scripts (which handle starting the Metro bundler and building the app), and proper IDE support for your native Android files.

Recommended setup:

1. **Create NPM Run Configurations.** Add two entries to the Run/Debug configuration dropdown at the top of Android Studio:
   - **Start Metro** runs `expo start --dev-client`
   - **Run Android** runs `expo run:android` (builds the Android app and launches it on the emulator)

2. **Link the Gradle Project.** Configure Android Studio to recognize the `android/` subdirectory as a native Gradle project.

This gives full IDE features (code completion, syntax highlighting) when editing native files like `build.gradle` or Kotlin/Java files.

## VS Code

VS Code works out of the box for TypeScript/JavaScript. For native files:
- Install the **Kotlin** and **Swift** extensions for syntax highlighting in `android/` and `ios/`.
- Use the built-in terminal to run `npx expo start --dev-client`, `npx expo run:ios`, or `npx expo run:android`.
- For Gradle/Xcode-level debugging, fall back to Android Studio / Xcode — VS Code is the editor, not the build host.
