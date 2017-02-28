#!/bin/bash

date=$(/usr/lib/waggle/edge_processor/scripts/nclogin date +%s)
exit_code=$?
if [ ${exit_code} -ne 0 ]; then
  echo "Warning: Failed to get the time from the Node Controller."
  return ${exit_code}
fi

# if date is not empty, set date
if [ ! "${date}x" == "x" ] ; then
  echo "Setting the system epoch to ${date}..."
  date -s@${date}
  exit_code=$?
  if [ ${exit_code} -ne 0 ] ; then
    echo "Error: failed to set the system date/time."
    exit ${exit_code}
  fi

  # Sync the system time with the hardware clock
  echo "Syncing the hardware clock with the system date/time..."
  hwclock -w
fi
