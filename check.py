#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ジョイスティック動作と出力コードを確認するためのプログラム。
キャラクタデバイス  /dev/input/js0 として認識されている
ジョイスティックのボタン操作を行うとどのようなコードが
出力されているのかを確認するためのプログラム。

Usage:
    check.py (logicool) [--direct_input]
    check.py (elecom)

Options:
    -h --help       ヘルプ表示
    --direct_input  Direct Inputモードで使用
    --debug         デバッグモードで実行
"""
from docopt import docopt

if __name__ == "__main__":

    # 検索対象文字列に合致するコントローラオブジェクトを生成する
    # 妥当性検査(Debug)モードで実行する
    print('[check] start')
    args = docopt(__doc__)

    if args['elecom']:
        # ELECOM製 JC-U3912T ゲームパッドの場合
        from elecom import JoystickController
        if args['--direct_input']:
            print('[check] use F710 with DirectInput mode')
            ctl = JoystickController(config_path='logicool/f710_di.yml', verbose=True)
        else:
            print('[check] use F710 with X-Input mode')
            ctl = JoystickController(config_path='logicool/f710_xi.yml', verbose=True)
    elif args['logicool']:
        # Logicool製 F710 ワイヤレスゲームパッドの場合
        from logicool import JoystickController
        print('[check] use JC-U3912T')
        ctl = JoystickController(config_path='elecom/jc_u3912t.yml', verbose=True)

    # イベント待受ループを開始する
    # 妥当性検査モードがTrueなのでジョイスティックのボタンやアナログスティックを操作したら
    # そのボタン名、値が１行ごとに表示される。
    print('[check] push joystick button to view it\'s name and value')
    ctl.update()
    print('[check] end')