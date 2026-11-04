// swift-tools-version: 6.2

//===----------------------------------------------------------------------===//
//
// This source file is part of the routeobjects-mcp project.
//
// Copyright (c) 2026 Craig A. Munro
//
// Licensed under the Apache License, Version 2.0.
// See the LICENSE file for details.
//
// SPDX-License-Identifier: Apache-2.0
//
//===----------------------------------------------------------------------===//

import Foundation
import PackageDescription

// CHANGE: Keep the immutable revision in the manifest so SwiftPM cache invalidation observes pin changes.
// The build verifier requires this literal and SDKSelection.json to agree; nil means reviewed local development.
let maintenanceSDKRevision: String? = "10cb175661ab095abfc73cf293a0c79af244e61e"
let sdkPath = ProcessInfo.processInfo.environment["ROUTEOBJECTS_MCP_SDK_PATH"]
let sdk: Package.Dependency
if let revision = maintenanceSDKRevision {
    precondition(revision.count == 40 && revision.utf8.allSatisfy { (48...57).contains($0) || (97...102).contains($0) }
        && revision != "a0ae212ebf6eab5f754c3129608bc5557637e605", "An exact maintenance commit is required.")
    precondition(sdkPath == nil, "Pinned SDK selection rejects local SDK overrides.")
    sdk = .package(url: "https://github.com/RouteObjects/swift-sdk.git", revision: revision)
} else {
    sdk = .package(url: "https://github.com/modelcontextprotocol/swift-sdk.git", exact: "0.12.1")
}
let adapterSettings: [SwiftSetting] = sdkPath != nil || maintenanceSDKRevision != nil
    ? [.define("ROUTEOBJECTS_PATCHED_SDK")] : []

let package = Package(
    name: "routeobjects-mcp",
    platforms: [.macOS(.v15)],
    products: [.executable(name: "routeobjects-mcp", targets: ["RouteObjectsMCP"])],
    dependencies: [
        .package(url: "https://github.com/RouteObjects/swift-cidr.git", exact: "0.8.1"),
        sdk,
        .package(url: "https://github.com/apple/swift-log.git", exact: "1.6.2"),
        .package(url: "https://github.com/apple/swift-system.git", exact: "1.4.0"),
    ],
    targets: [
        .target(name: "CIDRToolCore", dependencies: [.product(name: "CIDR", package: "swift-cidr")]),
        .target(
            name: "CIDRMCPAdapter",
            dependencies: [
                "CIDRToolCore", .product(name: "MCP", package: "swift-sdk"),
                .product(name: "Logging", package: "swift-log"),
                .product(name: "SystemPackage", package: "swift-system"),
            ],
            swiftSettings: adapterSettings),
        .executableTarget(name: "RouteObjectsMCP", dependencies: ["CIDRMCPAdapter"]),
        .testTarget(name: "CIDRToolCoreTests", dependencies: ["CIDRToolCore"]),
        .testTarget(
            name: "CIDRMCPAdapterTests",
            dependencies: ["CIDRMCPAdapter", "CIDRToolCore", .product(name: "MCP", package: "swift-sdk")]),
    ],
    swiftLanguageModes: [.v6]
)
