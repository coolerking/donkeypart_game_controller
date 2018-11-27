# -*- coding: utf-8 -*-


if __name__ == "__main__":

    # 検索対象文字列に合致するコントローラオブジェクトを生成する
    # 妥当性検査(Debug)モードで実行する
    from part.bt_elecom import JC_U3912T_JoystickController
    ctl = JC_U3912T_JoystickController(verbose=True)#, device_search_term='jc-u3912t')
    #ctl = CheckController(input_device_path='/dev/input/js0', verbose=True, device_search_term='smart jc-u3912t')
    # イベント待受ループを開始する
    # 妥当性検査モードがTrueなのでジョイスティックのボタンやアナログスティックを操作したら
    # そのボタン名、値が１行ごとに表示される。
    ctl.update()