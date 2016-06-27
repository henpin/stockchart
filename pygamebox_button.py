#! /usr/bin/python
# -*- coding: utf-8 -*-

import pygamebox

"""
PygameBoxのボタンコンテンツ実装。
"""

# PygameBox for Button Content
class Button_Box(pygamebox.SubBox):
	"""
	このBOXインターフェースは、UI_Buttonオブジェクトに対して、その描画領域と、イベントシグナルの提供を行うためのクラスです。
	"""
	#初期化処理
	def __init__(self,root,boxid=None,font=None,bgcolor=None):
		pygamebox.SubBox.__init__(self,root,Plural_Container,boxid)
		self.bgcolor = bgcolor or BACKGROUND_COLOR
		self.font = font or pygame.font.Font(FONT_NAME,14)
		self.set_size_prefix()
		self.init_attr()
		self.calc_height()

	def init_attr(self):
		"""属性値の初期化"""
		self.MARGINE = 3
		self.refresh_command = None

	def calc_height(self):
		"""高さの算出"""
		font_size = self.font.size("あ")
		self._height = font_size[1] + self.MARGINE * 2	#規定値によってデフォルトでは、静的な高さで生成される


	#Id
	def get_button(self,id):
		for button in self.button_list :
			if button.id == id :
				return button
		raise Exception("id,%s を持つBUttonオブジェクトはありません"%(id_str))


	#描画
	def draw(self,highlight=None):
		"""
		このオブジェクトの格納するすべてのボタンオブジェクトのdraw()関数を呼び出し、描画させます。
		すべての子ボタンオブジェクトはその描画にそのためのコンテキストが必要で、このメソッドはそれを引数を通して提供します。

		なお、このメソッドは引数にhighlightを取り得ます。この値は子オブジェクトとして登録されているButtonオブジェクトでなければなりません
		この定義時には、"その"オブジェクトのdraw()を呼ぶときにそのボタンをハイライト表示すべきことをやはり引数highlightで伝えます。
		なお、その引数値の利用のいかんについては、このオブジェクトは関知しません。
		"""
		if ( highlight is not None ) and ( highlight not in self.get_all_buttons() ) :
			raise TypeError("引数がこのオブジェクトの子ボタンオブジェクトでありません")

		rect = self.get_rect()
		surface = self.get_surface(bgcolor=self.bgcolor)
		left_top = (self.MARGINE,self.MARGINE)	#細かい見た目の設定と、BOXサーフェスに対する貼り付け位置
		#ボタンの描画
		for button in self.get_all_buttons() :
			#ハイライト表示に関する制御
			if highlight is button :
				button.draw(surface,left_top,self.font,highlight=True)
			else :
				button.draw(surface,left_top,self.font)
			#描画位置(左上)のシフト
			left_top = (left_top[0]+button._width+self.MARGINE,left_top[1])
		self.update(surface)


	#イベントプロセッシング
	def process_MOUSEBUTTONDOWN(self,event):
		if event.button == 1 :
			relative_pos = self.convert_pos_to_local(event.pos)	#Box相対座標
			for button in self :
				if button.collide_point(relative_pos):
					button.process_MOUSEBUTTONDOWN(event)
					self.draw()
					break
	
	def process_MOUSEMOTION(self,event):
		"""
		on_mouseイベントに対するバインドの呼び出しを行います。
		一般的に行われるべき処理はボタンのハイライト描画のための処理です。
		"""
		relative_pos = self.convert_pos_to_local(event.pos)	#BOX相対座標値へ変換
		for button in self :
			if button.collide_point(relative_pos) :
				button.process_MOUSEMOTION(event)
				#ボタンのハイライト描画に関するリフレッシュ処理。
				if self.refresh_command and self.refresh_command.is_cancelable() :
						#前に定義したリフレッシュ関数が未実行ならキャンセル
						self.get_father().cancel_command(self.refresh_command)
				self.refresh_command = self.get_father().after(500,self.draw)	#リフレッシュコマンドの呼び出し予約
				return

# Base-Classes for Button
class Base_Button(pygamebox.PygameBox_Content):
	"""
	"""
	def __init__(self,string,button_id):
		"""
		"""
		pygamebox.PygameBox_Content.__init__(self)
		self.string = unicode(" "+string+" ","utf-8")	#エンコードしとく
		self.button_id = button_id
	
	def collide_point(self,*pos):
		"""
		与えられた引数pos=(x,y)の表す地点がこのクラスを継承するオブジェクトの描画範囲に衝突しているか否かについての判定をするメソッド。真偽値を返す。
		"""
		x , y = parse_coordinate(*pos)
		left_top , width , height = self.get_size()
		if left_top[0] <= x <= width+left_top[0] and left_top[1]+height >= y >= left_top[1] :
			return True
		else :
			return False

	def set_size(self,left_top,width,height):
		"""
		このオブジェクトはButton_Boxオブジェクトから動的に設定された描画範囲についてのサイズ情報を有するが、そのセッターメソッドである。
		"""
		#エラー処理
		if not isinstance(left_top,tuple):
			raise Exception("引数が不正です")
		self._left_top = left_top
		self._width = width
		self._height = height

	def get_size(self):
		"""
		このオブジェクトに与えられた描画範囲情報についてのゲッターメソッド
		"""
		return self._left_top , self._width , self._height

	def process_MOUSEMOTION(self,event):
		"""
		このメソッドは一般的なすべてのボタンオブジェクトに共通するハイライト処理に関するステートメントを定義します

		このメソッドが呼ばれた時、親ボタンBOXをー自身をそのコンテキストの一部として渡してー再描画します
		親Boxはこのコンテキストを元に、そのオブジェクト(すなわち、この呼び出し元のオブジェクト自身)に、
		自身をハイライトして描画すべきであることをdraw()の引数ーコンテキストを通じて伝えます。
		"""
		self.get_parent_box().draw(highlight=self)


# Pygame Buttons
class Label_of_ButtonBox(Base_Button):
	"""
	Button_Boxオブジェクトに配置可能なラベルを表すコンテンツオブジェクト。
	多く、そのButton_Boxに設定されるボタンについての構造化された包括的なディスクリプションを表すのに用いられる。
	当然、イベント処理は不要で、即ちpassする。
	"""
	def __init__(self,string):
		Base_Button.__init__(self,string,None)	#IDは不要なので渡さない
		#以下の3つのプロパティはButton_Boxオブジェクトにより描画時、動的に与えられる。また、具体地は親のset_size()を用いる
		self._left_top , _width , _height= (0,0) , 0 , 0	

	def draw(self,target_surface,left_top,font):
		"""
		描画関数。親Button_Boxオブジェクトにより呼ばれる。
		ロジックの簡略化の為、ここでその描画領域を表す座標を算出し、set_size()メソッドにより内部に格納する。
		"""
		surface = font.render(self.string,True,(0,0,0),(255,255,255))
		surface.set_colorkey((255,255,255))	#Button_Boxの背景色と同化
		target_surface.blit(surface,left_top)
		#動的に決定される描画領域についての保存。
		w , h = surface.get_width() , surface.get_height()
		self.set_size(left_top,w,h)


class UI_Button(Base_Button):
	"""
	このアプリのユーザーインターフェースにおける"ボタン"を表すオブジェクト
	"""
	def __init__(self,string,button_id,command):
		Base_Button.__init__(self,string,button_id)
		self.command = command	#ボタンが押された時に起動する関数オブジェクト
		self.state = False	#押されているかいないか
		self.synchronize_with_focuse_content = None	#ボタンstate同期用の関数。self.set_synchro_function()で設定する。


	#描画
	def draw(self,target_surface,left_top,font,button_color=None,highlight=False):
		"""
		このメソッドの呼び出し元、すなわち、Button_Boxオブジェクトから提供される描画領域としてのサーフェスにボタンを描画する。
		また、この際決定されるボタンサイズ、親Button_Boxオブジェクトにおける座標位置、についての情報をset_zize()により納する。
		"""
		button_color = button_color or ( (255,0,0) if self.state else (255,255,255) )
		surface = font.render(self.string,True,(0,0,0),button_color)
		#枠線の描画。ハイライト表示として定義されている場合は枠線を目立つようにする
		surface = pygame.Surface.convert(surface)	#renderdの上にdrawするにはConvertする必要がある
		if highlight :
			pygame.draw.rect(surface,(100,100,255),surface.get_rect(),2)
		else :
			pygame.draw.rect(surface,(0,0,0),surface.get_rect(),1)

		target_surface.blit(surface,left_top)
		#動的に決定される描画領域についての保存。self.collideなどで用いられる。
		w , h = surface.get_width() , surface.get_height()
		self.set_size(left_top,w,h)


	#状態同期関数に関するメソッド
	def set_synchro_function(self,func):
		"""
		状態同期の為の関数の定義の為のインターフェイス。
		"""
		if not callable(func):
			raise TypeError("引数が不正です")
		self.synchronize_with_focuse_content = func

	def call_synchro_function(self):
		"""
		定義された状態同期の為の関数の呼び出し。
		未定義ならFalse値を返し、さもなくばシンクロ関数をコールし、また、その返り値のいかんに問わずTrue値を返す。
		"""
		if self.synchronize_with_focuse_content :
			self.synchronize_with_focuse_content(self)
			return True
		else :
			return False


	#状態に関する処理
	def set_state(self,state):
		self.state = state

	def get_state(self):
		return self.state

	def switch_state(self):
		"""
		ボタンの状態を変える-逆転させる。
		"""
		self.state = not self.state


	#イベントプロセッサ
	def process_MOUSEBUTTONDOWN(self,event):
		"""
		ボタンの状態を変える前に定義されたコマンドを実行し、そのコマンドが正常に実行されたら、ボタンの状態を変える。
		"""
		success = self.command(self) 
		if success :
			self.switch_state()
		self.get_parent_box().draw()


class No_Switch_Button(UI_Button):
	"""
	このオブジェクトはUI_Buttonの派生オブジェクトで、UI_Buttonオブジェクトと違い、「状態」の概念を持たないボタンです。
	つまり、ON,OFFの状態が付随しない、ファンクショナルなボタンを表現します。

	このオブジェクトはただ、イベントを処理するメソッドだけをオーバーライドします。
	"""
	def __init__(self,string,button_id,command):
		UI_Button.__init__(self,string,button_id,command)
		self.state = None	#このオブジェクトは状態を持たない

	def process_MOUSEBUTTONDOWN(self,event):
		"""
		このオブジェクトは状態を持たないので、ただ、ボタンが押された時には、規定のバインド関数を実行します。それ以上は何もしません。
		"""
		self.command(self)


class Toggle_Button(UI_Button):
	"""
	このボタンオブジェクトは、３つ以上の"状態"を持つボタンで、UI_Buttonを継承する。
	つまるところ、それに３つ以上の状態の概念をデコレイトするクラスである。

	このオブジェクトは３つ以上の「状態」を「状態のリスト」のそのindex値としてself.stateに格納する。
	「状態のリスト」とは、「状態を表す文字列のリスト」であって、これによってボタンプレスドコマンド関数は、今すべき処理を確定せしめるだろう。
	また、「状態（を表す文字列）」とは、実際にボタン上に表示される文字列でもある。
	実際の状態の変化に基づく、このオブジェクト内におけるデータの変化については、やはりこのオブジェクトのメソッドが請け負う。
	"""
	#初期化処理
	def __init__(self,states,button_id,command):
		"""
		"""
		if not isinstance(states,tuple) :
			raise TypeError("引数が不正です。")
		elif len(states) <= 2 :
			raise Exception("リストメンバ数が不十分です。")

		self.state = 0	#初期状態
		self.states = states
		initial_string = states[0]
		UI_Button.__init__(self,initial_string,button_id,command)


	#状態同期関数
	def call_synchro_function(self):
		"""
		定義されていれば、シンクロ関数をコールする。
		シンクロ関数が未定義ならば、チャートオブジェクトは複雑な「状態」について関知しない（予定）なので状態を初期化しちゃう。
		"""
		if self.synchronize_with_focuse_content :
			self.synchronize_with_focuse_content(self)
		else :
			self.initialize_state()
		return True


	#状態に関する処理
	def initialize_state(self):
		"""
		「状態」情報を完全に初期化する。
		また、フォーカスのあるチャートオブジェクトの状態もこの状態に同期する為にcommandを手放しで呼ぶ。
		"""
		self.string = self.get_state_str()
		self.command(self,initialize=True)

	def get_state_str(self,index=None):
		"""
		引数に与えられたindex値としてのstate値の表現する「状態」を、表現する文字列を返す。
		なお、index値は省略可能で、その時には、現在の「状態」を表す文字列を返す。
		"""
		if index is not None and 0 <= index < len(self.states) :
			return self.states[index]
		else :
			return self.states[self.state]

	def get_next_state(self):
		"""
		次の「状態」のstate値を返す。
		"""
		next_state = self.state + 1
		if next_state > len(self.states)-1 :
			next_state = 0
		return next_state

	def switch_state(self):
		"""
		このボタンの「状態」を変える。即ち、
		1,内部的な状態を格納するself.state属性値を変更する。
		2,ボタンの説明文字列self.string属性値を変更する。
		"""
		self.set_state( self.get_next_state() )
		self.string = self.get_state_str()	#「状態」を表すボタン上の文字列の更新

	#描画
	def draw(self,target_surface,left_top,font,button_color=None,highlight=False):
		"""
		UIボタンクラスのdrawメソッドは、状態により色を勝手に変更してしまうので、これを明示的に宣言する必要がある。
		"""
		color = (255,255,200)
		UI_Button.draw(self,target_surface,left_top,font,button_color=color,highlight=highlight)


if __name__ == '__main__':
	print "このモジュールはpygameboxのボタンコンテンツ実装です"

