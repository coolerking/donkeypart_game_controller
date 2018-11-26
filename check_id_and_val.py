# -*- coding: utf-8 -*-
from part.bt_con import BluetoothGameController

class CheckController(BluetoothGameController):
    def __init__(self, input_device_path='/dev/input/js0', *args, **kwargs):
        super(CheckController, self).__init__(*args, **kwargs)
        print('change device file: ', input_device_path)
        self.device = self.get_input_device(input_device_path)


if __name__ == "__main__":

    # 検索対象文字列に合致するコントローラオブジェクトを生成する
    # 妥当性検査(Debug)モードで実行する
    ctl = CheckController(input_device_path='/dev/input/js0', verbose=True, device_search_term=device_search_term)
    # イベント待受ループを開始する
    # 妥当性検査モードがTrueなのでジョイスティックのボタンやアナログスティックを操作したら
    # そのボタン名、値が１行ごとに表示される。
    ctl.update()