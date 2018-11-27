#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ジョイスティック動作と出力コードを確認するためのプログラム。

キャラクタデバイス  /dev/input/js0 として認識されている
ジョイスティックのボタン操作を行うとどのようなコードが
出力されているのかを確認するためのプログラム。

fcntl パッケージを使用するため、Windows環境では動作しない。
"""
import array
import time
import struct
from fcntl import ioctl

axis_states = {}            # 方向状態辞書{方向名:状態}:init()にて書き込まれる
button_states = {}          # ボタン状態辞書{ボタン名,状態}:init()にて書き込まれる
axis_map = []               # 方向マップ[方向名]:init()にて書き込まれる
button_map = []             # ボタンマップ[ボタン名]:init()にて書き込まれる
jsdev = None                # ジョイスティックキャラクタデバイス ファイルオブジェクト
dev_fn = '/dev/input/js0'   # ジョイスティックキャラクタデバイス パス

# ifdef ELECOM JC-U3912T
'''
axis_names = {
            0:  'left_stick_horz',
            1:  'left_stick_vert',
            2:  'right_stick_vert',
            3:  'right_stick_horz', # unknown 0x10 or x011
            4:  'dpad_horz', # unknown 0x10 or 0x11
            5:  'dpad_vert'
}

button_names = {
            0: '1',   # square
            1: '2',   # triangle
            2: '3',   # cross
            3: '4',   # circle
            4: '5',   # L1
            5: '6',   # R1
            6: '7',   # L2
            7: '8',   # R2
            8: 'left_stick_pressure', # 9_pressure
            9: 'right_stick_pressure', # 10_pressure
            10: '11', # select
            11: '12'  # start
}
'''

#ifdef Logicool F710
axis_names = {
            0:  'left_stick_horz',
            1:  'left_stick_vert',
            2:  'LT_pressure',
            3:  'right_stick_horz',
            4:  'right_stick_vert',
            5:  'RT_pressure',
            6:  'dpad_horz',
            7:  'dpad_vert',
}

button_names = {
            0:  'A',     # cross
            1:  'B',     # circle
            2:  'X',     # square
            3:  'Y',     # triangle
            4:  'LB',    # L1
            5:  'RB',    # R1
            6:  'BACK',  # select
            7:  'START', # start

            9:  'left_stick_pressure',
            10: 'right_stick_pressure',
}

def init():
    print('Opening %s...' % dev_fn)
    with open(dev_fn, 'rb') as jsdev:

        # Get the device name.
        buf = array.array('B', [0] * 64)
        ioctl(jsdev, 0x80006a13 + (0x10000 * len(buf)), buf) # JSIOCGNAME(len)
        js_name = buf.tobytes().decode('utf-8')
        print('Device name: %s' % js_name)

        # Get number of axes and buttons.
        buf = array.array('B', [0])
        ioctl(jsdev, 0x80016a11, buf) # JSIOCGAXES
        num_axes = buf[0]
        print('num_axes: ', num_axes)

        buf = array.array('B', [0])
        ioctl(jsdev, 0x80016a12, buf) # JSIOCGBUTTONS
        num_buttons = buf[0]
        print('num_buttons: ', num_buttons)

        # Get the axis map.
        buf = array.array('B', [0] * 0x40)
        ioctl(jsdev, 0x80406a32, buf) # JSIOCGAXMAP

        print('***** axis_name list')
        for axis in buf[:num_axes]:
            axis_name = axis_names.get(axis, 'unknown(0x%02x)' % axis)
            axis_map.append(axis_name)
            axis_states[axis_name] = 0.0
            print(' ', axis_name)
            print('    = 0x%02x' % axis)

        # Get the button map.
        buf = array.array('H', [0] * 200)
        ioctl(jsdev, 0x80406a34, buf) # JSIOCGBTNMAP

        print('***** button_name list')
        for btn in buf[:num_buttons]:
            btn_name = button_names.get(btn, 'unknown(0x%03x)' % btn)
            button_map.append(btn_name)
            button_states[btn_name] = 0
            print(' ', btn_name)
            print('    = 0x%03x' % btn)

        JS_FORMAT = "IhBB" 
        JS_SIZE = struct.calcsize(JS_FORMAT)
        print ('JS_SIZE = ', JS_SIZE)
        event = jsdev.read(JS_SIZE)
        while event:
            #(tval, value, typev, number) = struct.unpack(EVENT_FORMAT, event)
            tval, value, typev, number = struct.unpack(JS_FORMAT, event)
            print('(', tval, ', ', value, ', ', typev, ', ', number, '[ 0x03x ])' % number)
            event = jsdev.read(JS_SIZE)

if __name__ == '__main__':
    init()