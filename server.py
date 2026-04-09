#!/usr/bin/env python3
"""
Rhino Jewellery MCP Server — 155 jewelry CAD tools.
Each tool returns RhinoScript code for mcp__rhino__execute_rhinoscript_python_code.
"""

from app import mcp

import tools.necklace
import tools.gems
import tools.settings
import tools.rings
import tools.jewelry_types
import tools.chains
import tools.patterns
import tools.utils
import tools.finishing
import tools.manufacturing
import tools.presentation

if __name__ == "__main__":
    mcp.run(transport="stdio")
