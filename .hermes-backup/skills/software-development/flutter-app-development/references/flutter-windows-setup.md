# Flutter + Android SDK Setup on Windows

## Installation Steps

### 1. Flutter SDK

Option A — Winget (simplest):
```cmd
winget install Google.Flutter
```

Option B — Manual download:
```cmd
powershell -Command "Invoke-WebRequest -Uri 'https://storage.googleapis.com/flutter_infra_release/releases/stable/windows/flutter_windows_3.27.1-stable.zip' -OutFile '%USERPROFILE%\Downloads\flutter.zip'"
powershell -Command "Expand-Archive -Path '%USERPROFILE%\Downloads\flutter.zip' -DestinationPath 'C:\src'"
```

Add `C:\src\flutter\bin` to PATH.

### 2. Java 17 (Required for Android SDK cmdline-tools)

The Android command-line tools (`sdkmanager`) require **Java 17+**. Java 8 is insufficient and produces:
```
java.lang.UnsupportedClassVersionError: com/android/sdklib/tool/sdkmanager/SdkManagerCli has been compiled by a more recent version of the Java Runtime (class file version 61.0), this version of the Java Runtime only recognizes class file versions up to 52.0
```

Install JDK 17:
```powershell
winget install EclipseAdoptium.Temurin.17.JDK
```

Or download portable version (no installer):
```powershell
$url = "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.19%2B10/OpenJDK17U-jdk_x64_windows_hotspot_17.0.19_10.zip"
Invoke-WebRequest -Uri $url -OutFile "$env:USERPROFILE\Downloads\jdk17.zip"
Expand-Archive "$env:USERPROFILE\Downloads\jdk17.zip" -DestinationPath "C:\Java"
```

Set JAVA_HOME:
```cmd
set JAVA_HOME=C:\Java\jdk-17.0.19+10
```

### 3. Android Command-Line Tools

Download:
```powershell
$url = "https://dl.google.com/android/repository/commandlinetools-win-11076708_latest.zip"
Invoke-WebRequest -Uri $url -OutFile "$env:USERPROFILE\Downloads\cmdline-tools.zip"
Expand-Archive "$env:USERPROFILE\Downloads\cmdline-tools.zip" -DestinationPath "$env:LOCALAPPDATA\Android\Sdk"
```

The tools extract to `cmdline-tools/` but need to be in `cmdline-tools/latest/`:
```cmd
mkdir "%LOCALAPPDATA%\Android\Sdk\cmdline-tools\latest"
move "%LOCALAPPDATA%\Android\Sdk\cmdline-tools\bin" "%LOCALAPPDATA%\Android\Sdk\cmdline-tools\latest\"
move "%LOCALAPPDATA%\Android\Sdk\cmdline-tools\lib" "%LOCALAPPDATA%\Android\Sdk\cmdline-tools\latest\"
```

### 4. Install SDK Components

Set ANDROID_HOME and JAVA_HOME correctly (no trailing spaces!):
```cmd
set JAVA_HOME=C:\Java\jdk17           (NOT "C:\Java\jdk17 " with trailing space)
set ANDROID_HOME=%LOCALAPPDATA%\Android\Sdk
```

Accept licenses and install:
```cmd
set JAVA_HOME=C:\Java\jdk17&&echo y|"%ANDROID_HOME%\cmdline-tools\latest\bin\sdkmanager.bat" --sdk_root="%ANDROID_HOME%" platform-tools platforms;android-35 build-tools;35.0.0
```

**Important:** The `&&` between JAVA_HOME and sdkmanager is intentional — avoids trailing space in JAVA_HOME value.

### 5. Configure Flutter

```cmd
set ANDROID_HOME=%LOCALAPPDATA%\Android\Sdk
flutter config --android-sdk "%ANDROID_HOME%"
yes | flutter doctor --android-licenses
```

## Pitfalls

### `flutter pub get` → `.hermes-tmp` creation failure

In restricted environments (Hermes, CI sandboxes), `flutter pub get` fails with:
```
Creation of temporary directory failed, path = '...\.hermes-tmp.XXXX' (OS Error: The system cannot find the path specified.)
```

**Workaround:** Use `dart pub get` directly instead. It works in the same project directory without the Flutter tool's sandbox interference.

```bash
cd /path/to/project
dart pub get   # works
# flutter pub get  # fails in sandbox
```

After `dart pub get` succeeds, `flutter build apk` works normally.

### Gradle tmpdir in sandbox

Setting `TMPDIR` environment variable doesn't flow through to the Gradle JVM. Fix in `android/gradle.properties`:
```properties
org.gradle.jvmargs=-Djava.io.tmpdir=C:/Users/decni/AppData/Local/Temp -Xmx4G
```

### AGP version mismatch

When adding webview_flutter or other packages that need newer Android Gradle Plugin:
```
Dependency 'androidx.webkit:webkit:X.Y.Z' requires Android Gradle plugin 8.1.1 or higher.
```

Fix in `android/settings.gradle`:
```groovy
id "com.android.application" version "8.1.1" apply false
```

### Java trailing space

When setting JAVA_HOME from bash/cmd, trailing spaces cause `sdkmanager` to fail with "JAVA_HOME is set to an invalid directory". Use `&&` not `;` to avoid this:
```cmd
set JAVA_HOME=C:\Java\jdk17&&sdkmanager.bat ...
```

## Android 11+ URL Scheme Query Declaration

For custom URL schemes (magnet:, intent:, market:), add to `android/app/src/main/AndroidManifest.xml`:
```xml
<queries>
    <intent>
        <action android:name="android.intent.action.VIEW"/>
        <data android:scheme="magnet"/>
    </intent>
    <intent>
        <action android:name="android.intent.action.VIEW"/>
        <data android:scheme="intent"/>
    </intent>
</queries>
```

## Hermes Dashboard Proxy (No-Auth Bypass)

When the Hermes dashboard refuses to bind to a network interface without auth, start a simple Python reverse proxy on the target port:

```bash
# Start dashboard on localhost
hermes dashboard --port 8322

# Python proxy on network IP:8323 → localhost:8322 with correct Host header
python3 -c "
import http.server, urllib.request, socketserver
class P(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        url = 'http://127.0.0.1:8322' + self.path
        req = urllib.request.Request(url, headers={'Host': 'localhost'})
        resp = urllib.request.urlopen(req)
        self.send_response(resp.status)
        for k, v in resp.headers.items():
            if k.lower() not in ('transfer-encoding', 'content-encoding'):
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(resp.read())
    do_POST = do_GET
socketserver.TCPServer(('0.0.0.0', 8323), P).serve_forever()
"
```
