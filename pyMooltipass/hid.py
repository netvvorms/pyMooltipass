#!/usr/bin/env python3
"""
pyMooltipass is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

pyMooltipass is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with pyMooltipass.  If not, see <http://www.gnu.org/licenses/>.

This file is part of pyMooltipass

This code is inspired by the python_comms on
https://github.com/limpkin/mooltipass
"""

from . import export

import usb
import platform
import logging
import array

LOGGER = logging.getLogger("hid_device")

@export
class DataBuffer(array.array):
    """ Class describing an HID data array """

    def __new__(cls, *args):
        return array.array.__new__(cls, "B", *args)

    def __lshift__(self, value):
        if isinstance(value, array.array):
            self.extend(value)
        elif isinstance(value, tuple):
            for val in value:
                self.append(val)
        else:
            self.append(value)

        return self

    def append(self, _data):
        array.array.append(self, _data)

    def extend(self, _data):
        array.array.extend(self, _data)

@export
class HIDDevice(object):
    """
    HID interface to send and receive data to an USB device
    """

    __hid_device = None
    __device_id = ""
    __cfg = None
    __interface = None

    """ Endpoints """
    __ep_in = None
    __ep_out = None

    __vendor_id = None
    __product_id = None

    def __init__(self, vendor_id, product_id):
        self.__vendor_id = vendor_id
        self.__product_id = product_id

    def __enter__(self):
        self.__hid_device = usb.core.find(idVendor=self.__vendor_id,
                                          idProduct=self.__product_id)

        if self.__hid_device is None:
            raise ValueError("Could not find the device {0}".format(self.__device_id))

        self.__device_id = "[{2}] {0}:{1}".format(hex(self.__hid_device.idVendor),
                                                  hex(self.__hid_device.idProduct),
                                                  self.__hid_device.product)

        LOGGER.info("Found device %#x:%#x (%s)",
                    self.__vendor_id,
                    self.__product_id,
                    self.__hid_device.product)

        # Different init codes depending on the platform
        if platform.system() == "Linux":
            # Need to do things differently
            try:
                self.__hid_device.detach_kernel_driver(0)
                self.__hid_device.reset()
            except usb.core.USBError as ex:
                pass # Probably already detached
        else:
            # Set the active configuration. With no arguments, the first
            # configuration will be the active one
            try:
                self.__hid_device.set_configuration()
            except usb.core.USBError as ex:
                raise IOError("Cannot set configuration on device: {0}".format(ex)) from ex

        self.__cfg = self.__hid_device.get_active_configuration()
        self.__interface = self.__cfg[(0, 0)]

        if not self.__interface.bInterfaceClass == 3:
            LOGGER.warning("Interface %d of device %s " \
                           "is not a HID",
                           self.__interface.bInterfaceNumber,
                           self.__device_id)

            raise ValueError("Interface {0} of device {1}) " \
                             "is not a HID".format(self.__interface.bInterfaceNumber,
                                                   self.__device_id))

        # Match the first OUT endpoint
        self.__ep_out = usb.util.find_descriptor(self.__interface,
                                                 custom_match=lambda e: \
                                                 usb.util.endpoint_direction(e.bEndpointAddress) \
                                                 == usb.util.ENDPOINT_OUT)

        if self.__ep_out is None:
            LOGGER.warning("Could not find the OUTPUT endpoint %s",
                           self.__device_id)
            raise ValueError("Could not find the OUTPUT endpoint {0}".format(self.__device_id))

        LOGGER.info("Sucesfully opened output endpoint %#x", self.__ep_out.bEndpointAddress)

        # Match the first IN endpoint
        self.__ep_in = usb.util.find_descriptor(self.__interface,
                                                custom_match=lambda e: \
                                                usb.util.endpoint_direction(e.bEndpointAddress) \
                                                == usb.util.ENDPOINT_IN)

        if self.__ep_in is None:
            LOGGER.warning("Could not find the INPUT endpoint %s",
                           self.__device_id)
            raise ValueError("Could not find the INPUT endpoint {0}".format(self.__device_id))

        LOGGER.info("Sucesfully opened input endpoint %#x", self.__ep_in.bEndpointAddress)
        LOGGER.info("Sucesfully connected to device %s", self.__device_id)

        return self


    def read(self, timeout=15000, **kwargs):
        """receive data from the device"""
        _size = kwargs.pop('size', self.__ep_in.wMaxPacketSize)
        LOGGER.debug("Reading %d data from device %s [timeout: %s]",
                     _size,
                     self.__device_id,
                     timeout)

        try:
            _data = self.__ep_in.read(_size, timeout=timeout)
            LOGGER.debug("Read data [%s] from device %s",
                         ", ".join((hex(d) for d in _data)),
                         self.__device_id)
            return _data
        except usb.core.USBError as ex:
            LOGGER.warning("Timedout - no data read from device %s",
                           self.__device_id)
            raise TimeoutError("Read data timedout!") from ex


    def write(self, _data):
        """send data to the device"""
        LOGGER.debug("Writing data [%s] to device %s",
                     ", ".join((hex(d) for d in _data)),
                     self.__device_id)
        try:
            self.__ep_out.write(_data)
        except usb.core.USBError:
            LOGGER.error("Could not write data to device %s",
                         self.__device_id)

    def __exit__(self, *arg):
        if self.__hid_device is not None:
            self.__hid_device.reset()
            LOGGER.info("Sucesfully disconnected from device %s",
                        self.__device_id)

            self.__hid_device = None



if __name__ == '__main__':
    import time
    import random

    logging.basicConfig(level=logging.DEBUG)
    USB_VID = 0x16D0
    USB_PID = 0x09A0

    CMD_INDEX = 0x01
    DATA_INDEX = 0x02

    CMD_PING = 0xA1

    # This test suppose that you have a mooltipass...

    with HIDDevice(USB_VID, USB_PID) as hid_device:
        # prepare ping packet
        byte1 = random.randint(0, 255)
        byte2 = random.randint(0, 255)
        ping_packet = array.array('B')
        ping_packet.append(2)
        ping_packet.append(CMD_PING)
        ping_packet.append(byte1)
        ping_packet.append(byte2)

        print(hid_device)
        time.sleep(0.5)
        # try to send ping packet
        hid_device.write(ping_packet)
        retry_read = True
        while retry_read:
            try:
                # try to receive answer
                data = hid_device.read(timeout=2000)
                if (data is not None and
                    data[CMD_INDEX] == CMD_PING and
                    data[DATA_INDEX] == byte1 and
                    data[DATA_INDEX+1] == byte2):
                    retry_read = False
                    LOGGER.debug("Device replied to our ping message")
                else:
                    LOGGER.debug("Cleaning remaining input packets")
                time.sleep(.5)
            except usb.core.USBError as e:
                LOGGER.error(e)


