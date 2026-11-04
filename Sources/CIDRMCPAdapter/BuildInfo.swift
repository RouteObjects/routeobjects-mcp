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

public enum BuildInfo {
    public static let version = "0.1.0"
    public static let name = "routeobjects-mcp"
    public static let cidrVersion = "0.8.1"
    public static let sdkBaseline = "0.12.1"
    #if ROUTEOBJECTS_PATCHED_SDK
        public static let usesDevelopmentSDK = true
    #else
        public static let usesDevelopmentSDK = false
    #endif
}
