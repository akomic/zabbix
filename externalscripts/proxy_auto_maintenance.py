#!/usr/bin/python

"""
Automatically creates/destroys infinite maintenance period with data collection for all hosts behind specified zabbix proxy when zabbix-agent on zabbix-proxy is offline
"""

__author__ = "Alen Komic"
__license__ = "GPL"
__version__ = "1.0"

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--hostname",help="Zabbix Proxy Host Name as defined in zabbix", required=True)
parser.add_argument("--apihost",help="Zabbix API URL")
parser.add_argument("--username",help="Zabbix Username")
parser.add_argument("--password",help="Zabbix Password")
parser.add_argument("--action", choices=["activate","deactivate"], help="Action")
parser.add_argument("--verbose",help="Up the verbosity, for debugging purposes", action="count")
args = parser.parse_args()

import os
import sys
import pyzabbix
import requests
import time
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

zuser = ( args.username or os.getenv('ZABBIX_USER') )
zpass = ( args.password or os.getenv('ZABBIX_PASS') )
apihost = ( args.apihost or os.getenv('ZABBIX_API') )

if not zuser or not zpass:
  print "You must specify zabbix apihost, username, password via cli or ENV"
  sys.exit(1)

if not args.action:
  print "You need to specify action"
  sys.exit(1)

zapi = pyzabbix.ZabbixAPI(apihost)
zapi.session.auth = (zuser, zpass)
zapi.session.verify = False

zapi.login(zuser,zpass)
if args.verbose:
  print "Connected to Zabbix API Version %s" % zapi.api_version()

# Default is to return 1 (available), even if zabbix proxy does not exist for the specified host.
proxy_dep_alive=1

proxyhost = zapi.host.get(filter={"host": args.hostname}, output="extend", limit=1)
proxyhost_id = proxyhost[0]['proxy_hostid']
proxyhost_hostid = proxyhost[0]['hostid']
proxyhost_name = proxyhost[0]['name']

if args.action=='activate':
  result = zapi.maintenance.get(filter={"name": "proxydep-{0}-{1}-maintenance".format(proxyhost_name, proxyhost_id)}, output="extend")
  if len(result) == 0:
    target_hosts = []
    for zbx_host in zapi.host.get(proxyids=[proxyhost_id], output="extend"):
      if proxyhost_hostid != zbx_host['hostid']:
        target_hosts.append(zbx_host['hostid'])

    dt_start = int(time.time())
    dt_end = dt_start + 864000

    print "Creating maintenance proxydep-{0}-{1}-maintenance".format(proxyhost_name, proxyhost_id)
    result = zapi.maintenance.create(
      name="proxydep-{0}-{1}-maintenance".format(proxyhost_name, proxyhost_id),
      active_since=dt_start,
      active_till=dt_end,
      hostids=target_hosts,
      timeperiods=[{"timeperiod_type": 0, "start_date": dt_start ,"period": 864000}]
    )
  else:
    print "Maintenance already exists: proxydep-{0}-{1}-maintenance".format(proxyhost_name, proxyhost_id)
elif args.action=='deactivate':
  for maintenance in zapi.maintenance.get(filter={"name": "proxydep-{0}-{1}-maintenance".format(proxyhost_name, proxyhost_id)}, output="extend"):
    print "Destroying maintenance proxydep-{0}-{1}-maintenance".format(proxyhost_name, proxyhost_id)
    result = zapi.maintenance.delete(maintenance['maintenanceid'])
