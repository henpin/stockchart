#! /usr/bin/python
# -*- coding: utf-8 -*-

import pygame_eventer
import contaiers
import identifire
import command_reserver
from pygame.locals import *

"""
pygameにおける描画領域の分割と、割り当て、さらには描画やイベントの伝搬までに関する広い範囲の枠組みとインターフェイスを提供するフロントエンドモジュール。

このモジュールによって規定されるすべての実装型は、Boxというコンテナ型のオブジェクトで、Root_Boxを最上位として、樹形の連鎖構造が組まれることになる。
イベントの伝搬や、描画領域の動的割り当ての機能は、この樹形構造を上から下へとメソッド呼び出しの伝搬が走り、その再帰的呼び出しによって、実装される。


このモジュールは、identifire,contaiers,eventerモジュールに依存する。

"""
# Globals

# Base-Classes For Boxes
class PygameBox_EventRooter(pygame_eventer.Pygame_Event_Rooter):
	"""
	Event_Rooterの最終実装基底クラス。
	Root_Boxに継承されなければならない。
	"""
	def __init__(self):
		"""
		"""
		if not isinstance(self,Root_Box):
			raise TypeError("PygameBox_EventRooterクラスは、ただ、RootBoxの基底クラスです。")


	#バブリングターゲットの定義
	def get_next_target(self,event_type,event):
		"""
		バブリングターゲットの定義。
		"""
		mouse_event = (
			self.EVENT_MOUSEBUTTONDOWN,
			self.EVENT_MOUSEDRAG,
			self.EVENT_MOUSEMOTION,
			)
		#マウスイベントならposから対象の算出
		if event_type in mouse_event :
			return self.get_collide_box(event.pos)	#あればBoxを返し、なければNoneを返す


	#イベントプロセス
	def process_MOUSEBUTTONDOWN(self,event):
		"""
		マウスボタンイベント。フォーカスの移動を行う
		"""
		#フォーカスの変更
		collide_box = self.get_collide_box(event.pos)
		if collide_box is not None and not collide_box.is_focused() :
			self.set_focused_box(collide_box)
			self.update()

	def process_VIDEORESIZE(self,event):
		"""
		ウィンドウのリサイズを行う。
		"""
		self.resize_window()
	
	def process_FKEYDOWN(self,event):
		"""
		特殊キーのイベント処理
		"""
		# F11で最大化
		if event.key == pygame.K_F11 :
			self.maximize_window()


# Box Classes
class BaseBox(
	pygame_eventer.PYGAME_GLOBAL_EVENT_PROCESSOR
	eventer.Event_Distributer,
	):
	"""
	すべてのBoxオブジェクトの抽象規定クラス。

	すべてのBoxオブジェクトは少なくとも以下の要件を満たす
	・サイズを含むその「描画領域」についての情報を格納し、その設定、利用のためのインターフェイスを有する。
	・イベント分配オブジェクトである。
	・(pygameのすべての標準イベントタイプに対する処理インターフェイスを有する)イベント処理オブジェクトである。
	・サーフェスの取得と、その利用に関するインターフェイスを有する。
	"""
	def __init__(self):
		"""
		"""
		eventer.Event_Distributer.__init__(self)
		self._width , self._height , self._left_top = 0,0,0	#絶対サイズ、座標値


	# サイズに関するインターフェイス
	def update_size(self):
		"""サイズ情報の更新"""
		raise Exception("オーバーライド必須")

	def get_left_top(self):
		return self._left_top

	def set_width(self,width):
		self._width = width

	def set_height(self,height):
		self._height = height

	def set_left_top(self,left_top):
		self._left_top = left_top

	def get_size(self):
		"""BOXサイズを表す(self.width,self.height)のタプルを返すだけ。"""
		return (self._width , self._height)

	def get_width(self):
		return self._width

	def get_height(self):
		return self._height


	# サーフェスに関するメソッド
	def get_rect(self):
		"""このBoxに定義された描画領域を表すRectオブジェクトを返します。"""
		left_top = self.get_left_top()
		size = self.get_size()
		return pygame.Rect(left_top,size)

	def collide_point(self,*pos):
		"""定義された絶対座標値posがこのオブジェクトに与えられた描画領域と衝突するかチェックする"""
		return self.get_rect().collidepoint(pos)

	def get_surface(self,surface_size=None,bgcolor=BACKGROUND_COLOR):
		"""
		定義された描画領域を表現するサーフェスを得る為のインターフェイス。
		"""
		raise Exception("オーバーライド必須")

	def convert_pos_to_local(self,*abs_pos):
		"""
		Root絶対座標値をこのBox内における相対座標(=BOXローカル座標値)へ変換する。
		なお、絶対座標値abs_posはこのBOXにCollideしていることを前提としている。
		"""
		abs_pos = parse_coordinate(*abs_pos)
		assert self.collide_point(abs_pos)	#エラーチェック
		left_top_onroot = self.get_left_top()
		relative_pos = ( (abs_pos[0] - left_top_onroot[0]) , (abs_pos[1] - left_top_onroot[1]) )
		return relative_pos


	# 画面の更新に関するメソッド
	def draw(self):
		"""描画メソッド"""
		raise Exception("要オーバーライド")

	def update(self):
		"""描画して更新"""
		raise Exception("オーバーライド必須")


	# フォーカスに関するメソッド
	def is_focused(self):
		"""このBoxにフォーカスがあるか否か"""
		raise Exception("オーバーライド必須")


class RootBox(
	BaseBox,
	contaiers.Container_Of_Container,
	identifire.ID_Holder,
	command_reserver.Command_Reserver,
	PygameBox_EventRooter
	):
	"""
	Boxオブジェクトによる構造の最上位に立つ唯一のオブジェクト。
	すべてのその子オブジェクトの描画領域および、そのID値の管理と利用に関する管理の立場にある。
	"""
	# 初期化メソッド
	def __init__(self):
		#上位オブジェクトの初期化処理
		BaseBox.__init__(self)
		containers.Container_Of_Container.__init__(self)
		identifire.ID_Holder.__init__(self)
		command_reserver.Command_Reserver.__init__(self)
		pygame_eventer.Pygame_Event_Rooter.__init__(self)
		#内部変数の初期化
		self.init_attr()

	def init_attr(self):
		"""属性値の初期化"""
		#サーフェスに関する属性
		self.screen = pygame.display.get_surface()
		self.background_color = BACKGROUND_COLOR
		#動作に関する属性
		self.looping = True	#メインループのスイッチ
		self.fps = 30
		self.clock = pygame.time.Clock()
		#フォーカスに関する属性
		self._focused_box = None	#操作の対象となっているコンテンツの直轄のBOX
		self.prefocused_box = None
		#その他フラグ
		self.initialized = False	#初期化処理が完全に完了しているか否かを表すフラグ。これがFalseの時は描画不能などの制限がある。
		self.maximized = False		#このオブジェクトに関連付けられたスクリーンサーフェスが最大化されているかのフラグ

	def check_initialized(self,error=False):
		"""
		初期化処理が完了しているか確認する
		オプショナル引数killがTrueを取るとき、もし初期化処理が未完了なら、例外を投げる。
		"""
		if not self.initialized and error :
			raise Exception("初期化処理が完了していません")
		return self.initialized


	# Windowサイズに関するメソッド
	def resize_window(self,*size):
		"""
		このオブジェクトに関連付けられている、スクリーンサーフェス(=Root_Window)をリサイズします。
		実際には、サイズ値を引数にとり、新たなサイズのスクリーンサーフェスを生成、取得します。
		なお、最後に描画領域の再計算と、実際の再描画を行います。
		"""
		#引数チェック
		#引数が未定義なら、デフォルトサイズにリサイズ
		if not size :
			width , height = SCREEN_SIZE
		else :
			width , height = parse_coordinate(*size)
		self.screen = pygame.display.set_mode((width,height),pygame.VIDEORESIZE)	#リサイズされたルートウィンドウの取得。
		#再描画
		self.set_child_box_area()
		self.draw()

	def maximize_window(self):
		"""
		スクリーンサーフェスの最大化を行います。
		また、すでに最大化状態なら、デフォルトの大きさにサーフェスをリサイズします。
		なお、実際には、このメソッドは、self.resize_windowへのブリッジの役割を果たします。
		"""
		#最大化されていない状態なら最大化
		if not self.maximized :
			self.resize_window((3000,3000))	#特定のWindowシステム上では自動でリサイズされるので動く
			self.maximized = True	#フラグを立てる
		else :
			self.resize_window()	#引数なしの呼び出しでデフォルトサイズにリサイズ
			self.maximized = False	#フラグを下ろす


	# 子Boxの描画領域に関するメソッド
	def set_child_box_area(self):
		"""
		(すべてのこのオブジェクトの子BOXオブジェクトに)描画領域の分配を行うメソッド
		まずself.calc_childbox_heightpercentage()メソッドを呼び出し、均等な分配のための値を算出し、その値を用いて、実際の設定を行う。

		描画領域についてのすべての情報は、個々の子BOXオブジェクトのメンバ変数に保持されている。
		具体的には、box._left_topと、box.height、box.widthの3つの変数である。つまり、このメソッドはこの情報を設定する。
		"""
		#基本値の取得
		display_height = self.screen.get_height()	#スクリーンサーフェス全体の大きさ
		display_width = self.screen.get_width()
		average_height_percentage , prefixed_height_sum = self.calc_childbox_heightpercentage()
		#算出に必要な値の算出
		height_for_dynamic_dividing = display_height - prefixed_height_sum	#動的に分割可能な高さ
		average_height_for_dividing = int (height_for_dynamic_dividing * (float(average_height_percentage) / 100))	#動的に分割される高さの値

		#すべての子ボックスオブジェクトに対して描画領域の設定
		left_top=(0,0)	#width,height
		for child_box in self.child_box_list :
			"""#Boxコンテナなら、内部の静的サイズ情報の算出
			if isinstance(child_box,Container_Box) :
				child_box.calc_size()
			"""
			#サイズ情報とleft_topの分配、設定を行う。
			if child_box.height_prefix :
				child_box.set_left_top((left_top[0],left_top[1]))
			else :
				#動的な高さの定義
				child_box.set_height(average_height_for_dividing)
				child_box.set_left_top(left_top)
			if child_box.width_prefix :
				raise Exception("未定義です")
			else :
				child_box.set_width(display_width)	#処理が必要になったらheight同様動的に分割

			left_top = (left_top[0],left_top[1]+child_box.get_height())

	def calc_childbox_heightpercentage(self):
		"""
		このメソッドは、このオブジェクトの有する、すべての動的高さを持つ子BOXオブジェクトに対して、均等な描画領域を提供するために、それぞれの動的な高さを持つBOXにディスプレイ全体の何％の高さを提供するべきかを算出するメソッドであり、また、その上で、静的な高さを有するBOXオブジェクトのその設定された高さの総和も同時に算出、この2つの値をreturnする。
		この2つの値は動的なサイズを有するBOXに適当な範囲を提供するために不可欠である。

		1: 動的な高さ(box.prefix=False)で設定されたBOXオブジェクトに対し、等分な描画領域を提供するするための、平均パーセンテージをreturnする。
		2: また、静的な高さを持ったBOXオブジェクト(self.prefix=True)に定義された高さ(self.height)の総和を返す。
		"""
		prefixed_height_sum = 0
		num_of_dynamicheight_childbox = 0
		for child_box in self.child_box_list :
			if child_box.height_prefix :
				prefixed_height_sum += child_box.get_height()
			else :
				num_of_dynamicheight_childbox += 1

		average_height_percentage = int(100 / (num_of_dynamicheight_childbox or 1))
		return average_height_percentage , prefixed_height_sum

	def get_collide_box(self,*pos):
		"""
		与えられたポジション(X,Y)に対してcollide判定された子BOXオブジェクトを返す
		いかなる子BOXオブジェクトもcollideに反応しなければ、Noneを返す。
		"""
		x , y = parse_coordinate(*pos)
		for child_box in self.get_children() :
			if child_box.collide_point((x,y)) :
				return child_box
		return None
	
	#描画に関するメソッド
	def update(self):
		"""
		このRootオブジェクト以下の構造を再評価して、Box描画領域の再分割、全体の再描画、を明示的に行う。
		このメソッドは、内部構造の変更後、常に呼び出してよい。
		内部構造情報から正確な諸値をー最新の値としてー再導出するだけだから、
		(古い情報が失われることと、その導出などに関するわずかなオーバーヘッド以外にはー)いかなる副作用もない。
		"""
		self.set_child_box_area()
		self.draw()

	def fill_background(self,rect=None):
		self.screen.fill(self.background_color,rect)
		pygame.display.update(rect)

	def draw(self):
		self.fill_background()
		for child_box in self.child_box_list:
			child_box.draw()

	def msec2numof_frame(msec):
		"""ミリ秒をフレーム数に変換"""
		if not isinstance(msec,int) :
			raise TypeError("引数が不正です")
		elif msec <= 100 :
			#0.1秒以下ならとりあえず最小フレーム数でせってい
			pending_frames = 1
		else :
			#引数msecとRootの設定Fps値から何フレーム後にコマンドを予約するか算出
			msec_per_frame = 1000 / msec.fps	#self.fpsから、一フレームあたりの消費ミリ秒(1/1000秒)の算出
			pending_frames = msec / msec_per_frame	#実行待ちフレーム数の算出
		return pending_frames

	#コマンドに関するメソッド
	def after(self,command,msec):
		"""
		msec後に定義されたコマンドを実行する。
		"""
		def generate_closed_object():
			"""フレーム数を格納するオブジェクトを生成"""
			attributes = {"pending_frames" : msec2numof_frame(msec)}	#残りフレーム数を格納する
			closed_object = type("Closed",(object,),attributes)
			return closed_object

		def generate_closer():
			"""クロージャーの生成"""
			closed_object = generate_closed_object()#クロージャーに内包されるクローズオブジェクト
			#クロージャー
			def update_pending_frame():
				"""残りフレームを１消費して、それが0ならTrueを返すクロージャー"""
				closed_object.pending_frames -= 1
				condition = True if closed_object.pending_frames == 0 else False
				return condition

			return update_pending_frame

		#残りフレーム数格納クロージャーの生成
		update_pending_frame = generate_closer()
		#コマンドの登録
		reserved_command = command_reserver.Reserved_Command(command,update_pending_frame)
		self.reserve_command(reserved_command)

		return reserved_command

	def mainloop():
		"""メインループ"""
		while self.looping :
			self.event_loop()
			self.resolve_command()
			self.clock.tick(self.fps)


class SubBox(
	BaseBox,
	contaiers.Contained,
	identifire.Identifire,
	):
	"""
	"""
	# 初期化処理
	def __init__(self,id_holder=None,boxid=None,):
		"""
		"""
		#引数チェック
		if box_id is not None :
			if not isinstance(id_holder,RootBox):
				raise TypeError("BOXオブジェクトのID情報の格納オブジェクトは、RootBoxでなければなりません。")
		#初期化
		BaseBox.__init__(self)
		identifire.Identifire.__init__(box_id,id_holder)	#IDの設定。Noneなら省略される
		self.init_attr()

	def init_attr(self):
		pass

	# 描画領域に関するメソッド
	def calc_height(self):
		"""
		動的な高さの算出を行うオプショナルメソッド。デフォルトでは何もしない。
		内部情報から動的にーRoot静的なー高さを算出することが期待される。
		"""
		pass

	def calc_width(self):
		"""
		動的な幅の算出を行うオプショナルメソッド。デフォルトでは何もしない。
		内部情報から動的にーRoot静的なー高さを算出することが期待される。
		"""
		pass

	# サーフェスに関するメソッド
	def get_surface(self,surface_size=None,bgcolor=BACKGROUND_COLOR):
		"""
		サーフェスを得る為のインターフェイス。
		サーフェスサイズは省略できる。省略した場合は、ルートコンテナによって設定されたBOXサイズ情報を参照し、そのBOXオブジェクトに与えられた描画領域そのものの大きさをもつサーフェスを返す。
		背景色は任意のものを設定可能で、デフォルトでは背景色BACKGROUND_COLORに設定されている。
		BOX単位での描画関数呼出をサポートするために背景の透過設定は許されていない。この場合ルートによる背景上書きが必要になるからである。
		"""
		surface = pygame.Surface(surface_size or self.get_size())
		surface.fill(bgcolor)
		return surface


#あまり
"""
	def update(self,surface) :
		"""新しいサーフェスを引数にとって、与えられた描画領域に再描画"""
		rect = self.get_rect()
		if rect.contains(surface.get_rect()) :
			self.get_display_surface().blit(surface,rect)
			pygame.display.update(rect)
		else :
			raise Exception("与えられたサーフェスがRootにより設定された絶対描画領域を超えます。")
class Root_Container:
	def get_focused_box(self):
		return self._focused_box
	
	def set_focused_box(self,box):
		"""
		フォーカスのあるBOXを設定するセッターメソッド
		"""
		#与えられた引数のBOXが、今のフォーカスBOXと違うならば、処理をする。
		if box is not self.get_focused_box() :
			self.prefocused_box = self.get_focused_box()
			self._focused_box = box
			self.synchronize_button_state()

	def synchronize_button_state(self):
		"""
		ボタン状態の同期を行う。実際の同期処理は、UI_Buttonクラスのインスタンスのcall_synchro_function()によって行われる。
		"""
		buttonbox = self.get_button_box("buttons_for_chart_setting")
		for button in buttonbox.get_all_buttons() :
			if isinstance(button,UI_Button) :
				#トグル可能なボタンなら
				button.call_synchro_function()
		buttonbox.draw()

	def get_all_container_box(self):
		box_list = []
		for box in self.child_box_list :
			if isinstance(box,Container_Box) and box.get_content() :
				box_list.append(box)
		return box_list
		
"""

if __name__ == "__main__" :
	print "This Module is not difined yet"



