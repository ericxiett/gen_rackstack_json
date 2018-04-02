import json
import sys

import os

import xlrd
import xlwt
from ironicclient import client

# Global configurations for ironic
IRONIC_ENDPOINT = 'http://127.0.0.1:6385/'
DEFAULT_IRONIC_API_VERSION = '1.11'

# Global variables for excel
EXCEL_FILE = 'env_info.xls'
VALID_FIELDS = ['index', 'region', 'uuid', 'sn', 'ipmi_addr', 'role',
                'mgm_nic1','mgm_nic2', 'mgm_ip', 'mgm_netmask', 'mgm_gtw', 'mgm_vid',
                'inter_nic1', 'inter_nic2', 'inter_ip', 'inter_netmask', 'inter_gtw', 'inter_vid',
                'busi_nic1', 'busi_nic2', 'busi_vid',
                'stp_nic1', 'stp_nic2', 'stp_ip', 'stp_netmask', 'stp_vid',
                'stc_nic1', 'stc_nic2', 'stc_ip', 'stc_netmask', 'stc_vid',
                'desc', 'hostname', 'openstack_version',
                'ntp_server', 'intervip', 'managevip']

# Global variables for env
ENV_OS_VERSION = 'Mitaka'
NET_TYPE = 'vxlan,vlan'
NET_MODE = 'self'

COMS_CONTROLLER = 'db,rabbitmq,keystone,glance-api,glance-registry,' \
                  'nova-api,nova-conductor,nova-consoleauth,' \
                  'nova-novncproxy,nova-scheduler,neutron-server,' \
                  'cinder-api,cinder-scheduler,cinder-volume'
COMS_NETWORK = 'neutron-metadata-agent,neutron-dhcp-agent,neutron-l3-agent,' \
               'neutron-openvswitch-agent'
COMS_COMPUTE = 'nova-compute,neutron-openvswitch-agent'
COMS_STG_MON = 'ceph-mon'
COMS_STG_OSD = 'ceph-osd'
COMS = {
    'controller': COMS_CONTROLLER,
    'network': COMS_NETWORK,
    'compute': COMS_COMPUTE,
    'ceph-mon': COMS_STG_MON,
    'ceph-osd': COMS_STG_OSD
}

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


def _parse_nic_info(node_info):
    nics_info = ''
    nic_detailed = node_info.extra['nic_detailed']
    index = 1
    for nic in nic_detailed:
        if nic['has_carrier'] != True:
            continue

        print('nic raw: ', nic)
        nic_info = {}
        nic_info['name'] = nic['name']
        nic_info['mac'] = nic['mac_address']
        formated_lldp = nic['lldpctl']
        if "\\\n" in nic['lldpctl']:
            formated_lldp = nic['lldpctl'].replace("\\\n", "")
        lldpctl_json = json.loads(formated_lldp)
        if 'interface' in lldpctl_json['lldp'].keys():
            nic_info['vlanid'] = \
                lldpctl_json['lldp']['interface'][nic['name']]['vlan']['vlan-id']
        if 'vlanid' in nic_info.keys():
            print('index: ', index, ' name: ', nic_info['name'], ' mac: ',
                  nic['mac_address'], ' vlanid: ', nic_info['vlanid'])
            nic_record = nic_info['name'] + '(' + nic_info['vlanid'] + ')'
        else:
            print('index: ', index, ' name: ', nic_info['name'], ' mac: ',
                  nic['mac_address'])
            nic_record = nic_info['name']
        nics_info +=  nic_record

    return nics_info


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
    # index,region,uuid,sn,ipmi_addr,role,mgm_nic1,mgm_nic2,mgm_ip,inter_nic1,
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
        # nic_num = len(node_info.extra['nic_detailed'])
        # Get details info of nics for bond
        nic_info = _parse_nic_info(node_info)
        disk_num = len(node_info.extra['disk_detailed'])
        desc = str(lcpu_num) + ' lcpu, ' + str(mem_cap_gb) + 'GB mem, ' + \
            str(disk_num) + ' disks, ' + 'nics: ' + str(nic_info)
        # 'index' uses row value
        ws.write(row, VALID_FIELDS.index('index'), row)
        ws.write(row, VALID_FIELDS.index('uuid'), node.uuid, style0)
        ws.write(row, VALID_FIELDS.index('sn'), sn, style0)
        ws.write(row, VALID_FIELDS.index('ipmi_addr'), ipmi_addr, style0)
        ws.write(row, VALID_FIELDS.index('desc'), desc, style0)
        row += 1

    wb.save(EXCEL_FILE)


def generate_json():
    # If excel existed
    excel_file = os.getcwd() + '/' + EXCEL_FILE
    if not os.path.exists(excel_file):
        print('Please execute prepare phase!')
        exit(1)

    book = xlrd.open_workbook(excel_file)
    sh = book.sheet_by_name('node info')
    # Validate fields of row 0
    for col in range(len(VALID_FIELDS)):
        if sh.cell_value(0, col) != VALID_FIELDS[col]:
            print("Invalid field: ", sh.cell_value(0, col),
                  ", should be ", VALID_FIELDS[col])
            exit(1)

    # Maybe multiple environments, like env1(zw), env2(hl)
    env_list = []
    for row in range(1, sh.nrows):
        env = sh.cell_value(row, 1)
        if env not in env_list:
            env_list.append(env)
    print('Want to build envs: ', env_list)

    # Get info of nodes
    index = 1
    for env in env_list:
        # Build heads
        env_info = {}
        env_info['environ'] = {}
        env_info['environ']['bondmode'] = '1'
        env_info['environ']['openstack_version'] = ENV_OS_VERSION
        env_info['environ']['nettype'] = NET_TYPE
        env_info['environ']['netmode'] = NET_MODE
        env_info['environ']['environname'] = env
        env_info['environ']['environid'] = str(index)
        env_info['environ']['haenabled'] = False

        # Node detail info
        con_num = 0
        env_info['environ']['nodes'] = []
        for row in range(1, sh.nrows):
            if sh.cell_value(row, VALID_FIELDS.index('region')) != env:
                continue
            node = {}
            role = sh.cell_value(row, VALID_FIELDS.index('role'))
            print('role: ', role)
            # Get number of controller nodes
            if 'controller' in role:
                con_num += 1

            component = ''
            for r in role.split(','):
                for el in COMS[r].split(','):
                    if el not in component:
                        component = component + ',' + el
            node['component'] = component
            if ('ceph-mon' or 'ceph-osd') in role:
                role = 'storage'
            node['type'] = role
            node['ntp_server_ip'] = \
                sh.cell_value(row, VALID_FIELDS.index('ntp_server'))
            node['serverid'] = node['uuid'] = \
                sh.cell_value(row, VALID_FIELDS.index('uuid'))
            node['serialnum'] = sh.cell_value(row, VALID_FIELDS.index('sn'))
            node['hostname'] = \
                sh.cell_value(row, VALID_FIELDS.index('hostname'))
            node['intervip'] = \
                sh.cell_value(row, VALID_FIELDS.index('intervip'))
            node['managevip'] = \
                sh.cell_value(row, VALID_FIELDS.index('managevip'))
            node['nicbond'] = []
            # Management network
            mgm = {}
            mgm['netflag'] = 'admin'
            mgm['bondname'] = 'bondadmin'
            mgm['nic1'] = sh.cell_value(row, VALID_FIELDS.index('mgm_nic1'))
            mgm['nic2'] = sh.cell_value(row, VALID_FIELDS.index('mgm_nic2'))
            if mgm['nic1'] != '' and mgm['nic2'] != '':
                env_info['environ']['bondenabled'] = True
            else:
                env_info['environ']['bondenabled'] = False
            mgm['ip'] = sh.cell_value(row, VALID_FIELDS.index('mgm_ip'))
            mgm['netmask'] = \
                sh.cell_value(row, VALID_FIELDS.index('mgm_netmask'))
            mgm['gateway'] = sh.cell_value(row, VALID_FIELDS.index('mgm_gtw'))
            mgm['vlanid'] = \
                str(sh.cell_value(row, VALID_FIELDS.index('mgm_vid'))).split('.')[0]
            node['nicbond'].append(mgm)
            # Business network
            busi = {}
            busi['netflag'] = 'business'
            busi['bondname'] = 'bondbusiness'
            busi['nic1'] = sh.cell_value(row, VALID_FIELDS.index('busi_nic1'))
            busi['nic2'] = sh.cell_value(row, VALID_FIELDS.index('busi_nic2'))
            busi['ip'] = ''
            busi['netmask'] = ''
            busi['gateway'] = ''
            busi['vlanid'] = \
                str(sh.cell_value(row, VALID_FIELDS.index('busi_vid'))).split('.')[0]
            node['nicbond'].append(busi)
            # internaladmin network
            inter = {}
            inter['netflag'] = 'internaladmin'
            inter['bondname'] = 'bondinternal'
            inter['nic1'] = sh.cell_value(row, VALID_FIELDS.index('inter_nic1'))
            inter['nic2'] = sh.cell_value(row, VALID_FIELDS.index('inter_nic2'))
            inter['ip'] = sh.cell_value(row, VALID_FIELDS.index('inter_ip'))
            inter['netmask'] = \
                sh.cell_value(row, VALID_FIELDS.index('inter_netmask'))
            inter['gateway'] = sh.cell_value(row, VALID_FIELDS.index('inter_gtw'))
            inter['vlanid'] = \
                str(sh.cell_value(row, VALID_FIELDS.index('inter_vid'))).split('.')[0]
            node['nicbond'].append(inter)
            # storage public network
            stp = {}
            stp['netflag'] = 'storage'
            stp['bondname'] = 'bondstorage'
            stp['nic1'] = sh.cell_value(row, VALID_FIELDS.index('stp_nic1'))
            stp['nic2'] = sh.cell_value(row, VALID_FIELDS.index('stp_nic2'))
            stp['ip'] = sh.cell_value(row, VALID_FIELDS.index('stp_ip'))
            stp['netmask'] = \
                sh.cell_value(row, VALID_FIELDS.index('stp_netmask'))
            stp['gateway'] = ''
            stp['vlanid'] = \
                str(sh.cell_value(row, VALID_FIELDS.index('stp_vid'))).split('.')[0]
            node['nicbond'].append(stp)
            # storage cluster network
            stc = {}
            stc['netflag'] = 'stginter'
            stc['bondname'] = 'bondstginter'
            stc['nic1'] = sh.cell_value(row, VALID_FIELDS.index('stc_nic1'))
            stc['nic2'] = sh.cell_value(row, VALID_FIELDS.index('stc_nic2'))
            stc['ip'] = sh.cell_value(row, VALID_FIELDS.index('stc_ip'))
            stc['netmask'] = \
                sh.cell_value(row, VALID_FIELDS.index('stc_netmask'))
            stc['gateway'] = ''
            stc['vlanid'] = \
                str(sh.cell_value(row, VALID_FIELDS.index('stc_vid'))).split('.')[0]
            node['nicbond'].append(stc)

            env_info['environ']['nodes'].append(node)

        if con_num == 3:
            env_info['environ']['haenabled'] = True

        json_file = 'body_env_' + env + '_' + str(index) + '.json'
        with open(json_file, 'w+') as f:
            f.write(json.dumps(env_info, sort_keys=True, indent=4, separators=(',', ': ')))

        index += 1


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

    if sys.argv[1] == 'generate':
        generate_json()
        exit(0)


if __name__ == '__main__':
    sys.exit(main())
