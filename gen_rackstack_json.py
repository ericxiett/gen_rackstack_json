import sys

import xlwt
from ironicclient import client

# Global configurations for ironic
IRONIC_ENDPOINT = 'http://127.0.0.1:6385/'
DEFAULT_IRONIC_API_VERSION = '1.11'

# Global variables for excel
EXCEL_FILE = 'env_info.xls'
VALID_FIELDS = ['index', 'region', 'uuid', 'sn', 'ipmi_addr', 'role', 'mgm_nic1',
             'mgm_nic2', 'mgm_ip', 'inter_nic1', 'inter_nic2', 'inter_ip',
             'busi_nic1', 'busi_nic2', 'stp_nic1', 'stp_nic2', 'stp_ip',
             'stc_nic1', 'stc_nic2', 'stc_ip', 'desc']

def print_helper():
    print("*" * 47)
    print("* Welcome to use this script to generate json *")
    print("*   - python gen_rackstack_json.py prepare    *")
    print("*   - python gen_rackstack_json.py generate   *")
    print("*" * 47)


def get_client():
    args = {'token': 'noauth',
            'endpoint': IRONIC_ENDPOINT}

    args['os_ironic_api_version'] = DEFAULT_IRONIC_API_VERSION
    args['max_retries'] = 3
    args['retry_interval'] = 1
    return client.Client(1, **args)


def prepare_info():

    # Get node info from ironic
    icl = get_client()
    node_list = icl.node.list()

    # Init workbook
    style0 = xlwt.easyxf('font: name Times New Roman,'
                         ' bold on', num_format_str='#,##0.00')
    wb = xlwt.Workbook()
    ws = wb.add_sheet('node info')
    # First line to store fields
    # index,region,sn,ipmi_addr,role,mgm_nic1,mgm_nic2,mgm_ip,inter_nic1,
    # inter_nic2,inter_ip,busi_nic1,busi_nic2,stp_nic1,stp_nic2,stp_ip,
    # stc_nic1,stc_nic2,stc_ip,desc,
    # desc: description, like 20 lcpu, 256GB mem, 2 disks, 8 nics
    for col in range(len(VALID_FIELDS)):
        ws.write(0, col, VALID_FIELDS[col], style0)
    # Write some info from ironic into excel
    row = 1
    for node in node_list:
        node_info = icl.node.get(node.uuid)
        sn = node_info.extra['serial_number']
        ipmi_addr = node_info.driver_info['ipmi_address']
        lcpu_num = node_info.extra['cpu_detailed']['count']
        mem_cap_gb = node_info.extra['mem_detailed']['physical_mb'] / 1024
        # TODO: has_carrier if True or not
        nic_num = len(node_info.extra['nic_detailed'])
        disk_num = len(node_info.extra['disk_detailed'])
        desc = str(lcpu_num) + ' lcpu, ' + str(mem_cap_gb) + 'GB mem, ' + \
            str(nic_num) + ' nics, ' + str(disk_num) + ' disks'
        ws.write(row, 0, row)
        ws.write(row, 2, node.uuid, style0)
        ws.write(row, 3, sn, style0)
        ws.write(row, 4, ipmi_addr, style0)
        ws.write(row, 20, desc, style0)
        row += 1

    wb.save(EXCEL_FILE)


def main():
    if len(sys.argv) < 2:
        print_helper()
        exit(0)

    if sys.argv[1] not in ['prepare', 'generate']:
        print("Please input correct action, value: prepare, generate.")
        exit(1)

    if sys.argv[1] == 'prepare':
        prepare_info()
        exit(0)


if __name__ == '__main__':
    sys.exit(main())
