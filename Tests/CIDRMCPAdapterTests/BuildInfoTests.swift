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

import Testing

@testable import CIDRMCPAdapter

@Test func buildIdentity() {
    #expect(BuildInfo.name == "routeobjects-mcp")
    #expect(BuildInfo.version == "0.1.0")
}
