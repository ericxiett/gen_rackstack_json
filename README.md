# Generate JSON file for RackStack Deploy

## Intro
Generate JSON file for RackStack Deploy.

## Design
* Prepare node info, like sn, ipmi at etc.
* Put info into excel

* User update required fields, like nic bond mapping, ip, at etc
* Convert excel to json

Excel fields example:

|index|region|sn|ipmi_addr|role|mgm_nic1|mgm_nic2|mgm_ip|inter_nic1|inter_nic2|inter_ip|busi_nic1|busi_nic2|stp_nic1|stp_nic2|stp_ip|stc_nic1|stc_nic2|stc_ip|
|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|
|1|zw|11111|1.1.1.1|controller1|ens1|ens2|2.2.2.2|eno1|eno2|3.3.3.3|enp1|enp2|enq1|enq2|4.4.4.4|enr1|enr2|5.5.5.5|


## Usage
* python gen_rackstack_json.py prepare
* python gen_rackstack_json.py generate