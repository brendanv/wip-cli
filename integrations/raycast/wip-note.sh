#!/bin/bash
# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Note
# @raycast.mode fullOutput
# @raycast.packageName wip-cli

# Optional parameters:
# @raycast.icon 📝
# @raycast.argument1 { "type": "text", "optional": false, "placeholder": "Note content" }

../../wip note "$1"
../../wip current
