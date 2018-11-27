# -*- coding: utf-8 -*-

import os
import time
from itertools import cycle

import evdev
from evdev import ecodes
import yaml


class BluetoothDevice:
    """
    BluetoothDeviceをあらわすInputDeviceオブジェクトを取得するためのクラス。
    """

    # クラス変数：デバイス　..使ってる？！
    device = None

    def get_input_device(self, path):
        """
        引数pathで指定されたデバイスファイルをInputDevice化して返却する。

        引数
            path    インプットデバイスファイル(/dev/input/...)パス
        戻り値
            デバイスオブジェクト
        """
        return evdev.InputDevice(path)

    def find_input_device(self, search_term):
        """
        全イベントデバイスを引数指定したsearch_termで検索し、
        1件合致した場合のみ、該当するイベントデバイスオブジェクトを返却する。

        引数
            search_term          検索対象文字列（小文字指定すること）
        戻り値
            likely_devices[0]    合致したイベントデバイスオブジェクト
        """

        # イベントデバイスとして登録されているすべてのパスをもとにInputDeviceオブジェクト化したリスト
        # イベントデバイス＝(/dev/input/event*)
        all_devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        # 類似デバイスリストを初期化
        likely_devices = []
        # 全イベントデバイスオブジェクトループ
        for device in all_devices:
            print('device = ', device)
            # 検索文字列が小文字化したイベントデバイス名と合致する場合
            if search_term in device.name.lower():
                # 類似デバイスリストにイベントデバイスオブジェクトを追加
                likely_devices.append(device)

        # 1件合致の場合
        if len(likely_devices) == 1:
            # 発見した1件(イベントデバイスオブジェクト)を返却
            return likely_devices[0]

        # 2件以上合致の場合
        if len(likely_devices) >= 2:
            # 例外 ValueError を発生
            raise ValueError("Found multiple device possible devices. Please specify the specific event_input_path.")

    def load_device(self, search_term):
        """
        キャラクタデバイスを検索しヒットした場合インスタンス変数deviceへ格納する。

        引数
            search_term          検索対象文字列（小文字指定すること）
        戻り値
            なし(インスタンス変数deviceを後進)
        """

        # ローカル変数 device を初期化
        device = None
        # デバイス発見までループ
        while device is None:
            # 検索文字列search_termに合致するイベントデバイスオブジェクトを取得する
            device = self.find_input_device(search_term)
            # 合致するデバイスが存在しない場合
            if device is None:
                print("Device matching '{}' couldn't be found. Trying again in 3 seconds.".format(search_term))
                # 3秒待機して繰り返す
                time.sleep(3)
        # 発見したイベントデバイスオブジェクトをインスタンス変数deviceへ格納する
        self.device = device


class BluetoothGameController(BluetoothDevice):
    """
    Generator of cordinates of a bouncing moving square for simulations.
    """

    def __init__(self, event_input_device=None, config_path=None, device_search_term=None, verbose=False):
        '''
        コンストラクタ。

        引数
            event_input_device    イベント Input デバイス(デフォルトNone)
            config_path           設定ファイル(YAML型式)へのパス(デフォルトNone)
            device_search_term    デバイス検索文字列(デフォルトNone)
            verbose               妥当性検査(デフォルトFalse)
        戻り値
            なし
        '''

        # 妥当性検査
        self.verbose = verbose
        # 実行中判定
        self.running = False

        # 状態
        self.state = {}
        # アングル値
        self.angle = 0.0
        # スロットル値
        self.throttle = 0.0

        # スロットル倍率
        self.throttle_scale = 1.0
        # スロットル倍率増分
        self.throttle_scale_increment = .05
        # y軸方向正負補正値
        self.y_axis_direction = -1  # pushing stick forward gives negative values

        # 運転モード取りうる値(無限イテレータ)
        self.drive_mode_toggle = cycle(['user', 'local_angle', 'local'])
        # 運転モード
        self.drive_mode = next(self.drive_mode_toggle)

        # 記録モード取りうる値(無限イテレータ)
        self.recording_toggle = cycle([True, False])
        # 記録モード
        self.recording = next(self.recording_toggle)

        # 設定ファイルが指定されていない場合
        if config_path is None:
            # デフォルト設定ファイルのフルパスを登録
            config_path = self._get_default_config_path()
        # 設定ファイルを読み込む
        self.config = self._load_config(config_path)

        # ボタンマップ(key:ID,value:ボタン名)
        self.btn_map = self.config.get('button_map')
        # 最大棒倒し時のvalue値(指定がない場合1280)
        self.joystick_max_value = self.config.get('joystick_max_value', 1280)

        # Inputストリーム(/dev/input/...)を検索するための文字列
        # (指定がない場合設定ファイルの'device_search_term'値、それもない→1280)
        self.device_search_term = device_search_term or self.config.get('device_search_term', 1280)

        # 引数イベントInputデバイスの指定がない場合
        if event_input_device is None:
            # 検索文字列self.device_search_term と合致するイベントデバイスオブジェクトを取得し
            # インスタンス変数 self.device へ格納する
            self.load_device(self.device_search_term)
            # ?必ずNoneでしょ、コレ..
            print(event_input_device)
        # 引数イベントInputデバイスに指定がある場合
        else:
            # インスタンス変数deviceに登録
            self.device = event_input_device

        # 関数マップ(key:ボタン名, value:呼び出す関数)
        self.func_map = {
            'LEFT_STICK_X': self.update_angle,            # アングル値更新
            'LEFT_STICK_Y': self.update_throttle,         # スロットル値更新
            'B': self.toggle_recording,                   # 記録モード変更
            'A': self.toggle_drive_mode,                  # 運転モード変更
            'PAD_UP': self.increment_throttle_scale,      # スロットル倍率増加
            'PAD_DOWN': self.decrement_throttle_scale,    # スロットル倍率減少
        }

    def _get_default_config_path(self):
        '''
        デフォルト設定ファイルパスを取得する。

        引数
            なし
        戻り値
            デフォルト設定ファイルパスのフルパス
        '''
        # wii_config.yml のフルパスを返却
        return os.path.join(os.path.dirname(__file__), 'wiiu_config.yml')

    def _load_config(self, config_path):
        '''
        引数で指定された設定ファイルを読み込む。

        引数
            config_path    設定ファイルパス
        戻り値
            config         設定ファイルをパースしたYAMLオブジェクト
        '''
        with open(config_path, 'r') as f:
            # YAML型式ファイルをパース
            config = yaml.load(f)
        # パース済みYAMLオブジェクトを返却
        return config

    def read_loop(self):
        """
        イベントデバイスから１件読み取り、対象のボタン名、押下判定値(0,1)もしくは
        棒倒し比率(-1～0～1)を返却する。OSError発生時はともにNoneを返却する。

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
            btn = self.btn_map.get(event.code)
            # value値からデジタル/アナログレベル値を取得
            val = event.value
            # アナログ値である場合
            if event.type == ecodes.EV_ABS:
                # 最大棒倒し値で割り、棒倒し率化してvalue値を更新
                val = val / self.joystick_max_value
            print('code: [', event.code,  '] val:', event.value, '] type:[', event.type, ']')
            print(' is analog: ', (event.type == ecodes.EV_ABS) )
            print(' match name: ', btn)
            # ボタン名、値の返却
            return btn, val

        # OSエラー発生時
        except OSError as e:
            print('OSError: Likely lost connection with controller. Trying to reconnect now. Error: {}'.format(e))
            # 0.1秒待機
            time.sleep(.1)
            # 検索文字列self.device_search_term と合致するイベントデバイスオブジェクトを取得し
            # インスタンス変数 self.device へ格納する（やりなおし）
            self.load_device(self.device_search_term) #device_search_termの誤り
            # ボタン名, 値ともにNoneを返却
            return None, None

    def update(self):
        '''
        partクラスとなるためのテンプレートメソッド。
        値が更新されるたびに関数マップから呼び出す関数を取得して呼び出す処理を繰り返す。

        引数
            なし
        戻り値
            なし
        '''
        while True:
            # イベントデバイスから１件読み取り、対象のボタン名、値を取得する
            btn, val = self.read_loop()

            # 状態を更新
            self.state[btn] = val

            # 関数マップからボタン名に合致する関数を取得
            func = self.func_map.get(btn)
            if func is not None:
                # 合致した関数を呼び出す
                func(val)

            # 妥当性検査モードが真の場合
            if self.verbose==True:
                # ボタン名、値を表示
                print("button: {}, value:{}".format(btn, val))

    def run_threaded(self, img_arr=None):
        '''
        スレッド実行可能なpartクラスとなるためのテンプレートメソッド。
        インスタンス変数の各値を返却する。
        (各インスタンス変数の更新はupdate()内で実行される)

        引数
            img_arr    画像イメージデータ(内部では使用していない)
        戻り値
            angle         アングル値
            throttle      スロットル値
            drive_mode    運転モード
            recording     記録モード
        '''
        # インスタンス変数の各値をそのまま返却
        return self.angle, self.throttle, self.drive_mode, self.recording

    def shutdown(self):
        '''
        停止処理を行う。

        引数
            なし
        戻り値
            なし
        '''
        #　実行モードを偽値にする
        self.running = False
        time.sleep(0.1) #0.1秒待機

    def update_angle(self, val):
        '''
        アングル値を更新する。

        引数
            val    アングル値
        戻り値
            なし
        '''
        # インスタンス変数 angle を更新する
        self.angle = val
        return

    def update_throttle(self, val):
        '''
        スロットル値を更新する。

        引数
            val    スロットル値
        戻り値
            なし
        '''
        # インスタンス変数 throttle を更新する
        # 引数の値×スロットル倍率×y軸方向正負補正値
        self.throttle = val * self.throttle_scale * self.y_axis_direction
        return

    def toggle_recording(self, val):
        '''
        記録モードを変更する。

        引数
            val     押下判定(1:押, 0:無)
        戻り値
            なし
        '''
        # 押下時
        if val == 1:
            # インスタンス変数 recording を次の設定値に変更する
            self.recording = next(self.recording_toggle)
        return

    def toggle_drive_mode(self, val):
        '''
        運転モードを変更する。

        引数
            val     押下判定(1:押, 0:無)
        戻り値
            なし
        '''
        # 押下時
        if val == 1:
            # インスタンス変数 drive_mode を次の設定値に変更する
            self.drive_mode = next(self.drive_mode_toggle)
        return

    def increment_throttle_scale(self, val):
        '''
        スロットル倍率を増加させる。

        引数
            val    押下判定(1:押, 0:無)
        戻り値
            なし
        '''
        # 押下時
        if val == 1:
            # インスタンス変数 throttle_scale の値を
            # self.sthrottle_scale_increment分加算する
            self.throttle_scale += self.throttle_scale_increment
        return

    def decrement_throttle_scale(self, val):
        '''
        スロットル倍率を減少させる。

        引数
            val    押下判定(1:押, 0:無)
        戻り値
            なし
        '''
        # 押下時
        if val == 1:
            # インスタンス変数 throttle_scale の値を
            # self.sthrottle_scale_increment分減算する
            self.throttle_scale -= self.throttle_scale_increment
        return


if __name__ == "__main__":
    # デバイス検索文字列を標準入力から入力させる
    device_search_term = input("""Please give a string that can identify the bluetooth device (ie. nintendo)""")
    # 指定されなかった場合
    if device_search_term == "":
        # 検索対象文字列をNoneとする
        device_search_term = None
        print('No search term given. Using default.')

    # 検索対象文字列に合致するコントローラオブジェクトを生成する
    # 妥当性検査(Debug)モードで実行する
    ctl = BluetoothGameController(verbose=True, device_search_term=device_search_term)
    # イベント待受ループを開始する
    # 妥当性検査モードがTrueなのでジョイスティックのボタンやアナログスティックを操作したら
    # そのボタン名、値が１行ごとに表示される。
    ctl.update()