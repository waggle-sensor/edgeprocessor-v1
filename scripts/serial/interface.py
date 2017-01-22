import fileinput
import json
import os
import socket
import subprocess

def process_loop():
  script_dir = '/usr/lib/waggle/guestnode/scripts'
  for line in fileinput.input():
    instruction=json.loads(line)
    print(json.dumps(instruction, indent=2, separators=(',', ': ')))
    command = instruction["args"][0]
    args = []
    if len(instruction["args"]) > 1:
      args = instruction["args"][1:]
    if command == "quit":
      print(json.dumps({"rc":0}))
      return
    elif command == "nodeid":
      # arp -a 10.31.81.10
      arp_output = subprocess.check_output('arp -a 10.31.81.10')
      # ex: nodecontroller (10.31.81.10) at 00:1e:06:10:7d:97 [ether] on enx001e06303eaa
      node_id = arp_output[32:49].replace(':', '')
      print(json.dumps({"rc":0, "id":node_id}))
    elif command == "disk":
      print(json.dumps({"rc":0, "id":socket.gethostname()[12:15]}))
    elif command == "test":
      return_value = os.system(''.join((script_dir, "/run-tests")))
      print(json.dumps({"rc":return_value.to_bytes(2, byteorder='big')[0]}))
    elif command == "lockdown":
      return_value = os.system(''.join((script_dir, "/lockdown")))
      print(json.dumps({"rc":return_value.to_bytes(2, byteorder='big')[0]}))
    else:
      print(json.dumps({"rc":99, "pythonError":"unrecognized command"}))

if __name__ == '__main__':
  process_loop()
