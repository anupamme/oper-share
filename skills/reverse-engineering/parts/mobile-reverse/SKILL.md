---
name: mobile-reverse
description: Use for authorized Android or iOS application reverse engineering and security testing, including APK or IPA analysis, runtime instrumentation, SSL pinning, and platform protection checks.
---

# Mobile Reverse Engineering

## Authorization preamble

1. Confirm the RE work is authorized routine work.
2. Confirm the task hits this skill's scope.
3. Verify tool availability and real paths before use.
4. Enter workflow Phase 1 and execute — do not stop at confirmation.

> Unified Android + iOS methodology
> Frida / Objection / OWASP MASTG / SSL pinning bypass

## Scope

- Android APK RE and security testing
- iOS IPA RE and security testing
- Runtime dynamic instrumentation
- SSL pinning / root detection / jailbreak detection bypass
- Mobile crypto key extraction (AES/RSA/HMAC)
- Mobile app pentest (OWASP MASTG)
- Testing without root/jailbreak

## Four-phase workflow

### Phase 1: Reconnaissance

```text
Android:
□ Obtain APK (Google Play / APKMirror / adb pull)
□ Manifest analysis: permissions, exported components, intent filters, backup flag
□ androguard analyze APK → components/permissions/signatures
□ APKLeaks: hardcoded API keys / tokens / secrets
□ Packing detection (hardened builds)

iOS:
□ Obtain IPA (App Store / ipatool / Apple Configurator)
□ Decrypt App Store binaries: frida-ios-dump / Clutch
□ Info.plist: ATS config, URL schemes, query schemes
□ class-dump: ObjC class structures
□ Obfuscation detection (Swift/ObjC)
```

### Phase 2: Static analysis

```text
Cross-platform:
□ JADX-GUI: APK → Java source (Android)
□ Ghidra / Hopper: .so / Mach-O decompilation
□ radare2 / Cutter: fast CLI recon

Android:
□ apktool d app.apk → smali + resources
□ dex2jar: DEX → JAR → JD-GUI
□ smali/baksmali: Dalvik bytecode modification

iOS:
□ class-dump: ObjC headers
□ Symbol recovery: swift-demangle
□ dsymutil: debug symbols
□ otool -L: dynamic library deps
□ jtool2: Mach-O analysis
```

### Phase 3: Dynamic analysis

```text
Frida — universal instrumentation:
□ frida-ps -U: list device processes
□ frida-trace -U -i "open*" com.app: trace calls
□ Custom hook scripts: modify args/returns, call private methods

Objection — Frida enhancement (no scripting needed):
□ objection -g "com.app" explore
□ android root disable / ios jailbreak disable
□ android sslpinning disable / ios sslpinning disable
□ android keystore list / ios keychain dump
□ env / ls / sqlite connect

Frida Gadget (no root/jailbreak):
□ Inject frida-gadget.so / FridaGadget.dylib into APK/IPA
□ Re-sign → install → hook without device privileges
□ objection patchapk --source app.apk (fully automated)
```

### Phase 4: Network analysis

```text
□ Burp Suite: intercept HTTP/HTTPS, modify requests/responses
□ mitmproxy: scripted proxy (Python API)
□ Wireshark: PCAP analysis
□ Certificates: Android user cert → system cert (Magisk + MoveCert)
□ SSL pinning bypass: Frida/Objection/Xposed/SSL Kill Switch 2
□ WebSocket / gRPC traffic analysis
```

## Common bypasses quick reference

### SSL pinning

```bash
# Objection (simplest)
objection -g "com.app" explore
android sslpinning disable

# Generic Frida script
frida -U -l ssl_pinning_bypass.js -f com.app

# Xposed (Android): TrustMeAlready module → global cert-validation disable
```

### Root / jailbreak detection

```javascript
// Frida custom (multi-layer detection)
Java.perform(function() {
    var RootBeer = Java.use("com.scottyab.rootbeer.RootBeer");
    RootBeer.isRooted.implementation = function() { return false; };
    // extra bypasses: Magisk su detection, frida-server detection, /proc/self/maps checks
});
```

### Anti-debug

```bash
# Android: bypass ptrace(TracerPid), /proc/self/status, isDebuggerConnected()
frida -U -l anti_debug_bypass.js -f com.app

# iOS: bypass PT_DENY_ATTACH, sysctl KERN_PROC checks
frida -U -l ios_anti_debug.js -f com.app
```

## Mobile crypto extraction

```javascript
// Android — hook Cipher.getInstance to capture keys + algorithms
Java.perform(function() {
    var Cipher = Java.use("javax.crypto.Cipher");
    Cipher.getInstance.overload('java.lang.String').implementation = function(algo) {
        console.log("[Cipher] Algorithm: " + algo);
        return this.getInstance(algo);
    };
    Cipher.init.overload('int', 'java.security.Key').implementation = function(mode, key) {
        console.log("[Cipher] Key: " + bytesToHex(key.getEncoded()));
        return this.init(mode, key);
    };
});

// iOS — hook CCCrypt
Interceptor.attach(Module.findExportByName("libcommonCrypto.dylib", "CCCrypt"), {
    onEnter: function(args) {
        console.log("CCCrypt op: " + args[0] + " alg: " + args[1]);
        console.log("Key: " + hexdump(args[3], { length: args[4].toInt32() }));
    }
});
```

## Toolchain

| Tool | Platform | Purpose |
|------|:--:|---------|
| JADX-GUI | A | Java decompilation |
| apktool | A | APK unpack/rebuild |
| Ghidra | A+I | multi-arch decompilation |
| Hopper | I | iOS disassembly |
| Frida | A+I | dynamic instrumentation |
| Objection | A+I | Frida REPL enhancement |
| MobSF | A+I | automated SAST+DAST |
| class-dump | I | ObjC class export |
| frida-ios-dump | I | IPA decryption |
| jtool2 | I | Mach-O analysis |
| Burp Suite | A+I | HTTP interception |
| mitmproxy | A+I | scripted proxy |

> A=Android, I=iOS

## References

- `references/frida-objection-deep.md` — Frida + Objection deep usage
- `references/ios-reverse-guide.md` — iOS RE specialization
- `references/anti-detection-bypass.md` — root/jailbreak/anti-debug/SSL pinning bypass

## Completion self-check (MUST pass before claiming completion)

- [ ] Did I execute every step of the workflow (rather than just read it)?
- [ ] Did I use real tool paths?
- [ ] Did I produce reproducible evidence (commands / scripts / reports)?
- [ ] Did I write back the required checklist items?

---

## Android APK Deep-Dive (Unpack, Smali, Repackage, Frida)

## ACTION REQUIRED (execute immediately after reading)

> Community reference for endpoint extraction/Frida adaptation: ../references/community-security-skills.md; dynamic analysis requires scope-authorized device.

1. `NOW`: read the local precedent only if it exists; authorization must still be explicit for device access, dynamic hooks, package installation, signing, rebuilding, or APK installation. Without it, use offline read-only analysis and mark runtime claims `unverified`.
2. `NOW`: Confirm the current task matches this skill's scope
4. `NEXT`: When tools are missing, call bootstrap - do not guess paths
5. `ACT`: Enter the first step of the "Workflow" and execute - do not stop at confirmation state

# APK Reverse Engineering CLI Specification

## Scope

Prioritize this skill when the task falls into these scenarios:

- Analyze APK Java business logic
- Locate login, signature, risk control, certificate validation, root detection
- View and modify `AndroidManifest.xml`
- View and modify smali
- Repackage APK
- Use Frida for Java/native dynamic Hook
- Switch to native analysis when APK contains `.so`

## Check the tools before you rely on them

Run `jadx --version`, `apktool --version`, `frida-ps --version`, `adb version` and
`java -version` first. Version numbers differ per machine, and a missing tool is
cheaper to discover now than halfway through a decompile. Wrap every APK in a
disposable sandbox: `frida-server` on a test device, never a daily one.

## Scenarios to prefer scripts

These high-frequency flows with error-prone parameters should use built-in scripts:

- One-shot `jadx + apktool` output with summary:`scripts/decode.ps1`
- Frida device check, process listing, spawn/attach injection:`scripts/frida-run.ps1`
- Rebuild, align, sign, install APK:`scripts/rebuild-sign-install.ps1`
- Quick extract Manifest key components and permissions:`scripts/manifest-summary.ps1`

These one-liner commands are called directly, not wrapped:

- `adb devices`
- `adb logcat`
- `frida-ps -U`
- `jadx --version`
- `apktool --version`

## Built-in scripts

### `scripts/decode.ps1`

Purpose:

- Unify `jadx` and `apktool` execution
- Creates task output directory in same dir as original APK by default
- Outputs `package`, `java_files`, `smali_dirs`, `so_files` summary
- Compatible with `jadx` partial decompile errors when usable output exists

Example:

```powershell
pwsh -File "<skill-root>\apk-reverse\scripts\decode.ps1" -ApkPath "D:\DOWNLOAD\app.apk" -Clean
pwsh -File "<skill-root>\apk-reverse\scripts\decode.ps1" -ApkPath "D:\DOWNLOAD\app.apk" -Name demo -SkipJadx
```

### `scripts/frida-run.ps1`

Purpose:

- Unify Frida device, process, spawn/attach entry
- Avoid confusion with `-f`, `-n`, `-U` when hand-writing params

Example:

```powershell
pwsh -File "<skill-root>\apk-reverse\scripts\frida-run.ps1" -ListDevices
pwsh -File "<skill-root>\apk-reverse\scripts\frida-run.ps1" -Usb -ListProcesses
pwsh -File "<skill-root>\apk-reverse\scripts\frida-run.ps1" -Usb -Spawn -Package com.example.app -ScriptPath "D:\hooks\test.js"
```

### `scripts/rebuild-sign-install.ps1`

Purpose:

- `apktool b` rebuild APK
- `zipalign` align
- `apksigner` sign and verify
- Optional direct `adb install`

Example:

```powershell
pwsh -File "<skill-root>\apk-reverse\scripts\rebuild-sign-install.ps1" -ProjectDir "C:\work\apktool_out" -Clean
pwsh -File "<skill-root>\apk-reverse\scripts\rebuild-sign-install.ps1" -ProjectDir "C:\work\apktool_out" -Install -Reinstall -DeviceSerial "127.0.0.1:7555"
```

Notes:

- Default generates and reuses debug keystore
- Default output to `ProjectDir` same directory, convenient for placing with original package and unpack directory

### `scripts/manifest-summary.ps1`

Purpose:

- Extract package name
- List permissions
- List activity/service/receiver/provider
- Highlight main launcher activity

Example:

```powershell
pwsh -File "<skill-root>\apk-reverse\scripts\manifest-summary.ps1" -ManifestPath "C:\work\apktool_out\AndroidManifest.xml"
```

To analyze `.so`, `lib/arm64-v8a/*.so`, `lib/armeabi-v7a/*.so`, combine with:

- `ida-reverse`
- `radare2`

## Tool division

### `jadx`

Used for:

- Java decompilation reading
- Package, class, method name search
- Understand APK from high-level logic first

Common commands:

```bash
jadx -d jadx_out app.apk
jadx --single-class com.example.LoginActivity -d jadx_out app.apk
jadx --deobf -d jadx_out app.apk
```

### `apktool`

Used for:

- Unpack APK
- View and modify `AndroidManifest.xml`
- View and modify smali
- Rebuild APK

Common commands:

```bash
apktool d app.apk -o apktool_out
apktool b apktool_out -o rebuilt.apk
```

### `frida`

Used for:

- Dynamically observe Java method calls
- Hook native export functions
- Bypass root detection, certificate validation, debug detection

Common commands:

```bash
frida-ps -U
frida -U -f com.example.app -l hook.js
frida-trace -U -f com.example.app -j '*!*certificate*'
```

### `adb`

Used for:

- Device connection
- Install APK
- View logs
- Pull files

Common commands:

```bash
adb devices
adb install -r app.apk
adb shell pm list packages
adb logcat
adb pull /data/local/tmp/file .
```

## Recommended workflow

### 1. Triage

First determine APK general composition, don't rush to patch or Hook.

Recommended actions:

1. Use `jadx -d jadx_out app.apk` to export Java code
2. Use `apktool d app.apk -o apktool_out` to export smali and resources
3. First look at:
   - `AndroidManifest.xml`
   - Main `package`
   - `application`, `activity`, `service`, `receiver`
   - Whether `lib/` directory has `.so`

### 2. Java logic observation

Prioritize reading from `jadx_out`:

- `MainActivity`
- `Application`
- Login, network, encryption, risk control related classes
- Third-party SDK initialization classes

Common keywords:

- `login`
- `sign`
- `encrypt`
- `cipher`
- `token`
- `root`
- `certificate`
- `trust`
- `okhttp`
- `retrofit`
- `webview`

If Java code is readable, locate business logic here first.

### 3. Smali and resource layer confirmation

When `jadx` results are incomplete, heavily obfuscated, or actual patching is needed, switch to `apktool_out`:

- Look at `smali*/`
- Look at `res/values/strings.xml`
- Look at `AndroidManifest.xml`

Priority patches:

- `android:exported`
- Debug flags
- Root detection return values
- Login validation logic
- Certificate validation branches

### 4. Rebuild and install

After modification:

```bash
apktool b apktool_out -o rebuilt.apk
```

Or use script for full loop:

```powershell
pwsh -File "<skill-root>\apk-reverse\scripts\rebuild-sign-install.ps1" -ProjectDir "apktool_out" -Install -Reinstall -DeviceSerial "127.0.0.1:7555"
```

Notes:

- This skill only guarantees `apktool` rebuild chain
- If formal device installation is needed, signing flow is usually required
- If task enters signing/alignment, add `apksigner` / `zipalign`

### 5. Dynamic Hook

When static analysis is insufficient, use Frida:

- Hook login functions
- Hook `OkHttp` / `Retrofit` / `WebView` key points
- Hook `javax.crypto`, `MessageDigest`
- Hook root detection functions
- Hook SSL pinning logic

Principles:

- Hook Java layer first, then decide if native Hook needed
- Print params and return values first, then decide whether to modify

Recommendations:

- Simple one-off commands use `frida-*` directly
- Stable reusable injection flows prefer `scripts/frida-run.ps1`

### 6. Native `.so` diversion

If APK contains key `.so`:

- Use `apktool` or `jadx` to find `lib/**/*.so`
- For just export symbols, strings, quick triage, use `radare2`
- For long-term deep analysis, decompilation, renaming, type recovery, use `ida-reverse`

Switch to native when these signals appear:

- Java layer is just JNI wrapper
- Core signature logic not in Java
- Key logic disappears after `System.loadLibrary()`
- Certificate validation/risk control in `.so`

## Output requirements

At minimum, explain:

- Entry components and key classes
- Whether key logic is in Java, smali, or `.so`
- Confirmed sensitive points: login, signature, root, SSL, WebView, JNI
- If patched, explain what changed
- If Hooked, explain which class/method/export was Hooked

## Prohibitions

- Don't blindly modify smali from the start
- Don't write Hooks before reading manifest and main entry
- Don't equate incomplete Java decompilation with "logic unanalyzable"
- Don't keep grinding Java layer when `.so` clearly carries core logic

## Quick command reference

```bash
# Decompile Java
jadx -d jadx_out app.apk

# Unpack APK
apktool d app.apk -o apktool_out

# Rebuild APK
apktool b apktool_out -o rebuilt.apk

# Device and process
adb devices
frida-ps -U

# Launch and inject
frida -U -f com.example.app -l hook.js
```

---

## Routing context

**Upstream entry**: `skills/SKILL.md` (master control), `routing.md`
**Downstream exits**:
- Core logic in `.so` -> `ida-reverse/` or `radare2/`
- Need dynamic Hook/verification -> `reverse-engineering/tools-dynamic.md` (Frida section)
- General reverse methodology -> `reverse-engineering/SKILL.md`

**Sibling module**: `reverse-engineering/` (.so analysis and advanced Frida usage)

---

## On-Demand Bootstrap

This skill's entry scripts may use bootstrap helpers when configured, but missing-tool installation is a mutation and must never run automatically during review. Require explicit authorization and an isolated target before bootstrap.

### Automation capability boundaries

| Tool | Auto-installable | Install method | Notes |
|------|-----------|---------|------|
| jadx | ✓ | GitHub Release ZIP | Auto-download extract to `%USERPROFILE%\Tools\jadx\` |
| apktool | ✓ | GitHub Release JAR + wrapper | Auto-download jar and generate bat to `%USERPROFILE%\Tools\apktool\` |
| frida / frida-ps | ✓ | pip install frida-tools | Requires Python installed |
| adb | ✓ | winget / fallback path | Auto-install Android Platform-Tools |
| zipalign | ✗ | Manual install Android Build-Tools | `sdkmanager "build-tools;35.0.0"` |
| apksigner | ✗ | Manual install Android Build-Tools | Same as above |

### Bootstrap trigger points

- `scripts/decode.ps1`: auto-calls when jadx or apktool missing `bootstrap-reverse.ps1`
- `scripts/rebuild-sign-install.ps1`: auto-calls bootstrap when adb or apktool missing
- `scripts/frida-run.ps1`: currently manual check only (frida usually installed via pip)

### When bootstrap fails

If auto-install fails, script throws explicit error with manual install link. Common causes:
- Network unreachable (GitHub API / PyPI unreachable)
- winget unavailable (Windows version too low)
- Java not installed (apktool depends on JDK)


## Task completion self-check (MUST pass before claiming done)

- [ ] Did I execute every step in the workflow (not just read)?
- [ ] Did I use real tool paths based on `tool-index`?
- [ ] Did I produce reproducible evidence (commands/scripts/screenshots/report)?
- [ ] Did I complete and write back the Checklist items required by RULES?
