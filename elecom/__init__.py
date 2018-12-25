# -*- coding: utf-8 -*-
"""
ELECOM製ジョイスティック JC-U3912T を使用するためのpartクラス。
donkeypart_bluetooth_game_controller パッケージのクラスを基底クラスとして使用するため、
先にインストールしておく必要がある。

git clone https://github.com/autorope/donkeypart_bluetooth_game_controller.git
cd donkeypart_bluetooth_game_controller
pip install -e .

各ボタン/各axisにどの機能が割り振られているかは、
コントロールクラス JoystickController の self.func_map を参照のこと。
"""
import time
import evdev
from evdev import ecodes

from donkeypart_bluetooth_game_controller import BluetoothGameController

class JoystickController(BluetoothGameController):
    '''
    JC-U3912T ゲームパッド用コントローラクラス。
    manage.pyを編集し、ジョイスティックコントローラとして本コントローラをimportし
    て使用する。
    Vehiecleフレームワークに準拠している。
    '''
    def __init__(self, 
        event_input_device=None, 
        config_path=None, 
        device_search_term=None, 
        verbose=False):
        '''
        コンストラクタ。
        親クラスの実装を処理後、ELECOM製JC-U3912T固有の設定に対応できるように
        引数で与えられた項目をもとにいくつかのインスタンス変数を初期化・上書きする。

        引数
            event_input_device    イベントキャラクタデバイスのInputDeviceオブジェクト(デフォルトNone→device_search_termで検索する)
            config_path           設定ファイルパス(デフォルトNone)
            device_search_term    検索対象文字列(デフォルトNone)
            verbose               デバッグモード(デフォルトFalse)
        戻り値
            なし
        '''
        # デフォルト値の設定
        if config_path:
            config_path = 'elecom/jc_u3912t.yml'
        if device_search_term:
            device_search_term = 'smart jc-u3912t'

        super(JoystickController, self).__init__(
            event_input_device=event_input_device, 
            config_path=config_path, 
            device_search_term=device_search_term, 
            verbose=verbose)

        # コードマップ(event.type==3)
        self.code_map = self.config.get('code_map')
        # button_map 対象となるラベル
        self.button_map_target = self.config.get('button_map_target', 
            ['BUTTON'])
        # DPAD 対象となるラベル
        self.dpad_target = self.config.get('dpad_target', 
            ['DPAD_UP', 'DPAD_DOWN', 'DPAD_LEFT', 'DPAD_RIGHT'])
        
        # アナログ/DPADの正負反転補正
        self.y_axis_direction = self.config.get('axis_direction', -1)

        # event.value 可変値範囲
        self.analog_stick_max_value = self.config.get('analog_stick_max_value', 255)
        self.analog_stick_zero_value = self.config.get('analog_stick_zero_value', 128)
        self.analog_stick_min_value = self.config.get('analog_stick_min_value', 0)

        # 独自関数マップ　書き換え(key:ボタン名, value:呼び出す関数)
        self.func_map = {
            'LEFT_STICK_X': self.update_angle,     # アングル値更新
            'RIGHT_STICK_Y': self.update_throttle, # スロットル値更新
            '1': self.toggle_recording,            # 記録モード変更
            '4': self.toggle_drive_mode,           # 運転モード変更
            '2': self.increment_throttle_scale,    # スロットル倍率増加
            '3': self.decrement_throttle_scale,    # スロットル倍率減少
        }

    def read_loop(self):
        """
        イベントデバイスから１件読み取り、対象のボタン名、値を返却する。
        親クラスの実装のままでは JC-U3912T 固有のイベントキャラクタデバイス
        フォーマットに対応できないため、本メソッドをオーバライドして対応している。

        引数
            なし
        戻り値
            btn     対象のボタン名
            val     押下判定値(0,1)もしくは棒倒し率(-1～0～1)
        """
        try:
            # イベントデバイスから1件イベントを読み込む
            event = next(self.device.read_loop())
            # code値から対象のボタン名を取得
            btn = self.code_map.get(event.code)
            if btn in self.button_map_target:
                # event.value値から詳細ボタン名を取得
                btn = self.btn_map.get(event.value)

            # アナログジョイスティック/DPAD(3)の場合
            if event.type == ecodes.EV_ABS:
                # アナログジョイスティック/DPADへ入力すると
                # 入力時に1イベント以上、離脱時に1イベント直列に発生する
                if self.verbose:
                    print('type == ecodes.EV_ABS -> analog/dpad')
                if btn in self.dpad_target:
                    if self.verbose:
                        print(btn, ' is in dpad_tareget')
                    # 上/左:-1 中央:0 sita 下/右:1
                    val = event.value * 1.0 
                else:
                    if self.verbose:
                        print(btn, ' is not in dpad_target')
                    # 中央位置の場合
                    if event.value == self.analog_stick_zero_value:
                        val = 0.0
                    # 中央位置以外の場合
                    else:
                        val = ((event.value - self.analog_stick_zero_value) * 1.0) \
                            / ((self.analog_stick_max_value - self.analog_stick_min_value) / 2.0)
            # 通常ボタン(4)の場合
            elif event.type == ecodes.EV_MSC:
                if self.verbose:
                    print('type == ecodes.EV_ABS -> not analog/dpad')
                # JC-U3912T ではボタン離脱イベントは存在しない
                val = 1
            # その他のイベントの場合
            else:
                if self.verbose:
                    print('unknown type: ', event.type)
                    print('code: [', event.code,  '] val:[', event.value, '] type:[', event.type, ']')
                # ボタン名, 値ともにNoneを返却
                return None, None

            # デバッグコード
            if self.verbose:
                print('code: [', event.code,  '] val:[', event.value, '] type:[', event.type, ']')
                print('name: [', btn, '] value=(', val ,')')

            # ボタン名、値の返却
            return btn, val

        # OSエラー発生時
        except OSError as e:
            print('OSError: Likely lost connection with controller. Trying to reconnect now. Error: {}'.format(e))
            # 0.1秒待機
            time.sleep(.1)
            # 検索文字列self.device_search_term と合致するイベントデバイスオブジェクトを取得し
            # インスタンス変数 self.device へ格納する（やりなおし）
            self.load_device(self.device_search_term)
            # ボタン名, 値ともにNoneを返却
            return None, None
    