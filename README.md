# Generate JSON file for RackStack Deploy

## Intro
Generate JSON file for RackStack Deploy.

## Design
* Prepare node info, like sn, ipmi at etc.
* Put info into excel

* User update required fields, like nic bond mapping, ip, at etc
* Convert excel to json


## Usage
* python gen_rackstack_json.py prepare
* python gen_rackstack_json.py generate