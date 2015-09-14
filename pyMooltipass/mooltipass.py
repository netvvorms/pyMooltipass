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

from .hid import HIDDEvice, DataBuffer

import logging
import enum
import time
import random
from contextlib import contextmanager
import usb

LOGGER = logging.getLogger("mooltipass")

class MooltipassCmd(enum.IntEnum):
    """Enumerated types for the Mooltipass commands"""
    EXPORT_FLASH_START = 0x8A
    EXPORT_FLASH = 0x8B
    EXPORT_FLASH_END = 0x8C
    IMPORT_FLASH_BEGIN = 0x8D
    IMPORT_FLASH = 0x8E
    IMPORT_FLASH_END = 0x8F
    EXPORT_EEPROM_START = 0x90
    EXPORT_EEPROM = 0x91
    EXPORT_EEPROM_END = 0x92
    IMPORT_EEPROM_BEGIN = 0x93
    IMPORT_EEPROM = 0x94
    IMPORT_EEPROM_END = 0x95
    ERASE_EEPROM = 0x96
    ERASE_FLASH = 0x97
    ERASE_SMC = 0x98
    DRAW_BITMAP = 0x99
    SET_FONT = 0x9A
    USB_KEYBOARD_PRESS = 0x9B
    STACK_FREE = 0x9C
    CLONE_SMARTCARD = 0x9D
    DEBUG = 0xA0
    PING = 0xA1
    VERSION = 0xA2
    CONTEXT = 0xA3
    GET_LOGIN = 0xA4
    GET_PASSWORD = 0xA5
    SET_LOGIN = 0xA6
    SET_PASSWORD = 0xA7
    CHECK_PASSWORD = 0xA8
    ADD_CONTEXT = 0xA9
    SET_BOOTLOADER_PWD = 0xAA
    JUMP_TO_BOOTLOADER = 0xAB
    GET_RANDOM_NUMBER = 0xAC
    START_MEMORYMGMT = 0xAD
    IMPORT_MEDIA_START = 0xAE
    IMPORT_MEDIA = 0xAF
    IMPORT_MEDIA_END = 0xB0
    SET_MOOLTIPASS_PARM = 0xB1
    GET_MOOLTIPASS_PARM = 0xB2
    RESET_CARD = 0xB3
    READ_CARD_LOGIN = 0xB4
    READ_CARD_PASS = 0xB5
    SET_CARD_LOGIN = 0xB6
    SET_CARD_PASS = 0xB7
    ADD_UNKNOWN_CARD = 0xB8
    MOOLTIPASS_STATUS = 0xB9
    FUNCTIONAL_TEST_RES = 0xBA
    SET_DATE = 0xBB
    SET_UID = 0xBC
    GET_UID = 0xBD
    SET_DATA_SERVICE = 0xBE
    ADD_DATA_SERVICE = 0xBF
    WRITE_32B_IN_DN = 0xC0
    READ_32B_IN_DN = 0xC1
    GET_CUR_CARD_CPZ = 0xC2
    CANCEL_REQUEST = 0xC3
    PLEASE_RETRY = 0xC4
    READ_FLASH_NODE = 0xC5
    WRITE_FLASH_NODE = 0xC6
    GET_FAVORITE = 0xC7
    SET_FAVORITE = 0xC8
    GET_STARTING_PARENT = 0xC9
    SET_STARTING_PARENT = 0xCA
    GET_CTRVALUE = 0xCB
    SET_CTRVALUE = 0xCC
    ADD_CARD_CPZ_CTR = 0xCD
    GET_CARD_CPZ_CTR = 0xCE
    CARD_CPZ_CTR_PACKET = 0xCF
    GET_FREE_SLOTS_ADDR = 0xD0
    GET_DN_START_PARENT = 0xD1
    SET_DN_START_PARENT = 0xD2
    END_MEMORYMGMT = 0xD3

class MooltipassStatus(enum.IntEnum):
    """Enumerated types for the Mooltipass status"""
    NO_CARDS = 0
    LOCKED = 1
    UNLOCKING = 3
    UNLOCKED = 5
    INVALID_SMARTCARD = 9

@export
class Mooltipass(HIDDevice):
    """
    Mooltipass class to interact with the mooltipass
    the Mooltipass class is a context manager
    """
    USB_VID = 0x16D0
    USB_PID = 0x09A0

    SUCCESS = 0x01

    LEN_INDEX = 0x00
    CMD_INDEX = 0x01
    DATA_INDEX = 0x02
    PREV_ADDRESS_INDEX = 0x02
    NEXT_ADDRESS_INDEX = 0x04
    NEXT_CHILD_INDEX = 0x06
    SERVICE_INDEX = 0x08
    DESC_INDEX = 0x06
    LOGIN_INDEX = 37
    NODE_SIZE = 132


    BITMAP_ID_OFFSET = 128
    KEYBD_ID_OFFSET = BITMAP_ID_OFFSET + 18

    PARAMETERS = {'keyboard_layout': 1,
                  'user_inter_timeout': 2,
                  'lock_timeout_enable': 3,
                  'lock_timeout': 4,
                  'touch_di': 5,
                  'touch_wheel_os_old': 6,
                  'touch_prox_os': 7,
                  'offline_mode': 8,
                  'screensaver': 9,
                  'touch_charge_time': 10,
                  'touch_wheel_os0': 11,
                  'touch_wheel_os1': 12,
                  'touch_wheel_os2': 13,
                  'flash_screen': 14,
                  'user_req_cancel': 15,
                  'tutorial_bool': 16,
                  'screen_saver_speed': 17}

    KEYBOARD_LAYOUT = {'EN_US': 0,
                       'FR_FR': 1,
                       'ES_ES': 2,
                       'DE_DE': 3,
                       'ES_AR': 4,
                       'EN_AU': 5,
                       'FR_BE': 6,
                       'PO_BR': 7,
                       'EN_CA': 8,
                       'CZ_CZ': 9,
                       'DA_DK': 10,
                       'FI_FI': 11,
                       'HU_HU': 12,
                       'IS_IS': 13,
                       'IT_IT': 14,
                       'NL_NL': 15,
                       'NO_NO': 16,
                       'PO_PO': 17,
                       'RO_RO': 18,
                       'SL_SL': 19,
                       'FRDE_CH': 20,
                       'EN_UK': 21}

    STATUS = {0: {'status': MooltipassStatus.NO_CARDS, 'text': "no smartcard"},
              1: {'status': MooltipassStatus.LOCKED, 'text': "locked"},
              3: {'status': MooltipassStatus.UNLOCKING, 'text': "unlocking"},
              5: {'status': MooltipassStatus.UNLOCKED, 'text': "unlocked"},
              9: {'status': MooltipassStatus.INVALID_SMARTCARD, 'text': "unknown smartcard"}}

    def __init__(self):
        HIDDevice.__init__(self, self.USB_VID, self.USB_PID)

    def __enter__(self):
        HIDDevice.__enter__(self)
        time.sleep(0.5)
        if not self._ping():
            LOGGER.error("Mooltiass not initialized")
            raise IOError("Could not connect to the Mooltipass")

        _res = self._send_command(MooltipassCmd.VERSION)

        LOGGER.info("Mooltipass v%d initialized", _res[0])
        return self

    def _ping(self):
        """pings the Mooltipass"""
        # prepare ping packet
        _data = DataBuffer()
        _data << random.randint(0, 255) << random.randint(0, 255)

        # try to send ping packet
        try:
            _res = self._send_command(MooltipassCmd.PING, _data, timeout=2000)
        except usb.core.USBError as e:
            LOGGER.error(e)
        except InterruptedError:
            self.wait_status_unlocked()
            _res = self._send_command(MooltipassCmd.PING, _data, timeout=2000)

        _retries = 0
        _max_reties = 3
        while  ((_res is None) or
                not (_res[0] == _data[0] and
                     _res[1] == _data[1])):
            LOGGER.warning("Mooltipass did not answer to the ping request yet")
            if  _retries > _max_reties:
                LOGGER.error("Mooltipass did not answer to the ping request!")
                return False
            time.sleep(0.2)
            try:
                _res = self._read_data(timeout = 2000)
            except TimeoutError:
                _res = None

            _retries += 1

        LOGGER.debug("Device replied to our ping message")
        return True


    def _send_command(self, command, *arg, **kwargs):
        _data = DataBuffer()
        _data_val = DataBuffer()
        for val in arg:
            _data_val << val

        _data << len(_data_val)
        _data << command
        _data << _data_val

        self.write(_data)
        return self._read_data(**kwargs)

    def _read_data(self, **kwargs):
        _timeout = kwargs.pop('timeout', 1500)
        _res = self.read(timeout=_timeout)

        _beginning = self.DATA_INDEX
        if kwargs.pop('full_packet', False):
            _beginning = self.CMD_INDEX

        if kwargs.pop('retry_on_locked', False):
            while _res[self.CMD_INDEX] == MooltipassCmd.MOOLTIPASS_STATUS \
                  and _res[self.DATA_INDEX] == MooltipassStatus.UNLOCKING:
                try:
                    _res = self.read(timeout=_timeout)
                except TimeoutError:
                    time.sleep(2)
        else:
            if _res[self.CMD_INDEX] == MooltipassCmd.MOOLTIPASS_STATUS \
               and _res[self.DATA_INDEX] == MooltipassStatus.UNLOCKING:
                raise InterruptedError("Mooltipass not ready")
        return _res[_beginning:self.DATA_INDEX+_res[0]]


    def _set_parameter(self, param, value):
        _data = DataBuffer()
        _data << self.PARAMETERS[param]
        _data << value

        _res = self._send_command(MooltipassCmd.SET_MOOLTIPASS_PARM, _data)

        print (_res)

        if _res[0] == self.SUCCESS:
            LOGGER.info("Parameter set %s to (%#x).", param, value)
        else:
            LOGGER.error("Couldn't change parameter (%s)", param)
            raise ValueError("Couldn't change parameter {0}".format(hex(param)))


    def _get_parameter(self, param):
        _data = DataBuffer()
        _data << self.PARAMETERS[param]
        _res = self._send_command(MooltipassCmd.GET_MOOLTIPASS_PARM, _data)
        LOGGER.info("Parameter %s is set to [%s].",
                    param,
                    ', '.join((str(v) for v in _res)))
        return _res

    @contextmanager
    def _data_management_mode(self):
        """ Context to enter memory management mode"""
        _success = False
        try:
            self.wait_status_unlocked()
            LOGGER.info("Trying to enter memory management mode")

            logging.disable(logging.DEBUG)
            while not _success:
                try:
                    _res = self._send_command(MooltipassCmd.START_MEMORYMGMT,
                                              timeout=2000,
                                              retry_on_locked=True)
                    if not _res[0] == self.SUCCESS:
                        _success = None
                        raise InterruptedError("User refused management mode")

                    _success = True
                except TimeoutError:
                    time.sleep(1)

            logging.disable(logging.NOTSET)
            LOGGER.info('Entered memory management mode')

            yield
        finally:
            logging.disable(logging.NOTSET)
            LOGGER.info('Quit memory management mode')
            if not _success is None:
                _res = self._send_command(MooltipassCmd.END_MEMORYMGMT)

    def wait_status_unlocked(self):
        """wait for the Mooltipass to be unlocked"""
        _res = [self.get_status()['status']]
        LOGGER.info('Waiting Mooltipass to be unlocked')
        while not _res[0] == MooltipassStatus.UNLOCKED:
            try:
                _res = self._send_command(MooltipassCmd.MOOLTIPASS_STATUS)
            except TimeoutError:
                time.sleep(1)
            except InterruptedError:
                time.sleep(1)
        LOGGER.info('Mooltipass unlocked')

    def get_status(self):
        """Get the current status"""
        try:
            _res = self._send_command(MooltipassCmd.MOOLTIPASS_STATUS)
        except InterruptedError:
            _res = [MooltipassStatus.UNLOCKING]
        return self.STATUS[_res[0]]

    def select_keyboard_layout(self, layout):
        """activate a new layout on the Mooltipass"""
        self._set_parameter('keyboard_layout',
                            self.KEYBD_ID_OFFSET + self.KEYBOARD_LAYOUT[layout])

    def get_keyboard_layout(self):
        """Get the keyboard layout currently active"""
        _res = self._get_parameter('keyboard_layout')
        _lay_val = _res[0] - self.KEYBD_ID_OFFSET
        for _key, _val in self.KEYBOARD_LAYOUT.items():
            if _val == _lay_val:
                return _key
        return None

    def get_favorites_list(self):
        """Get the list of favorites stored in the Mooltipass as a dict()"""
        _favorite = {}

        with self._data_management_mode():
            for _fav_count in range(14):
                _fav_arg = DataBuffer()
                _fav_arg << _fav_count

                # request favorite
                _fav_data = self._send_command(MooltipassCmd.GET_FAVORITE, _fav_arg)

                # check if it is defined
                LOGGER.info('Getting favorites list')

                if not (_fav_data[0] == 0 and _fav_data[1] == 0):
                    # read parent node
                    _parent_data = self._send_command(MooltipassCmd.READ_FLASH_NODE, _fav_data[0:2])

                    # read it
                    _parent_data.extend(self._read_data())
                    _parent_data.extend(self._read_data())

                    _context = "".join((chr(c) \
                                        for c in _parent_data[self.SERVICE_INDEX:]))
                    _context = _context.split('\x00')[0]

                    # read child node
                    _child_data = self._send_command(MooltipassCmd.READ_FLASH_NODE,
                                                     _fav_data[2:4])
                    # read child info
                    _child_data.extend(self._read_data())
                    _child_data.extend(self._read_data())

                    _login = "".join((chr(c) \
                                      for c in _child_data[self.LOGIN_INDEX:]))
                    _login = _login.split('\x00')[0]
                    LOGGER.debug(' - slot %d: context "%s" - login "%s"',
                                 _fav_count, _context, _login)

                    _favorite[_fav_count] = {'context': _context, 'login': _login}
                else:
                    LOGGER.debug(' - slot %d: empty', _fav_count)

        return _favorite


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    with Mooltipass() as mltp:
        _layout = mltp.get_keyboard_layout()
        print("Layout {0}".format(_layout))

        #mltp.select_keyboard_layout('FRDE_CH')
        #print("Layout {0}".format(mltp.get_keyboard_layout()))
        #mltp.select_keyboard_layout(_layout)

        # print(mltp.get_favorites_list())

#  LocalWords:  Mooltipass smartcard
