# -*- coding: utf-8 -*-
"""
ELECOM製ジョイスティック JC-U3912T を使用するためのpartクラス。
donkeypart_ps3_controller パッケージのクラスを基底クラスとして使用するため、
先にインストールしておく必要がある。

git clone https://github.com/autorope/donkeypart_ps3_controller.git
cd donkeypart_ps3_controller
pip install -e .

各ボタン/各axisにどの機能が割り振られているかは、
コントロールクラス JC_U3912T_JoystickController の init_trigger_maps() を
参照のこと
"""
import struct
from donkeypart_ps3_controller.part import Joystick, JoystickController

class JC_U3912T_Joystick(Joystick):
    '''
    ELECOM社製 JC-U3912T ジョイスティック固有の情報を定義したサブクラス。
    基本的にコントローラから呼び出して使用する。
    '''

    def __init__(self, *args, **kwargs):
        '''
        コンストラクタ。
        JC-U3912Tでは、デバイスからbutton/axis情報を入手せず、
        予め調べたマッピング情報を使用する。
        引数
            any     Joystickクラスのコンストラクタを参照のこと
        戻り値
            なし
        '''
        super(JC_U3912T_Joystick, self).__init__(*args, **kwargs)

        self.axis_names = {
            0:  'left_stick_horz',
            1:  'left_stick_vert',
            2:  'right_stick_vert',
            3:  'right_stick_horz', # unknown 0x10 or x011
            4:  'dpad_horz', # unknown 0x10 or 0x11
            5:  'dpad_vert'
        }

        self.button_names = {
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
    
    def init(self):
        '''
        初期化処理
        親クラスの同一メソッドを実行後、以下のインスタンス変数を書き換える。
        * num_axes, num_buttons
        * axis_map, button_map
        * axis_states, button_states

        引数
            なし
        戻り値
            なし 
        '''
        super(JC_U3912T_Joystick, self).init()
        # debug code
        #print('[input] axis_map/button_map re-config * before')
        #print(' [debug] axis_map:')
        #for axis_name in self.axis_map:
        #    print('  ', axis_name)
        #print(' [debug] button_map:')
        #for btn_name in self.button_map:
        #    print('  ', btn_name)
        
        self.num_axes = len(self.axis_names)
        self.axis_map = list(self.axis_names.values())
        self.axis_states = {}
        for axis_name in self.axis_map:
            self.axis_states[axis_name] = 0.0
        
        self.num_buttons = len(self.button_names)
        self.button_map = list(self.button_names.values())
        self.button_states = {}
        for btn_name in self.button_map:
            self.button_states[btn_name] = 0

        # debug code
        #print('[input] axis_map/button_map re-config * after')
        #print(' [debug] axis_map:')
        #for axis_name in self.axis_map:
        #    print('  ', axis_name)
        #print(' [debug] button_map:')
        #for btn_name in self.button_map:
        #    print('  ', btn_name)

        
    def poll(self):
        '''
        ポーリング処理を実行する。
        キャラクタデバイスから読み取り、どのキーがどのくらい押下、傾斜させたか
        を数値化して戻す。

        引数
            なし
        戻り値
            button          ボタン名
            button_state    変化後のボタン状態
            axis            axis名
            axis_state      変化後のaxis状態
        '''
        button = None
        button_state = None
        axis = None
        axis_val = None

        if self.jsdev is None:
            return button, button_state, axis, axis_val

        # Main event loop
        evbuf = self.jsdev.read(8)

        if evbuf:
            _, value, typev, number = struct.unpack('IhBB', evbuf)

            if typev & 0x80:
                # ignore initialization event
                #print('[poll] initialization event')
                #print(' [debug] ignore event')
                return button, button_state, axis, axis_val

            if typev == 1:
                if len(self.button_map) <= number:
                    print('[poll] out of range button_map number=', number, ', len=', len(self.button_map))
                    return button, button_state, axis, axis_val
                button = self.button_map[number]
                # print(tval(_), value, typev, number, button, 'pressed')
                if button:
                    self.button_states[button] = value
                    button_state = value

            if typev == 2:
                if len(self.axis_map) <= number:
                    print('[poll] out of range axis_map number=', number, ', len=', len(self.axis_map))
                    return button, button_state, axis, axis_val
                axis = self.axis_map[number]
                if axis:
                    fvalue = value / 32767.0
                    self.axis_states[axis] = fvalue
                    axis_val = fvalue

        return button, button_state, axis, axis_val

    def _test_poll(self):
        '''
        Joystick in-key テスト用メソッド
        入力した button/axis をコントローラが何と判断しているか
        確認することができる

        引数
            なし
        戻り値
            なし
        '''
        evbuf = self.jsdev.read(8)
        if evbuf:
            _, value, typev, number = struct.unpack('IhBB', evbuf)
            if typev == 1:
                if number < self.num_buttons:
                    button_name = self.button_names[number]
                    print('[B] ', button_name, ' pressed value= ', value)
                else:
                    print('[B] out of range number=', number)
            elif typev == 2:
                if number < self.num_axes:
                    axis_name = self.axis_names[number]
                    print('[A] ', axis_name, ' pressed value= ', value)
                else:
                    print('[A] out of range number=', number)
            else:
                print('[W] warning: typev=', typev, ', number=', number)

class JC_U3912T_JoystickController(JoystickController):
    '''
    ELECOM 社製 JC-U3912T ジョイスティックのためのコントローラクラス。
    Vihecleへadd()可能なpartクラスとして実装されている。
    '''

    def __init__(self, *args, **kwargs):
        '''
        デフォルトコンストラクタ。
        親クラスのコンストラクタ処理を実行する。
        '''
        super(JC_U3912T_JoystickController, self).__init__(*args, **kwargs)

    def init_js(self):
        '''
        JC_U3912T_Joystickオブジェクトを生成、初期化する。

        引数
            なし
        戻り値
            なし
        '''
        try:
            self.js = JC_U3912T_Joystick(self.dev_fn)
            self.js.init()
        except FileNotFoundError:
            print(self.dev_fn, "not found.")
            self.js = None

        return self.js is not None

    def init_trigger_maps(self):
        '''
        JC-U3912T 上の各ボタンに機能を割り当てるマッピング情報を
        初期化する。

        引数
            なし
        戻り値
            なし
        '''
        self.button_down_trigger_map = {
            '11': self.toggle_mode,                # 運転モード変更(user, local_angle, local)
            '4': self.toggle_manual_recording,     # tubデータ保管
            '2': self.erase_last_N_records,        # 最後のN件tubデータ削除(未実装?)
            '3': self.emergency_stop,              # 緊急ストップ
            '7': self.increase_max_throttle,       # 最大スロットル値＋＋
            '8': self.decrease_max_throttle,       # 最大スロットル値ーー
            '12': self.toggle_constant_throttle,   # 常時一定スロットル確保
            "6": self.chaos_monkey_on_right,       # カオスモード
            "5": self.chaos_monkey_on_left,        # カオスモード
        }

        self.button_up_trigger_map = {
            "6": self.chaos_monkey_off,            # カオスモードoff
            "5": self.chaos_monkey_off,            # カオスモードoff
        }

        self.axis_trigger_map = {
            'left_stick_horz': self.set_steering,  # ステアリング操作
            'right_stick_vert': self.set_throttle, # スロットル操作
        }

    def _test_poll(self):
        '''
        in-keyテストを無限に繰り返す。

        引数
            なし
        戻り値
            なし
        '''
        while True:
            self.js._test_poll()

def main(ctr):
    '''
    テストを実行するための関数。

    引数
        ctr     対象とする JoystickController オブジェクト
    戻り値
        なし
    '''
    if ctr is None:
        print('[main] please set argument')
        return

    print('Joystick controller in-key test')
    print('    press button/axis on the joystick device')
    print('    press Ctrl+C to quit test')
    ctr.init_js()
    ctr._test_poll()

if __name__ == '__main__':
    ctr = JC_U3912T_JoystickController(
                 throttle_scale=0.25,
                 steering_scale=1.0,
                 auto_record_on_throttle=True)
    main(ctr)