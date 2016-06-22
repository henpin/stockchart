#! /usr/bin/python
# -*- coding: utf-8 -*-

import pygame
import eventer

"""
eventerモジュールのpygame拡張。
キー入力のリピート処理などを担当
"""

class Pygame_Event_Rooter(eventer.Event_Rooter):
	"""
	Event_Rooterのpygame実装。
	pygameプログラムにおいて、「mainloop」を実装するプログラムが継承することを前提としている。
	pygameのインターフェイスからイベントを取得し、分配する。
	"""
	def __init__(self):
		eventer.Event_Distributer.__init__(self)

	def root_events(self):
		"""
		イベントを補足、処理する最上層のルーチンで、イベントの処理はpygameによって提供される２つの手段を両方用います。
		まず、全てのキーイベントに対しては、pygame.keyモジュールの枠組みを用います。これはpygame.eventではキーリピートを補足できない為です。
		一方、マウスイベントや、その他終了、リサイズイベントの処理についてはpygame.eventに提供されるイベントキューの枠組みを用います。
		ただし、イベントの処理に関する情報伝達インターフェイスの統一の為、
		「前者の枠組みにおいても」、能動的にpygameのイベントオブジェクトを発行し、これをdiispachする。
		"""
		def root_events_on_keystate():
			"""
			pygame.keyを用いたキーイベント処理。
			Eventオブジェクトを自己発行する。
			また、キーの繰り返し処理に対応する為にself.validate_keypress()を、
			キーについてのフレームをまたいだ情報を格納するためにself.update_key_information()を、それぞれこの中で呼ぶ。
			"""
			key_state = pygame.key.get_pressed()
			pressed_keys = [ index for index in range(len(key_state)) if key_state[index] ]	#現在押されているキーのpygame定数のリスト
			shift_mod , ctrl_mod = (pygame.K_RSHIFT in pressed_keys or pygame.K_LSHIFT in pressed_keys) , (pygame.K_RCTRL in pressed_keys or pygame.K_LCTRL in pressed_keys)
			mod = ( shift_mod and pygame.KMOD_SHIFT ) or ( ctrl_mod and pygame.KMOD_CTRL ) or 0
			for key in pressed_keys :
				#Repeatなどの中間処理に関するキーブロックに引っかかるかどうか
				if self.validate_keypress(key):
					event = pygame.event.Event(pygame.KEYDOWN,key=key,mod=mod)	#イベントの発行

		def root_events_on_queue():
			"""
			イベントキュー上の処理。
			pygame.eventにより提供されるイベントキューからイベントを取り出して処理する。
			"""
			for event in pygame.event.get():
				if event.type == pygame.QUIT or self.get_key_state(pygame.K_ESCAPE) :
					self.root_event(pygame.QUIT)
					self.looping = False	#停止。
				elif event.type == pygame.MOUSEBUTTONDOWN :
					self.process_MOUSEBUTTONDOWN(event)
				elif event.type == pygame.MOUSEBUTTONUP :
					continue
				elif event.type == pygame.VIDEORESIZE :
					self.resize_window(event.size)
				elif event.type == pygame.MOUSEMOTION :
					if event.buttons[0] :	#ドラッグイベントとして補足
						self.process_MOUSEDRAG(event)
					else :
						self.process_MOUSEMOTION(event)
				elif event.type == pygame.KEYDOWN :
					if event.key == pygame.K_F11 :
						self.maximize_window()
		#Do Process
		root_event_on_keystate()
		root_event_on_queue()

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

	
