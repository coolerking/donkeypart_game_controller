# Donkey Car用ジョイスティックコントローラ

Donkey Carの手動運転にて以下のコントローラを使用可能にします。

* [Logicool Wireress GamePad F710](https://amzn.to/2R85kAK)

* [ELECOM Wireress GamePad JC-U3912T](https://amzn.to/2SddDvo)

ともにUSBドングルが同梱された製品であるため、Raspberry Pi上でのbluetooth設定が不要です。

> ドングルを刺さずに、Raspberry Pi本体上に搭載されたBluetoothデバイスを使用することもできますが、本サイトでは紹介しません。

# インストール

Raspberry Pi上にdonkeycarパッケージがインストールされ、`donkey createcar`コマンドで独自アプリ用ディレクトリ`~/mycar`が作成されている状態とします。

1. Raspberry Pi にターミナル接続します。
2. 以下のコマンドを実行して、前提パッケージ`donkeypart_ps3_game_controller`をインストールします。
    ```bash
    cd
    git clone https://github.com/autorope/donkeypart_ps3_controller.git
    cd donkeypart_ps3_controller
    pip install -e .
    ```
3. 以下のコマンドを実行して、本リポジトリをcloneします。
    ```bash
    cd
    git clone https://github.com/coolerking/donkeypart_game_controller.git
    ```
4. 以下のコマンドを実行して、必要なファイルを`~/mycar/part`へコピーします。
    ```bash
    mkdir ~/mycar/part
    cp ~/donkeypart_game_controller/part/*.py ~/mycar/part/
    ```
5. `~/mycar/manage.py` を、以下のように編集します(ELECOM JC-U3912Tの場合)。
    ```python
        # manage.py デフォルトのジョイスティックpart生成
        #if use_joystick or cfg.USE_JOYSTICK_AS_DEFAULT:
        #    ctr = JoystickController(max_throttle=cfg.JOYSTICK_MAX_THROTTLE,
        #                             steering_scale=cfg.JOYSTICK_STEERING_SCALE,
        #                             throttle_axis=cfg.JOYSTICK_THROTTLE_AXIS,
        #                             auto_record_on_throttle=cfg.AUTO_RECORD_ON_THROTTLE)
        # ジョイスティック part の生成
        if use_joystick or cfg.USE_JOYSTICK_AS_DEFAULT:
            # F710用ジョイスティックコントローラを使用
            #from parts.logicool import F710_JoystickController
            #ctr = F710_JoystickController(
            # PS4 Dualshock4 ジョイスティックコントローラを使用
            #from donkeypart_ps3_controller.part import PS4JoystickController
            #ctr = PS4JoystickController(
            # ELECOM JC-U3912T ジョイスティックコントローラを使用
            from parts.elecom import JC_U3912T_JoystickController
            ctr = JC_U3912T_JoystickController(

                                 throttle_scale=cfg.JOYSTICK_MAX_THROTTLE,
                                 steering_scale=cfg.JOYSTICK_STEERING_SCALE,
                                # throttle_axis=cfg.JOYSTICK_THROTTLE_AXIS,
                                 auto_record_on_throttle=cfg.AUTO_RECORD_ON_THROTTLE)
    ```

# ライセンス

本リポジトリの上記OSSで生成、コピーしたコード以外のすべてのコードはMITライセンス準拠とします。
