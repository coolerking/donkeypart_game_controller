#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ジョイスティック動作と出力コードを確認するためのプログラム。

キャラクタデバイス  /dev/input/js0 として認識されている
ジョイスティックのボタン操作を行うとどのようなコードが
出力されているのかを確認するためのプログラム。

fcntl パッケージを使用するため、Windows環境では動作しない。
"""

if __name__ == "__main__":

    # 検索対象文字列に合致するコントローラオブジェクトを生成する
    # 妥当性検査(Debug)モードで実行する

    # ELECOM製 JC-U3912T ゲームパッドの場合
    #from elecom.jc_u3912t import JoystickController

    # Logicool製 F710 ワイヤレスゲームパッドの場合
    from logicool.f710 import JoystickController
    ctl = JoystickController(verbose=True)

    # イベント待受ループを開始する
    # 妥当性検査モードがTrueなのでジョイスティックのボタンやアナログスティックを操作したら
    # そのボタン名、値が１行ごとに表示される。
    ctl.update()