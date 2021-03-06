"""Menus for Magic DXLink Configurator"""

import wx
import csv
from scripts import mdc_gui, datastore
from netaddr import IPRange, IPNetwork
from pydispatch import dispatcher


class PreferencesConfig(mdc_gui.Preferences):
    """Sets the preferences """

    def __init__(self, parent):
        mdc_gui.Preferences.__init__(self, parent)

        self.parent = parent
        self.prefs = self.parent.preferences
        self.set_values()

    def set_values(self):
        """Set the field values"""
        self.master_address_txt.SetValue(self.prefs.master_address)
        self.device_number_txt.SetValue(str(self.prefs.device_number))
        self.subnet_filter_txt.SetValue(self.prefs.subnet_filter)
        self.subnet_filter_txt.Enable(self.prefs.subnet_filter_enable)
        self.subnet_filter_chk.SetValue(self.prefs.subnet_filter_enable)
        getattr(self, self.prefs.connection_type.lower() + '_chk').SetValue(True)

        self.sounds_chk.SetValue(int(self.prefs.play_sounds))
        self.funny_sounds_chk.SetValue(int(self.prefs.randomize_sounds))
        self.check_for_updates_chk.SetValue(int(self.prefs.check_for_updates))

        self.master_user_txt.SetValue(self.prefs.master_user)
        self.master_password_txt.SetValue(self.prefs.get_password())

        for item in self.prefs.cols_selected:
            getattr(self, item.lower() + '_chk').SetValue(True)

    def on_ok(self, _):
        """When user clicks ok"""
        self.prefs.cols_selected = []
        columns = ['Time', 'Model', 'MAC', 'IP', 'Hostname', 'Serial', 'Firmware', 'Device', 'Static', 'Master', 'System', 'Status']
        for item in columns:
            if getattr(self, item.lower() + '_chk').GetValue():
                self.prefs.cols_selected.append(item)
        self.prefs.master_address = self.master_address_txt.GetValue()
        self.prefs.device_number = self.device_number_txt.GetValue()
        self.prefs.subnet_filter_enable = self.subnet_filter_chk.GetValue()
        if self.subnet_filter_chk.GetValue():
            try:
                IPNetwork(self.subnet_filter_txt.GetValue())
            except Exception as error:
                self.bad_subnet(error)
                return
            self.prefs.subnet_filter = self.subnet_filter_txt.GetValue()

        if self.tcp_chk.GetValue():
            self.prefs.connection_type = "TCP"
        if self.udp_chk.GetValue():
            self.prefs.connection_type = "UDP"
        if self.ndp_chk.GetValue():
            self.prefs.connection_type = "NDP"
        if self.auto_chk.GetValue():
            self.prefs.connection_type = "AUTO"

        self.prefs.play_sounds = self.sounds_chk.GetValue()
        self.prefs.randomize_sounds = self.funny_sounds_chk.GetValue()
        self.prefs.check_for_updates = self.check_for_updates_chk.GetValue()

        if self.master_user_txt.GetValue() != "":
            self.prefs.master_user = self.master_user_txt.GetValue()
        if self.master_password_txt.GetValue() != "":
            self.prefs.set_password(self.master_password_txt.GetValue())
   
        # self.parent.update_status_bar()
        # self.parent.select_columns()
        # self.parent.resize_frame()
        self.Destroy()

    def bad_subnet(self, error):
        """Dialog showing error"""
        dlg = wx.MessageDialog(parent=self,
                               message='The subnet you have entered is invalid. \n\n' +
                               str(error) + '\n' +
                               'CIDR example 192.168.71.0/24 or 192.168.71.0/255.255.255.0',
                               caption='Error saving subnet',
                               style=wx.OK)
        dlg.ShowModal()
        self.subnet_filter_chk.SetValue(False)
        self.subnet_filter_txt.Enable(False)

    def on_subnet_enable(self, event):
        """Enable or disable the subnet field"""
        self.subnet_filter_txt.Enable(self.subnet_filter_chk.GetValue())

    def on_cancel(self, _):
        """When user clicks cancel"""
        self.Destroy()


class DeviceConfig(mdc_gui.DeviceConfiguration):
    """Configures a device"""

    def __init__(self, parent, obj, device_num):
        mdc_gui.DeviceConfiguration.__init__(self, parent)

        self.parent = parent
        self.prefs = self.parent.preferences
        self.obj = obj
        self.ip_org = obj.ip_address
        self.device_num = device_num

        self.SetTitle("Device settings for %s %s"
                      % (obj.ip_address, obj.device))
        self.hostname = obj.hostname
        self.ip_address = obj.ip_address
        self.subnet = obj.subnet
        self.gateway = obj.gateway
        self.master = obj.master
        self.device = obj.device
        self.system = obj.system

        if self.hostname == '':
            self.hostname = 'hostname'
        if self.ip_address == '':
            self.ip_address = '0.0.0.0'
        if self.subnet == '':
            self.subnet = '255.255.255.0'
        if self.gateway == ' ':
            self.gateway = '0.0.0.0'
        if self.master == '' or self.master == 'not connected':
            if self.prefs.master_address == "127.0.0.1":
                self.master = ''
            else:
                self.master = str(self.prefs.master_address)

        if self.device == '' or obj.device == '0':
            self.device = str(device_num)

        if self.system == '':
            self.system = '0'

        self.hostname_txt.SetLabel(self.hostname)

        if obj.ip_type == 's':
            self.dhcp_chk.SetValue(False)
            self.static_chk.SetValue(True)
        else:
            self.dhcp_chk.SetValue(True)
            self.static_chk.SetValue(False)

        self.ip_address_txt.SetLabel(self.ip_address)
        self.subnet_txt.SetLabel(self.subnet)
        self.gateway_txt.SetLabel(self.gateway)
        self.master_txt.SetValue(self.master)
        self.device_txt.SetValue(self.device)
        self.master_number_txt.SetValue(self.system)
        if self.prefs.master_user != "":
            self.master_user_txt.SetValue(self.prefs.master_user)
        if self.prefs.get_password() != "":
            self.master_password_txt.SetValue(self.prefs.get_password())

        self.on_dhcp(None)  # call to update dhcp / static
        getattr(self, self.prefs.connection_type.lower() + '_chk').SetValue(True)
        self.on_connection_type(None)
        self.Fit()

    def on_connection_type(self, _):
        """Sets up for connection type"""
        if self.tcp_chk.GetValue() or self.udp_chk.GetValue:
            self.master_number_txt.Enable(False)
            self.master_txt.Enable(True)
        if self.ndp_chk.GetValue():
            self.master_number_txt.Enable(False)
            self.master_txt.Enable(False)
        if self.auto_chk.GetValue():
            self.master_number_txt.Enable(True)
            self.master_txt.Enable(False)

    def on_dhcp(self, _):
        """Sets DHCP mode on or off and enables the DHCP options"""

        if self.dhcp_chk.GetValue() is True:
            self.ip_address_txt.Enable(False)
            self.subnet_txt.Enable(False)
            self.gateway_txt.Enable(False)

        else:
            self.ip_address_txt.Enable(True)
            self.subnet_txt.Enable(True)
            self.gateway_txt.Enable(True)

    def on_cancel(self, _):
        """Canel and close"""
        selected_items = self.parent.main_list.GetSelectedObjects()
        selected_items.remove(self.obj)
        self.parent.configure_list.remove(self.obj)
        self.parent.main_list.SelectObjects(selected_items,
                                            deselectOthers=True)
        self.parent.cancel = True
        self.Destroy()

    def on_abort(self, _):
        """Quits processing the list of selected items"""
        self.parent.abort = True
        self.parent.main_list.DeselectAll()
        self.Destroy()

    def on_set(self, _):
        """Sends the setting to the device"""
        if self.dhcp_chk.GetValue() is True:
            setdhcp = True
        else:
            setdhcp = False

        info = ['set_device_config',
                self.obj,
                self.prefs.telnet_timeout,
                setdhcp,
                str(self.hostname_txt.GetValue()),
                str(self.ip_org),
                str(self.ip_address_txt.GetValue()),
                str(self.subnet_txt.GetValue()),
                str(self.gateway_txt.GetValue()),
                str(self.get_type()),
                str(self.master_number_txt.GetValue()),
                str(self.master_txt.GetValue()),
                str(self.device_txt.GetValue()),
                str(self.master_user_txt.GetValue()),
                str(self.master_password_txt.GetValue())]
        if self.device_txt.GetValue() != str(self.device_num):
            self.parent.dev_inc_num = int(self.device_txt.GetValue())
        self.parent.telnet_job_queue.put(info)
        self.Destroy()

    def get_type(self):
        """Gets the connection type"""
        if self.tcp_chk.GetValue():
            return "TCP"
        if self.udp_chk.GetValue():
            return "UDP"
        if self.ndp_chk.GetValue():
            return "NDP"
        if self.auto_chk.GetValue():
            return "AUTO"


class IpListGen(mdc_gui.GenerateIP):
    """Generates a list of IP's"""

    def __init__(self, parent):
        mdc_gui.GenerateIP.__init__(self, parent)

        self.parent = parent
        self.prefs = self.parent.preferences

        self.start_txt.SetLabel(self.prefs.master_address)
        self.finish_txt.SetLabel(self.prefs.master_address)

        self.data = []

        self.SetTitle("Generate IP list")

    def on_action(self, event):
        """Testing event"""
        if not self.gen_list():
            return
        if self.check_size():
            if event.GetEventObject().GetLabel() == "Add to List":
                self.on_add()
            elif event.GetEventObject().GetLabel() == "Replace List":
                self.on_replace()
        else:
            return

    def on_replace(self):
        """Replaces list with generated list"""
        if not self.gen_list():
            return
        self.parent.main_list.DeleteAllItems()
        self.on_add()

    def on_add(self):
        """Adds to the bottom of the list"""
        if not self.gen_list():
            return
        for item in self.data:
            obj = datastore.DXLinkUnit()
            obj.ip_address = item
            self.parent.main_list.AddObject(obj)
        self.parent.save_main_list()
        self.Destroy()

    def on_save(self, _):
        """Saves the ip list to a file"""
        if not self.gen_list():
            return
        if self.check_size():
            save_file_dialog = wx.FileDialog(self, message="Save IP list",
                                             defaultDir=self.parent.storage_path,
                                             defaultFile="generatediplist.csv",
                                             wildcard="CSV files (*.csv)|*.csv",
                                             style=wx.FD_SAVE)
            if save_file_dialog.ShowModal() == wx.ID_OK:

                path = save_file_dialog.GetPath()
                with open(path, 'w', newline='') as ip_list_file:
                    writer_csv = csv.writer(ip_list_file)
                    for item in self.data:
                        writer_csv.writerow([item])
                    self.Destroy()
            else:
                self.Destroy()
        else:
            return

    def gen_list(self):
        """Generates the IP list"""
        self.data = []
        try:
            ip_range = IPRange(self.start_txt.GetValue(),
                               self.finish_txt.GetValue())
        except Exception as error:
            print('error: ', error)
            dlg = wx.MessageDialog(parent=self,
                                   message=f'The IP address entered is invalid\r{error}',
                                   caption='Invalid IP',
                                   style=wx.OK)
            dlg.ShowModal()
            return False
        for address in list(ip_range):
            self.data.append(str(address))
        return True

    def check_size(self):
        """Warning abou the size of the range"""
        if len(self.data) > 500:
            dlg = wx.MessageDialog(
                parent=self,
                message='Are you sure? \n\nThis will create ' +
                        str(len(self.data)) +
                        ' IP\'s. Creating more than 1000 IP\'s could slow' +
                        ' or even crash the program',
                        caption='Creating IP list',
                        style=wx.OK | wx.CANCEL)
            if dlg.ShowModal() == wx.ID_OK:
                return True
            else:
                return False
        else:
            return True


class TestDia(mdc_gui.TestDialog):
    def __init__(self, parent):
        mdc_gui.TestDialog.__init__(self, parent)

        self.parent = parent

    def on_ok(self, event):
        """send fake DHCP"""
        ip = self.fake_ip_txt.GetValue()
        hostname = 'Fake DHCP host'
        mac_address = self.mac_address_txt.GetValue()
        dispatcher.send(signal="Incoming Packet",
                        sender=(hostname, mac_address, ip))
