#!/bin/bash
# Double-click this file in Finder to publish your website edits.
cd "$(dirname "$0")"
echo "Publishing website..."
echo
if bash publish.sh "Website update"; then
  echo
  echo "Done. You can close this window."
else
  echo
  echo "Something went wrong - see the message above."
fi
read -n 1 -s -r -p "Press any key to close..."
echo
