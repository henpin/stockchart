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

#イベント名に関するグローバル変数
PYGAME_EVENTTYPE_EVENTNAME_TABLE = {
	pygame.MOUSEBUTTONDOWN : "MOUSEBUTTONDOWN",
	pygame.MOUSEBUTTONUP : "MOUSEBUTTONUP",
	pygame.MOUSEMOTION : "MOUSEMOTION"
	pygame.KEYDOWN : "KEYDOWN"
	pygame.VIDEORESIZE : "VIDEORESIZE"
	pygame.QUIT : "QUIT"
	}#pygame.localsで定義されるイベント定数とイベント名のマップ

PYGAME_GLOBAL_EVENTNAMES = (
	"MOUSEBUTTONDOWN", #マウス関連
	"MOUSEBUTTONUP",
	"MOUSEMOTION",
	"KEYDOWN", #キー関連
	"FUNCTIONKEYDOWN", #特殊関連
	"VIDEORESIZE",
	"QUIT",
	)#Pygameのイベント名

#Pygameのイベント名に対応するイベントプロセッサインターフェイス
PYGAME_GLOBAL_EVENT_PROCESSOR = eventer.generate_event_processor(PYGAME_GLOBAL_EVENTNAMES)


# Base-Classes For PygameEventers
class Key_Repeat_Controler(object):
	"""
	キーリピートを検知する単純な部分クラス
	"""
	def __init__(self):
		"""
		"""
		#クラス構造のチェック
		if not isinstance(self,Pygame_Event_Rooter) :
			raise Exception("このクラスはPygame_Event_Rooterの単純部分実装です")
		#キーテーブル
		self.key_repeat_table = {}	#pygame.key:repeatの情報

	def validate_keypress(self,key):
		"""
		引数に与えられたキーkeyについて、それに関するイベントが伝搬されるべきかどうかを判定するメソッド。
		このメソッドは、そのキーについてのフレームをまたいでの情報を、self.key_repeat_tableから参照する。
		なお、キーについての情報は、当然前フレームまでの情報をベースに取得するべきだから、
		キー情報の更新メソッドself.update_key_repeat_table()は同一フレームにおいて、このメソッドより後に呼び出されなければならない。
		"""
		numof_frames = self.key_repeat_table.get(key,0)	#キーの押され続けているフレーム数
		#消費フレーム数が1~3以内なら、それをブロックする。
		elif 1 <= numof_frames <= 3 :
			return False

	def update_key_repeat_table(self,pressed_keys):
		"""
		キー処理に関する状態を保存するためのメソッド。
		押されたキーに対する、その押され続けているフレーム数を数える。

		このメソッドはキーに関するすべてのイベント処理が終了してから呼ばれるべきである。
		"""
		#キーの押されているフレーム数をアップデートする
		for key in pressed_keys :
			if key in self.key_repeat_table :
				self.key_repeat_table[key] += 1
			else :
				self.key_repeat_table[key] = 1

		#フレーム検出中のキーが押されていないのならそのキーについてのフレーム情報を初期化
		active_keys = [ key for key in self.key_repeat_table if self.key_repeat_table.get(key) ]
		for key in active_keys :
			if key not in pressed_keys :
				self.key_repeat_table[key] = 0	#非アクティブ化


# Pygame Event Classes
class Pygame_Event_Rooter(
	eventer.Event_Rooter,
	PYGAME_GLOBAL_EVENT_PROCESSOR,
	Key_Repeat_Controler,
	):
	"""
	Event_Rooterのpygame実装。
	pygameプログラムにおいて、「mainloop」を実装するプログラムが継承することを前提としている。
	pygameのインターフェイスからイベントを取得し、分配する。
	"""
	def __init__(self):
		eventer.Event_Distributer.__init__(self)
		Key_Repeat_Controler.__init__(self)

	def dispatch_event(self):
		"""
		イベントを補足、処理する最上層のルーチンで、イベントの処理はpygameによって提供される２つの手段を両方用います。
		まず、全てのキーイベントに対しては、pygame.keyモジュールの枠組みを用います。これはpygame.eventではキーリピートを補足できない為です。
		一方、マウスイベントや、その他終了、リサイズイベントの処理についてはpygame.eventに提供されるイベントキューの枠組みを用います。
		ただし、イベントの処理に関する情報伝達インターフェイスの統一の為、
		「前者の枠組みにおいても」、能動的にpygameのイベントオブジェクトを発行し、これをdiispachする。
		"""
		#Do Process
		self.dispatch_event_on_keystate()
		self.dispatch_event_on_queue()

	def dispatch_event_on_keystate(self):
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
			if not self.validate_keypress(key) :
				continue	#キーリピートヴァリデートにひっかかったのでイベントは発行しない
			event = pygame.event.Event(pygame.KEYDOWN,key=key,mod=mod)	#イベントの発行
			self.root_event(pygame.KEYDOWN,event)

		#キーリピートの情報の更新
		self.update_key_repeat_table(pressed_keys)

	def dispatch_event_on_queue(self):
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

	#イベントプロセス
	def process_QUIT(self,event):
		"""
		終了イベントの処理
		"""
		self.looping = False	#停止。



	
