#! /usr/bin/python
# -*- coding: utf-8 -*-

import eventer
import contaiers
import identifire

"""
pygameにおける描画領域の分割と、割り当て、さらには描画やイベントの伝搬までに関する広い範囲の枠組みとインターフェイスを提供するフロントエンドモジュール。

このモジュールによって規定されるすべての実装型は、Boxというコンテナ型のオブジェクトで、Root_Boxを最上位として、樹形の連鎖構造が組まれることになる。
イベントの伝搬や、描画領域の動的割り当ての機能は、この樹形構造を上から下へとメソッド呼び出しの伝搬が走り、その再帰的呼び出しによって、実装される。


このモジュールは、identifire,contaiers,eventerモジュールに依存する。

"""
# Globals
#Pygameのイベント名に対応するイベントプロセッサインターフェイスの生成
PYGAME_GLOBAL_EVENTNAMES = (
)#Pygameのイベント名
PYGAME_GLOBAL_EVENT_PROCESSOR = eventer.generate_event_processor(PYGAME_GLOBAL_EVENTNAMES)

#Classes
class BaseBox(
	PYGAME_GLOBAL_EVENT_PROCESSOR
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

	# 画面の更新に関するメソッド
	def draw(self):
		"""描画メソッド"""
		raise Exception("要オーバーライド")

	def update(self):
		"""描画して更新"""
		raise Exception("オーバーライド必須")


class RootBox(
	BaseBox,
	contaiers.Container_Of_Container,
	identifire.ID_Holder,
	):
	"""
	Boxオブジェクトによる構造の最上位に立つ唯一のオブジェクト。
	すべてのその子オブジェクトの描画領域および、そのID値の管理と利用に関する管理の立場にある。
	"""
	# 初期化メソッド
	def __init__(self):
		BaseBox.__init__(self)
		self.init_attr()

	def init_attr(self):
		"""
		"""
		self.screen = pygame.display.get_surface()
		self.background_color = BACKGROUND_COLOR
		self._focused_box = None	#操作の対象となっているコンテンツの直轄のBOX
		self.prefocused_box = None
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
	def convert_pos_to_local(self,*abs_pos):
		"""
		Root絶対座標値をこのBox内における相対座標(=BOXローカル座標値)へ変換する。
		なお、絶対座標値abs_posはこのBOXにCollideしていることを前提としている。

		多重チェックによるオーバーヘッドを嫌って、あえて引数チェクを行わない
		"""
		abs_pos = parse_coordinate(*abs_pos)
		left_top_onroot = self.get_left_top()
		relative_pos = ( (abs_pos[0] - left_top_onroot[0]) , (abs_pos[1] - left_top_onroot[1]) )
		return relative_pos

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


class Application(object):
	"""
	"""
	def main(self):
		self.init_attr()
		self.main_loop()

	def init_attr(self):
		"""インスタンスメンバ変数の初期化"""
		self.key_information = {}	#pygameから提供されるキーの定数と、その押され続けているフレーム数の辞書
		self.looping = True	#メインループのスイッチ
		self.clock = pygame.time.Clock()
		self.fps = 30
		self.reserved_commands = []	#self.afterによって予約された実行待ちコマンドのリスト

	def main_loop(self):
		"""
		このアプリのメインループ
		"""
		while self.looping:
			self.event_loop()
			self.execute_reserved_commands()
			self.clock.tick(self.fps)
		
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

	def event_loop(self):
		"""
		イベントを補足、処理する最上層のルーチンで、イベントの処理はpygameによって提供される２つの手段を両方用います。
		まず、全てのキーイベントに対しては、pygame.keyモジュールの枠組みを用います。これはpygame.eventではキーリピートを補足できない為です。
		一方、マウスイベントや、その他終了、リサイズイベントの処理についてはpygame.eventに提供されるイベントキューの枠組みを用います。
		ただし、イベントの処理に関する情報伝達インターフェイスの統一の為、「前者の枠組みにおいても」、能動的にイベントオブジェクトを発行し、これをdiispachする。
		"""
		def Process_event_on_keystate():
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
					focused_box = self.get_focused_box()
					focused_box.process_KEYDOWN(event)
			self.update_key_information(pressed_keys)

		def Process_event_on_queue():
			"""
			イベントキュー上の処理。
			pygame.eventにより提供されるイベントキューからイベントを取り出して処理する。
			"""
			for event in pygame.event.get():
				if event.type == pygame.QUIT or self.get_key_state(pygame.K_ESCAPE) :
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
		Process_event_on_keystate()
		Process_event_on_queue()

	def after(self,msec,command):
		"""
		Rootオブジェクトに関数の呼び出しを予約する
		引数にはint値ミリ秒msec,と呼び出し可能なcommandをとる。
		引数チェックのあと、予約コマンドリストに追加します

		なお、帰り値は新たに生成されたコマンドオブジェクトで、予約済みコマンドキャンセルメソッドself.cancel_commandはこれを引数にとります。
		"""
		#待機時間msecが100(=0.1秒)以上であり、commandがcallableか否か
		if not ( isinstance(msec,int) and ( msec is 0 or msec >= 100 ) ) or not callable(command) :
			raise TypeError("引数が不正です")

		if msec is 0 :
			#明示的にmsecに0が与えられたら、最小フレーム(=次フレーム)にコマンドを予約
			numof_waiting_frame = 1
		else :
			#引数msecとRootの設定Fps値から何フレーム後にコマンドを予約するか算出
			msec_per_frame = 1000 / self.fps	#self.fpsから、一フレームあたりの消費ミリ秒(1/1000秒)の算出
			numof_pending_frame = msec / msec_per_frame	#実行待ちフレーム数の算出

		#コマンドの登録
		reserved_command = self.Reserved_Command(numof_pending_frame,command)
		self.reserved_commands.append(reserved_command)

		return reserved_command

	def cancel_command(self,command):
		"""
		コマンドをキャンセルします。
		このメソッドは冗長なエラー送出を行います。
		このエラー送出を回避するには、その呼び出し元で、すべてのコマンドオブジェクトの有するis_cancelable()を呼び出して、取り消し可能かチェックすることです。
		"""
		if not isinstance(command,self.Reserved_Command) :
			raise TypeError("引数がCommandオブジェクトでありません")
		if command in self.reserved_commands :
			self.reserved_commands.remove(command)
		else :
			raise Exception("指定されたコマンドオブジェクトが予約済みコマンドリストに存在していません")

	def execute_reserved_commands(self):
		"""
		予約されたコマンドの残り消費フレームを更新して、それが無くなればコマンドを呼び出す
		"""
		for command in copy.copy(self.reserved_commands) :
			command.spend_frame()
			if command.remaining_frame <= 0 :
				command.call()
				self.reserved_commands.remove(command)

	class Reserved_Command:
		"""
		コマンド予約用の単純なユーザー定義型。
		"""
		def __init__(self,numof_pending_frame,command):
			if not ( numof_pending_frame >=2 and callable(command) ) :
				raise TypeError("引数が不正です")

			self.remaining_frame = numof_pending_frame	#残りフレーム数
			self.command = command
			self.cancelable = True	#取り消し可能か否か。単純な符号であり、必ずしも動作の完全性を保証しない。

		def is_cancelable(self):
			return self.cancelable

		def call(self):
			"""登録されたコマンドを呼び出す"""
			self.cancelable = False
			return self.command()

		def spend_frame(self,numof_frame=1):
			"""
			残りフレーム数を引数分だけ消費する。
			"""
			#冗長なエラーチェック
			if self.remaining_frame <= 0:
				raise Exception("すでに残り消費フレームはありません")

			self.remaining_frame -= numof_frame
			if self.remaining_frame < 0 :
				self.remaining_frame = 0



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



