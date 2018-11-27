

from part.bt_con import BluetoothGameController

class JC_U3912T_JoystickController(BluetoothGameController):
    def __init__(self, 
        event_input_device=None, 
        config_path=None, 
        device_search_term='smart jc-u3912t', 
        verbose=False):
        super(JC_U3912T_JoystickController, self).__init__(
            event_input_device=event_input_device, 
            config_path=config_path, 
            device_search_term=device_search_term, 
            verbose=verbose)

        # コードマップ(event.type==3)
        self.code_map = self.config.get('code_map')
        # button_map 対象となるラベル
        self.button_map_target = self.config.get('button_map_target', ['BUTTON'])
        # DPAD 対象となるラベル
        self.dpad_target = self.config.get('dpad_target', ['DPAD_UP', 'DPAD_DOWN', 'DPAD_LEFT', 'DPAD_RIGHT'])

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
        イベントデバイスから１件読み取り、対象のボタン名、値を返却する

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

            # アナログジョイスティック/DPADの場合
            if event.type == ecode.EV_ABS:
                if btn in self.dpad_target:
                    # 上/左:-1 中央:0 sita 下/右:1
                    val = event.value * 1.0 
                else:
                    # 中央位置の場合
                    if event.value == self.analog_stick_zero_value:
                        val = 0.0
                    # 中央位置以外の場合
                    else:
                        val = ((event.value - self.analog_stick_zero_value) * 1.0) / 
                            ((self.analog_stick_max_value - self.analog_stick_min_value) / 2.0)
            # 通常ボタンの場合
            else:
                val = 1

            # アナログ値である場合
            if event.type == ecodes.EV_ABS:
                # 最大棒倒し値で割り、棒倒し率化してvalue値を更新
                val = val / self.joystick_max_value

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
            self.load_device(self.device_search_term) #device_search_termの誤り
            # ボタン名, 値ともにNoneを返却
            return None, None
    