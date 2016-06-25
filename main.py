#! /usr/bin/python
# -*- coding: utf-8 -*-


class Application(object):
	"""
	このアプリケーションのメインループを管理するオブジェクト。
	"""
	def __init__(self):
		"""
		1,pygameを初期化
		2,screenサーフェスの作成と設定
		"""
		#初期化処理
		self.init_attr()
		self.init_pygame()
		
	def main(self):
		"""
		1,メインループを包括するStock_Chart()インスタンスの生成と、そのメインループを呼び出す。
		2,行儀よくexit
		"""
		#メインループ
		self.main_loop()
		#再初期化
		pygame.quit()	#pygameの停止

	def init_attr(self):
		"""インスタンスメンバ変数の初期化"""
		root = Root_Box()

	def init_pygame(self):
		"""pygameの初期化"""
		pygame.init()
		pygame.display.set_caption("株チャートテクニカル分析")
		pygame.display.set_mode(SCREEN_SIZE,pygame.RESIZABLE)

	def mainloop(self):
		"""
		このアプリのメインループ
		self.root.main_loopに移譲。
		"""
		self.root.mainloop()


if __name__ == '__main__' :
	app = Application()
	app.main()

