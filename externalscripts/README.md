# Zabbix External Scripts Collection

## proxy_auto_maintenance

Tested on Zabbix 3.2

Automatically creates/destroys infinite maintenance period with data collection for all hosts behind specified zabbix proxy when zabbix-agent on zabbix-proxy is offline.

Template relies on Zabbix Agent template nodata() item. nodata internval for
proxy zabbix-agent needs to be lower than for the rest of the hosts.

Once imported you need to
- populate macros (on template/or host level).
- create action that triggers the script
