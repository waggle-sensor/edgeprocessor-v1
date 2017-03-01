#!/bin/bash

date=$1

date -s@${date}

# Sync the system time with the hardware clock
echo "Syncing the Edge Processor hardware clock with the system date/time..."
hwclock -w
