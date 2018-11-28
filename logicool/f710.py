# -*- coding: utf-8 -*-
"""
Logicool製ワイヤレスゲームパッド F710 を使用するためのpartクラス。
donkeypart_bluetooth_game_controller パッケージのクラスを基底クラスとして使用するため、
先にインストールしておく必要がある。

git clone https://github.com/autorope/donkeypart_bluetooth_game_controller.git
cd donkeypart_bluetooth_game_controller
pip install -e .

F710 上部にD/Xを選択するスイッチが存在する。
これは(D)irectInputモードか(X)inputモードの選択が可能となっている。
各モードで振る舞いが代わるため、実装では２つの設定ファイルで切り分けている。

MODE横にあるLEDは、点灯時は十字キーと左アナログパッドの入力を変えている状態である。
MODEボタンを押すたびに点灯、消灯を切り替えることができる。
F710固有の仕様であり、本コードでは消灯時の状態を前提として実装している。

各ボタン/各axisにどの機能が割り振られているかは、
コントロールクラス JoystickController の self.func_map を参照のこと。
"""
import time
import evdev
from evdev import ecodes

from donkeypart_bluetooth_game_controller import BluetoothGameController

class JoystickController(BluetoothGameController):
    """
    F710 ワイヤレスゲームパッド用コントローラクラス。
    manage.pyを編集し、ジョイスティックコントローラとして本コントローラをimportし
    て使用する。
    Vehiecleフレームワークに準拠している。
    """
    def __init__(self, 
        event_input_device=None, 
        config_path=None, 
        device_search_term=None, 
        verbose=False):
        """
        コンストラクタ。
        親クラスの実装を処理後、Logicool製F710固有の設定に対応できるように
        引数で与えられた項目をもとにいくつかのインスタンス変数を初期化・上書きする。

        引数
            event_input_device    イベントキャラクタデバイスのInputDeviceオブジェクト(デフォルトNone→device_search_termで検索する)
            config_path           設定ファイルパス(デフォルトNull)
            device_search_term    検索対象文字列(デフォルトNull)
            verbose               デバッグモード(デフォルトFalse)
        戻り値
            なし
        """
        XI_SEARCH_TERM = 'logitech gamepad f710'
        XI_CONFIG_PATH = 'logicool/f710_xi.yml'
        DI_SEARCH_TERM = 'logicool logicool cordless rumblepad 2'
        DI_CONFIG_PATH = 'logicool/f710_di.yml'

        if self.find_input_device(XI_SEARCH_TERM) is None:
            super(JoystickController, self).__init__(
                event_input_device=event_input_device, 
                config_path=DI_CONFIG_PATH, 
                device_search_term=DI_SEARCH_TERM, 
                verbose=verbose)
            if self.verbose:
                print('Use Xinput configuration')
            self.is_xi = False
            self._init_di()
        else:
            super(JoystickController, self).__init__(
                event_input_device=event_input_device, 
                config_path=XI_CONFIG_PATH, 
                device_search_term=XI_SEARCH_TERM, 
                verbose=verbose)
            if self.verbose:
                print('Use DirectInput configuration')
            self.is_xi = True
            self._init_xi()

    def _init_xi(self):
        """
        Xinputモード固有の初期処理を実行する。

        引数
            なし
        戻り値
            なし
        """
        # 両モード共通初期化処理を実行
        self._init_common()


        # event.type=ecodes.EV_KEY である場合に使用する value マップを取得
        self.ev_key_value_map = self.config.get('ev_key_value_map')
        if self.verbose:
            print('ev_key_value_map: ', self.ev_key_value_map)

        # アナログスティックの入力に関する情報をインスタンス変数へ格納
        self._init_analog_domain(default_max_value=32767, default_min_value=-32768, 
            default_zero_value=0, default_epsilone=129)


    def _init_di(self):
        """
        DirectIinputモード固有の初期処理を実行する。

        引数
            なし
        戻り値
            なし
        """
        # 両モード共通初期化処理を実行
        self._init_common()

        # event.type=ecodes.EV_KEY である場合に使用する value マップを取得
        self.ev_msc_value_map = self.config.get('ev_key_value_map')

        # アナログスティックの入力に関する情報をインスタンス変数へ格納
        self._init_analog_domain(default_max_value=255, default_min_value=0, 
            default_zero_value=127.5, default_epsilone=0.5)
    
    def _init_common(self):
        """
        Xinput/DirectInput 両モード共通の処理を記述。
        キー割り当てを変更する場合は、本メソッドを編集する。

        引数
            なし
        戻り値
            なし
        """
        # event.type=ecodes.EV_ABS である場合に使用する code マップを取得
        self.ev_abs_code_map = self.config.get('ev_abs_code_map')

        # DPAD 対象となるラベル
        self.dpad_target = self.config.get('dpad_target', 
            ['DPAD_X', 'DPAD_Y'])

        # アナログ/DPADの正負反転補正
        self.y_axis_direction = self.config.get('axis_direction', -1)

        # 独自関数マップ　書き換え(key:ボタン名, value:呼び出す関数)
        self.func_map = {
            'LEFT_STICK_X': self.update_angle,     # アングル値更新
            'RIGHT_STICK_Y': self.update_throttle, # スロットル値更新
            'X': self.toggle_recording,            # 記録モード変更
            'B': self.toggle_drive_mode,           # 運転モード変更
            'Y': self.increment_throttle_scale,    # スロットル倍率増加
            'A': self.decrement_throttle_scale,    # スロットル倍率減少
        }

    def _init_analog_domain(self, default_max_value=32767, default_min_value=-32768, 
        default_zero_value=0, default_epsilone=129):
        """
        アナログジョイスティック関連情報をインスタンス変数化している。

        引数
            default_max_value     設定ファイル上に存在しない場合使用される最大値(デフォルト 32767)
            default_min_value     設定ファイル上に存在しない場合使用される最小値(デフォルト-32768)
            default_zero_value    設定ファイル上に存在しない場合使用される中央値(デフォルト0)
            default_epsilone      設定ファイル上に存在しない場合使用される中央値誤差(デフォルト129)
        戻り値
            なし
        """

        # アナログスティックの入力値に関する情報を取得
        self.analog_stick_target = self.config.get('analog_stick_target', [])
        self.analog_stick_max_value = self.config.get('analog_stick_max_value', default_max_value)
        analog_stick_zero_value = self.config.get('analog_stick_zero_value', default_zero_value)
        self.analog_stick_min_value = self.config.get('analog_stick_min_value', default_min_value)
        analog_stick_epsilone = self.config.get('analog_stick_epsilone', default_epsilone) # あそび
        self.analog_stick_zero_domain = [\
            int(analog_stick_zero_value - analog_stick_epsilone), \
            int(analog_stick_zero_value + analog_stick_epsilone)]
        if self.verbose:
            print('analog sticks are: ', self.analog_stick_target)
            print('analog sticks return [', \
                self.analog_stick_max_value, ',', \
                self.analog_stick_min_value, '] zero domain: ', self.analog_stick_zero_domain)

    def read_loop(self):
        """
        イベントデバイスから１件読み取り、対象のボタン名、値を返却する。
        親クラスの実装のままでは F710 固有のイベントキャラクタデバイス
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

            # event.type が ecodes.EV_ABS(3) である場合
            if event.type == ecodes.EV_ABS:
                # アナログパッド名の確定
                btn = self.ev_abs_code_map.get(event.code)

                # 十字キーの場合
                if btn in self.dpad_target:
                    if self.verbose:
                        print('in dpad_target: ', self.dpad_target)
                    # -1,0,1のいずれかとなるのでそのまま使用
                    val = event.value

                # 十字キー以外のアナログスティックの場合
                else:
                    if self.verbose:
                        print('analog pad: ', btn)
                    
                    # 中央値の誤差範囲内である場合
                    if self.analog_stick_zero_domain[0] < event.value and event.value < self.analog_stick_zero_domain[1]:
                        if self.verbose:
                            print('in zero domain: ', self.analog_stick_zero_domain)

                        # ゼロとして扱う
                        val = 0

                    # ゼロ誤差範囲内以外の値の場合
                    else:
                        # 明確な中央値を計算
                        middle = (self.analog_stick_zero_domain[0] + self.analog_stick_zero_domain[1]) / 2.0
                        length = self.analog_stick_max_value - self.analog_stick_min_value
                        # [-1, 1]の範囲内の値に按分
                        val = ((event.value - middle) * 1.0) / (length / 2.0)

                        if self.verbose:
                            print('compute from ', event.value, ' to ', val)

            # event.type が ecodes.EV_KEY(1) である場合
            elif event.type == ecodes.EV_KEY and self.is_xi:
                if self.verbose:
                    print('in button target(Xinput)')
                btn = self.ev_key_value_map.get(event.value)
                # 0ではない場合、 1 にする
                val = 0 if event.value == 0 else 1

            # event.type が ecodes.EV_MSC(4) である場合
            elif event.type == ecodes.EV_MSC and (not self.is_xi):
                if self.verbose:
                    print('in button target(DirectInput)')
                btn = self.ev_msc_value_map.get(event.value)
                # イベントは入力時のみ発生するため 1 を常にセット
                val = 1

            else:
                print('ignore event: ', event)
                btn = None
                val = None

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


