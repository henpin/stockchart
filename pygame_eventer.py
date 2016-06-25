#! /usr/bin/python
# -*- coding: utf-8 -*-

import pygame
import eventer

"""
eventerモジュールのpygame拡張。

大まかに以下を実装する。
1,Pygameにおけるイベントインターフェイスの定義
2,PygameにおけるEvent_Rooter実装
3,キーリピートをバリデーションするEvent_Monitor実装
"""

#Pygameのイベント名に対応するイベントプロセッサインターフェイス
PYGAME_GLOBAL_EVENTNAMES = (
	pygame.MOUSEBUTTONDOWN
	pygame.MOUSEBUTTONUP
	pygame.MOUSEMOTION
	pygame.KEYDOWN
	pygame.VIDEORESIZE
	pygame.QUIT
	)#Pygameのイベント名
PYGAME_GLOBAL_EVENT_PROCESSOR = eventer.generate_event_processor(PYGAME_GLOBAL_EVENTNAMES)


class Pygame_Event_Rooter(eventer.Event_Rooter):
	"""
	Event_Rooterのpygame実装。
	pygameプログラムにおいて、「mainloop」を実装するプログラムが継承することを前提としている。
	pygameのインターフェイスからイベントを取得し、分配する。
	"""
	def __init__(self):
		eventer.Event_Distributer.__init__(self)

	def dispatch_event(self):
		"""
		イベントを補足、処理する最上層のルーチンで、イベントの処理はpygameによって提供される２つの手段を両方用います。
		まず、全てのキーイベントに対しては、pygame.keyモジュールの枠組みを用います。これはpygame.eventではキーリピートを補足できない為です。
		一方、マウスイベントや、その他終了、リサイズイベントの処理についてはpygame.eventに提供されるイベントキューの枠組みを用います。
		ただし、イベントの処理に関する情報伝達インターフェイスの統一の為、
		「前者の枠組みにおいても」、能動的にpygameのイベントオブジェクトを発行し、これをdiispachする。
		"""
		def dispatch_event_on_keystate():
			"""
			pygame.keyを用いたキーイベント処理。
			Eventオブジェクトを自己発行する。
			また、キーの繰り返し処理に対応する為にself.validate_keypress()を、
			キーについてのフレームをまたいだ情報を格納するためにself.update_key_information()を、それぞれこの中で呼ぶ。
			"""
			def get_modifered(key_state):
				"""キーモディファ情報を格納した定数を返す"""
				shift_mod = pygame.K_RSHIFT in pressed_keys or pygame.K_LSHIFT in pressed_keys
				ctrl_mod = pygame.K_RCTRL in pressed_keys or pygame.K_LCTRL in pressed_keys
				mod = ( shift_mod and pygame.KMOD_SHIFT ) or ( ctrl_mod and pygame.KMOD_CTRL ) or 0
				return mod

			#イベントの取得
			key_state = pygame.key.get_pressed()
			pressed_keys = [ index for index in range(len(key_state)) if key_state[index] ]	#現在押されているキーのpygame定数のリスト
			#モディファ情報の取得
			mod = get_modifered(key_state)

			#イベントの生成
			for key in pressed_keys :
				event = pygame.event.Event(pygame.KEYDOWN,key=key,mod=mod)	#イベントの発行
				self.root_event(pygame.KEYDOWN,event)

		def dispatch_event_on_queue():
			"""
			イベントキュー上の処理。
			pygame.eventにより提供されるイベントキューからイベントを取り出して処理する。
			"""
			for event in pygame.event.get():
				#終了処理
				if event.type == pygame.QUIT or pygame.K_ESCAPE in pygame.key.get_pressed() :
					self.root_event(pygame.QUIT,event)
				#ドラッグイベントの補足
				elif event.type == pygame.MOUSEMOTION :
					if event.buttons[0] :	#ドラッグイベントとして補足
						self.root_event(self.EVENT_MOUSEDRAG,event)
					else :	#マウスボタンダウンイベントの発行
						self.root_event(self.EVENT_MOUSEBUTTONDOWN,event)
				#あるいは単にルーティング
				else :
					event_name = eventtype2name(event.type)
					self.root_event(event_name,event)

		#Do Process
		dispatch_event_on_keystate()
		dispatch_event_on_queue()

	#イベントプロセス
	def process_QUIT:
		"""
		終了イベントの処理
		"""
		self.looping = False	#停止。


class KeyEvent_Validater(eventer.Event_Monitor):
	"""
	キーイベントに関するイベント監視クラス。
	"""
	def __init__(self):
		self.key_information = {}	#pygameから提供されるキーの定数と、その押され続けているフレーム数の辞書

	def get_key_state(self,key):
		"""
		キーの状態とフレームをまたいだキー状態に関する情報を得る為のインターフェイス。
		押されていれば少なくとも0以上を返す
		"""
		return self.key_information.get(key,0)

	def validate_keypress(self,key):
		"""
		引数に与えられたキーkeyについて、それに関するイベントが伝搬されるべきかどうかを判定するメソッド。
		このメソッドは、そのキーについてのフレームをまたいでの情報を、self.key_informationから参照する。
		なお、キーについての情報は、当然前フレームまでの情報をベースに取得するべきだから、
		キー情報の更新メソッドself.update_key_information()は同一フレームにおいて、このメソッドより後に呼び出されなければならない。
		"""
		numof_frames = self.get_key_state(key)	#キーの押され続けているフレーム数
		#消費フレーム数が1~3以内なら、それをブロックする。
		if not numof_frames :
			return True
		elif 1 <= numof_frames <= 3 :
			return False
		elif 4 <= numof_frames :
			return True

	def update_key_information(self,pressed_keys):
		"""
		キー処理に関する状態を保存するためのメソッド。
		押されたキーに対する、その押され続けているフレーム数を数える。

		このメソッドはキーに関するすべてのイベント処理が終了してから呼ばれるべきである。
		"""
		#キーの押されているフレーム数をアップデートする
		for key in pressed_keys :
			if key in self.key_information :
				self.key_information[key] += 1
			else :
				self.key_information[key] = 1

		#フレーム検出中のキーが押されていないのならそのキーについてのフレーム情報を初期化
		for key in [ key for key in self.key_information if self.key_information[key] ]:
			if key not in pressed_keys :
				self.key_information[key] = 0

	
