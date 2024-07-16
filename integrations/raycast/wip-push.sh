#!/bin/bash
# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Push
# @raycast.mode fullOutput
# @raycast.packageName wip-cli

# Optional parameters:
# @raycast.icon 📥
# @raycast.argument1 { "type": "text", "placeholder": "WIP Name" }
# @raycast.argument2 { "type": "text", "optional": true, "placeholder": "Notes" }

../../wip push "$1" ${2:+--notes "$2"}
