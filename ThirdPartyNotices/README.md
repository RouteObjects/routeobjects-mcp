# Toolchain runtime notices

These files supplement the exact SwiftPM dependency licenses under an archive's `ThirdPartyLicenses`. Linux pilot binaries statically link Swift/Foundation runtime components from their recorded Swift 6.3.3 toolchain. ARM64 qualification used the official image below; the native x86-64 build used an existing official toolchain managed by Swiftly. The notice-source provenance below is distinct from each executable's compiler/build provenance. macOS binaries use the OS frameworks and Swift runtime. No system libcurl or its dependencies are bundled.

Unmodified notice sources:

- `Swift-Runtime-LICENSE.txt`: `/usr/share/swift/LICENSE.txt` from official image `swift@sha256:1038d54c80063f5cdfabc4560990c30af64b5de8ebf28161deb22ca4ad5db866`.
- `Foundation-ICU-LICENSE.md`: [Swift Foundation ICU, Swift 6.3.3 tag](https://github.com/swiftlang/swift-foundation-icu/blob/swift-6.3.3-RELEASE/LICENSE.md). The tagged source tree is `e29ee41079d35eae68d98a7479864a19f2928d84`. The tagged `_foundation_unicode/uvernum.h` identifies ICU 76.1. Its Apache license with runtime exception also matches the Foundation project's tagged license.
- `Foundation-NOTICE.txt`: [Foundation notices at Swift 6.3.3](https://github.com/swiftlang/swift-foundation/blob/swift-6.3.3-RELEASE/NOTICE.txt).
- `libdispatch-LICENSE.txt`: [libdispatch license at Swift 6.3.3](https://github.com/swiftlang/swift-corelibs-libdispatch/blob/swift-6.3.3-RELEASE/LICENSE).
- `ICU-LICENSE.txt`: [ICU 76.1 license and third-party notices](https://github.com/unicode-org/icu/blob/release-76-1/LICENSE), retained alongside the Foundation ICU distribution notice.

Preserve these files when redistributing the prepared runtime-containing archive. The complete dependency inventory, SDK maintenance source identity and binary checksum are in `BUILD-INFO.json`; exact toolchain and runtime-environment evidence is in the platform verification report.
