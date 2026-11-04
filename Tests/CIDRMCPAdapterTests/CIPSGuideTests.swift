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

import CIDRToolCore
import Foundation
import MCP
import Testing

@testable import CIDRMCPAdapter

@Test func bundledGuideFitsLegacyBatchFrameBudget() throws {
    // Measure SDK-encoded frames, including JSON escaping and LF, rather than Markdown alone.
    let result = ReadResource.Result(contents: [
        .text(CIPSGuide.text, uri: CIPSGuide.uri, mimeType: "text/markdown")
    ])
    let responses = (1...8).map { ReadResource.response(id: .string(String($0)), result: result) }
    let encoder = JSONEncoder()
    #expect(try encoder.encode(responses[0]).count + 1 <= 65_536)
    #expect(try encoder.encode(responses).count + 1 <= 65_536)
}

@Test func semanticDescriptionsFitNetClawCatalogLimit() {
    // NetClaw's pinned OpenClaw catalog truncates descriptions beyond 1,200 characters.
    for tool in CIDRTool.allCases {
        #expect(tool.description.count <= 1_200)
    }
}
