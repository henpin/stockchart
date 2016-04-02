#! usr/bin/python
# -*- coding: utf-8 -*-

"""
株価チャートプログラム。
1,Tkinter を用いて各種設定を行ったり、株式コードの入力を受け付ける。
2,株価データダウンロードサイトk-db.comから株価のcsvをダウンロードし
3,Pygameを用いてチャートを描画する。

このプログラムは以下の6つのクラスによって成っています。
1,Root_Container:
	このアプリケーションのインターフェイスと描画、メインループ及びイベント処理、のすべてを司るクラス。
	すべての描画は、このクラスのdraw()メソッドが担い、具体的にはメンバ変数self.childlistに含まれるオブジェクトのdraw()関数によって実際の描画が行われる。
2,Container_Box:
	このクラスは、チャートの表示領域を提供するためのクラス。
	すべてのStock_Chartオブジェクトはこのクラスのインスタンスに関連付けられることによって、その表示領域を得、またイベントの補足、あるいは描画関数の呼び出しを受けることができる。
3,Stock_Chart:
	チャート。
4,Setting_Tk_Dialog:
	ユーザーに銘柄コードの入力と、チャートについての設定を求めるダイアログを表示し、また、その設定情報を保存しておくためのクラス。
5,UI_Button:
	ボタン
6,Button_Box:
	ボタンボックス
7,UI_Button_Label:
	
"""
import math,sys,urllib2,os.path
import pygame
from pygame.locals import *
import Tkinter as Tk
import tkMessageBox
from datetime import date as Date
from HTMLParser import HTMLParser

#STATICS-----
SCREEN_SIZE = (1000,600)
TERM_LIST = "月足,週足,日足,前場後場,5分足,1分足".split(",")	#数字は半角
TERM_DICT = dict( zip( (TERM_LIST+range(1,7)),(range(1,7)+TERM_LIST) ) )	#相互参照の列挙体としての辞書。 1:月足 2:週足 3:日足 4:前後場足 5:五分足 6:一分足
TERM2URL_DICT = {"日足":"","前場後場":"a","5分足":"5min","1分足":"minutely"} 
BUTTON_SIZE = (40,30)
FONT_NAME =  os.path.join(os.path.abspath(os.path.dirname(__file__)),"TakaoGothic.ttf") if os.path.isfile( os.path.join(os.path.abspath(os.path.dirname(__file__)),"TakaoGothic.ttf")) else None 
BOLD_FONT_NAME = os.path.join(os.path.abspath(os.path.dirname(__file__)),"BoldFont.ttf") if os.path.isfile( os.path.join(os.path.abspath(os.path.dirname(__file__)),"BoldFont.ttf")) else None 
#Changed by windows - ダウンロードモードと、サイト設定
DOWNLOAD_MODE_LOCAL = 1
DOWNLOAD_MODE_DIFF = 2
DOWNLOAD_MODE_DOWNLOAD = 3
DOWNLOAD_MODE_ETC = 4
DOWNLOAD_SITE_KDB = 10
DOWNLOAD_SITE_ETC = 100

#Globals------
DEBUG_MODE = 0
CSV_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)),"csv")


#Class-----
class BASE_BOX():
	"""
	BOXの基底クラス
	"""
	def get_rect(self):
		left_top = self.get_left_top()
		size = self.get_size()
		return pygame.Rect(left_top,size)

	def get_size(self):
		"""
		BOXサイズを表す(self.width,self.height)のタプルを返すだけ。
		"""
		return (self.width,self.height)

	def get_father(self):
		"""
		最大の親BOXオブジェクトである、Root_Containerオブジェクトを参照するための共通メソッド。
		すべてのRoot_Containerオブジェクト以外のBOXオブジェクトは、自分の直接の親BOXオブジェクトを返すが、最終的には必ずRoot_Containerのget_fatherメソッドがコールされ、これはそのRoot_Containerオブジェクト自身を返す。
		"""
		return self.get_parent().get_father()

	def collide_point(self,pos):
		"""
		"""
		x = pos[0]
		y = pos[1]
		my_width , my_height = self.get_size()
		my_left_top = self.get_left_top()
		if my_left_top[0] <= x <= my_width+my_left_top[0] and my_left_top[1]+my_height >= y >= my_left_top[1] :
			return True
		else :
			return False

	def get_label_box(self,id_str) :
		"""
		id_strで識別される、テキストの描画領域を提供するBOXオブジェクトを返します。
		"""
		return self.get_parent().get_label_box(id_str)

	def get_button_box(self,id_str) :
		"""
		"""
		return self.get_parent().get_button_box(id_str)

	def get_size(self):
		return (self._width , self._height)

	def get_height(self):
		return self._height

	def get_width(self):
		return self._width

	def get_left_top(self):
		return self._left_top

	def set_width(self,width):
		self._width = width

	def set_height(self,height):
		self._height = height

	def set_left_top(self,left_top):
		self._left_top = left_top

	def set_parent(self,parent):
		self._parent = parent

	def get_parent(self):
		return self._parent


class Root_Container():
	"""
	このアプリケーションのインターフェイスと描画、メインループ及びイベント処理、のすべてを司るクラスです。

	1,このクラスのインスタンスが生成されると、スクリーンサーフェスが生成されます。
	2,続いて、初期化メソッド内において、Setting_Tk_Dialog()オブジェクトが生成され、ユーザーは銘柄コードの入力を求められます。
	3,ユーザーが銘柄コードの入力及び、チャートについての設定を終えると、Setting_Tk_Dialog()オブジェクトの生成が完全に終了し、それと同時にこのインスタンスの生成(つまり、その初期化処理)も終了します。
	4,main_loop()が呼ばれると、イベントの受付状態に入ります。
	5,チャート表示状態におけるすべてのイベントは、event_loop()メソッドにより補足され、イベントの種類に応じて描画関数を呼び出します。

	:描画について	すべての描画は、このクラスのdraw()メソッドが担い、具体的にはメンバ変数self.child_box_listに含まれるオブジェクトのdraw()関数が間接的に呼ばれることで、実際の描画が行われます。

	"""
	def __init__(self):
		#インスタンス変数
		self.screen = pygame.display.get_surface()
		self.background = (255,255,255)
		self.keys = pygame.key.get_pressed()	#キー入力の保存リスト、eventloop()で更新。
		self.looping = True	#メインループのスイッチ
		self.clock = pygame.time.Clock()
		self.fps = 10
		self.child_box_list = []	#すべてのGUI要素を含むリスト
		self._focused_box = None	#操作の対象となっているコンテンツの直轄のBOX
		self.prefocused_box = None
		event_dict = {"from":self}
		self.dummy_event = pygame.event.Event(pygame.USEREVENT,event_dict)	#ダミーのイベントオブジェクト
		#イベント用定数
		self.keys_control_chart = (pygame.K_LEFT,pygame.K_RIGHT,pygame.K_UP,pygame.K_DOWN)

		#初期化処理
		self.fill_background()
		add_default_buttons(self)	#デフォルトのボタンを配置
		add_default_labels(self)	#デフォルトラベルの配置
		#設定画面の呼び出し
		Setting_Tk_Dialog(self).initial_chart_setting()	
	
	def add_box(self,child):
		"""
		このオブジェクトに新たなBOXオブジェクトを、子BOXとして登録します。
		登録後、各BOXオブジェクトに割り当てる描画領域を更新します。
		"""
		if isinstance(child,BASE_BOX):
			if isinstance(child,Container_Box):
				self.set_focused_box(child)
			self.child_box_list.append(child)
			self.set_child_box_area()
			self.draw()
		else:
			raise TypeError("不正なオブジェクト型の代入です。")

	def remove_box(self,child_box):
		"""
		"""
		if len(self.get_all_container_box()) == 1:
			print "唯一の要素です"
			return False
		else :
			if child_box == self.get_focused_box() :
				self.set_focused_box(self.prefocused_box)
			elif child_box == self.prefocused_box :
				self.prefocused_box = None
			self.child_box_list.remove(child_box)
			self.set_child_box_area()
			self.draw()
			return True

	def set_child_box_area(self):
		"""
		(すべてのこのオブジェクトの子BOXオブジェクトに)描画領域の分配を行うメソッドで、まずself.calc_childbox_heightpercentage()メソッドを呼び出し、均等な分配のための値を算出し、その値を用いて、実際の設定を行う。

		描画領域についてのすべての情報は、個々の子BOXオブジェクトのメンバ変数に保持されている。具体的には、box._left_topと、box.height、box.widthの3つの変数である。つまり、このメソッドはこの情報を設定する。
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
			#動的な高さ、あるいは幅で定義された子BOXならば、高さ、幅の設定を行う
			if child_box.width_prefix == False:
				child_box.set_width(display_width)	#処理が必要になったらheight同様動的に分割
				child_box.set_left_top((left_top[0],left_top[1]))
			if child_box.height_prefix == False :
				child_box.set_height(average_height_for_dividing)
				child_box.set_left_top(left_top)

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
			if child_box.height_prefix == True :
				prefixed_height_sum += child_box.get_height()
			else:
				num_of_dynamicheight_childbox += 1
		average_height_percentage = int(100 / (num_of_dynamicheight_childbox or 1))
		return average_height_percentage , prefixed_height_sum

	def get_father(self):
		return self

	def get_label_box(self,id_str):
		for box in self.child_box_list :
			if isinstance(box,Label_box) and box.id_str == id_str :
				return box
		raise Exception("識別子",id_str,"を持ったLabel_boxオブジェクトは見つかりませんでした。")

	def get_focused_box(self):
		return self._focused_box
	
	def set_focused_box(self,box):
		"""
		フォーカスのあるBOXを設定するセッターメソッド
		"""
		#与えられた引数のBOXが、今のフォーカスBOXと違うならば、処理をする。
		if box != self.get_focused_box() :
			self.prefocused_box = self.get_focused_box()
			self._focused_box = box
#			self.dispatch_button_symchro_event()

	def dispatch_button_symchro_event(self):
		"""
		フォーカス移動時、コンテンツの設定内容をボタンに共有する。
		ダミーイベントに共有する状態を付与して目的のボタンのあるボタンBOXにそのユーザー定義のイベントを流して、目的のボタンに情報を共有する
		"""
		id_str = "synchronous"
		target_button_box = self.get_button_box(id_str)
		focused_content = self.get_focused_box().get_content()
		#Y軸固定オプション値についてのシンクロ
		dummy.target_id = "Y-prefix"
		dummy.state = focused_content.get_Y_axis_fixed()
		target_button_box.dispatch_synchro_event()
		#etc
		raise Exception("使うかどうか未定")

	def get_all_container_box(self):
		box_list = []
		for box in self.child_box_list :
			if isinstance(box,Container_Box) and box.get_content() :
				box_list.append(box)
		return box_list

	def get_button_box(self,id_str):
		for box in self.child_box_list :
			if isinstance(box,Button_Box) and box.id_str == id_str :
				return box
		raise Exception("識別子",id_str,"を持ったButton_boxオブジェクトは見つかりませんでした。")

	def fill_background(self):
		self.screen.fill(self.background)
		pygame.display.update()

	def draw(self):
		for child_box in self.child_box_list:
			child_box.draw()

	def event_loop(self):
		"""
		イベントを補足します。ルートにおける一般的なキー入力については即時性が必要ないので、pygame.Key.get_pressedを用います。
		それ以外はイベントキューを用います。
		"""
		#Changed_by_Win - リサイズ時イベントが処理されないバグの修正。fps値の変更
		#一般のルート側でのキー処理
		self.keys = pygame.key.get_pressed()
		#イベントキュー上の処理
		num_of_processed_MM = 0	#MouseMotionのイベント数を管理する。多すぎてdraw()呼ばれまくりで重くなるため。
		for event in pygame.event.get():
			if event.type == pygame.QUIT or self.keys[pygame.K_ESCAPE] :
				self.looping = False	#停止。
			elif event.type == pygame.MOUSEBUTTONDOWN :
				self.fps = 30	#滑らかに動かす
				for child_box in self.child_box_list :
					if child_box.collide_point(event.pos) :
						child_box.dispatch_MOUSEBUTTONDOWN(event)
						break
			elif event.type == pygame.MOUSEBUTTONUP :
				self.fps = 4	#プロセッサ時間の節約
			elif event.type == pygame.VIDEORESIZE :
				self.screen = pygame.display.set_mode(event.size,pygame.VIDEORESIZE)
				self.set_child_box_area()
				self.draw()
			elif event.type == pygame.MOUSEMOTION :
				#イベント数を３分の１にする
				num_of_processed_MM += 1
				if (num_of_processed_MM % 2 == 0) or (num_of_processed_MM % 5 == 0) or (num_of_processed_MM % 7 == 0) or (num_of_processed_MM % 9 ) == 0 :
					continue
				if event.buttons[0] :
					for child_box in self.child_box_list :
						if child_box.collide_point(event.pos) :
							child_box.dispatch_MOUSEDRAG(event)
							break
			elif event.type == pygame.KEYDOWN and event.key in self.keys_control_chart :
				focused_box = self.get_focused_box()
				focused_box.dispatch_KEYDOWN(event)

	def main_loop(self):
		"""
		このアプリのメインループ
		"""
		while self.looping:
			self.event_loop()
			self.clock.tick(self.fps)


class Label_box(BASE_BOX):
	"""
	文字情報の描画を行うLabelオブジェクトにその描画領域を提供するオブジェクトで、また、その実際の描画命令も、このオブジェクトのdraw()メソッドから間接的に呼ばれることになる。
	このオブジェクトに必要な高さ(確保しなくてはならない描画領域)は、このオブジェクトの有する子ラベルオブジェクトにより一意に決まり、これはset_own_height()メソッドにより動的に算出、設定される。
	"""
	def __init__(self,parent,id_str=None) :
		self._parent = parent	#逆参照に使う
		self.label_list = []	#子ラベルのリスト
		self.id_str = id_str or "General"	#このオブジェクトの参照に用いられるID値
		self.height_prefix = True	#このオブジェクトはデフォルトで静的な高さを有する。
		self.width_prefix = False
		self._left_top = (0,0)	#Root_Containerオブジェクトによって動的に決定されます。
		self._width = 0
		self._height = 0

	def add_label(self,label) :
		if not isinstance(label,Label) :
			raise TypeError("不正な型のオブジェクトのaddです。: ")
		self.label_list.append(label)
		self.set_own_height()	#このオブジェクトのheightを再設定
	
	def remove_label(self,label) :
		self.label_list.remove(label)
		self.set_own_height()	#このオブジェクトのheightを再設定

	def set_own_height(self) :
		"""
		このオブジェクトのself.heightを子ラベルから動的に生成します。
		このメソッドは、このオブジェクトの描画領域を一意に決定せしめる点で重要です。
		"""
		height_sum = 0
		for label in self.label_list :
			height_sum += label.height
		self._height = height_sum
		self.get_father().set_child_box_area()	#Root_Containerオブジェクトに描画領域を再分配してもらう
	
	def draw(self) :
		"""
		このオブジェクトの含むすべての子labelについて描画メソッドdraw()を呼びます。
		"""
		left_top = self.get_left_top()
		for label in self.label_list :
			surface = pygame.Surface(self.get_size())
			surface.fill((255,255,255))
			label.draw(surface)
			self.get_father().screen.blit(surface,left_top)
			left_top = (left_top[0],left_top[1]+label.height)
		pygame.display.update(self.get_rect())

	def dispatch_MOUSEMOTION(self,event) :
		pass

	def dispatch_MOUSEBUTTONDOWN(self,event) :
		pass

	def dispatch_MOUSEDRAG(self,event):
		pass


class Label(object):
	"""
	文字列の描画を行うオブジェクトです。
	1,描画される文字列self.stringの設定を行う。
	2,描画に必要な範囲をフォントサイズから算出し、self.heightに格納
	3,描画
	"""
	def __init__(self,string=None,color=None,font=None) :
		self.font = font or pygame.font.Font(FONT_NAME,16)	#文字の描画に用いられるフォント
		self.initial_string = "セッティングにはKEYを押してください。"	#文字列非設定時のデフォルト値
		self.color = color or (0,0,0)
		self.string = string or self.initial_string	#実際に描画される文字列
		self.height = 0	#フォントサイズから動的に決定される
		self.MARGINE = 1
		self.set_own_height()	#self.heightの動的な算出

	def set_own_height(self) :
		"""
		フォントサイズからその描画に必要な高さを動的に算出し、self.heightに格納する。
		"""
		self.height = self.font.size(self.string)[1] + self.MARGINE * 2

	def set_string(self,string=None) :
		self.string = string or self.initial_string
		self.set_own_height()

	def draw(self,surface) :
		"""
		"""
		decoded = unicode(self.string,"utf-8")	#日本語の貼り付けにはデコードが必要。
		text_surface = self.font.render(decoded,True,self.color)
		surface.blit(text_surface,(20,self.MARGINE))

	def dispatch_MOUSEMOTION(self,event) :
		pass


class Container_Box(BASE_BOX):
	"""
	このクラスは、チャートの表示領域を主に、Stock_Chartオブジェクトに対して提供するためのもので、すべてのチャート情報を保持するオブジェクトはこのクラスのインスタンスに関連付けられることによって、その表示領域を得、またイベントの補足、あるいは描画関数の呼び出しを受けることができます。
	また、このオブジェクトを有効に、つまり実際に描画領域の確保とイベントの受付を行うためには、このオブジェクトを、Root_Containerオブジェクトに登録する必要があります。

	コンテンツ : このクラスはただ1つの、Stock_Chartオブジェクトをはじめとする株価データを保持するオブジェクトを、その「コンテンツ」として有し、そのチャートオブジェクトに対して描画領域を提供します。
	"""
	def __init__(self,parent,content=None,font=None) :
		self.set_parent(parent)
		if content :
			self.set_content(content)
		self.child_box_list = None	#拡張性のため子BOXを考えている。ただし、コンテンツとの共存は考えていない。
		self.font = font or pygame.font.Font(FONT_NAME,15)
		self.bold_font = pygame.font.Font(BOLD_FONT_NAME,15)
		self.height_prefix = False	#動的な大きさか静的な大きさか。デフォルトは前者。
		self.width_prefix = False
		self._width = 0
		self._height = 0		
		self._left_top = (0,0)	#この値はRoot_Containerオブジェクトによってのみ設定可能

	def get_left_top_on_root(self):
		"""
		ルートウィンドウにおけるこのBOXのX,ｙの位置。
		"""
		return self._left_top

	def set_content(self,content) :
		self._content = content
		content.set_parent_box(self)

	def get_content(self):
		return self._content

	def draw(self):
		"""
		コンテンツの描画を行います。
		1,まず、Root_Containerから与えられた描画領域に準じて、surfaceを生成します。
		2,このサーフェスをコンテンツのdraw()メソッドに渡してそこにコンテンツを描画させます。
		3,最後に描画されたサーフェスをXを軸として、Y方向に逆転させます。
		  これはpygameの座標が左上を原点とするためで、つまり、「より大きい」値は、より、視覚的に小さい方（=「より下」）を表すので、つまり、例えば、高値(＝上)と安値（＝下）が高々「視覚的に」全く逆転してしまいます。これを「小さい値」は「下」を、より「大きい値」はより「上」を、座標上においてもー視覚的に、表すように、座標を完全に逆転させる必要があります。
		assigned_index引数は、足についての詳細な情報を表示する場合に、その対象となるローソク足を示すself.content.stock_price_listのインデックス値である。
		"""
		rect_on_root = self.get_rect()
		surface = pygame.Surface(self.get_size())
		surface.fill((255,255,255))
		if self.get_father().get_focused_box() == self:
			rect_for_self = pygame.Rect((0,0),rect_on_root.size)
			pygame.draw.rect(surface,(255,200,40),rect_for_self,5)
		self.get_content().draw(surface,self.font,self.bold_font)
		self.get_father().screen.blit(surface,rect_on_root)
		pygame.display.update(rect_on_root)

	def dispatch_MOUSEBUTTONDOWN(self,event):
		#フォーカスの変更
		focused = self.get_father().get_focused_box()	#クリック前のフォーカスBOX
		if focused != self:
			self.get_father().set_focused_box(self)	#フォーカスBOXの変更
			focused.draw()	#フォーカスされていたBOXを再描画(フォーカス表示の解除のため)
		#コンテンツにイベント処理を伝搬
		self.get_content().dispatch_MOUSEBUTTONDOWN(event)

	def dispatch_MOUSEMOTION(self,event):
		self.get_content().dispatch_MOUSEMOTION(event)

	def dispatch_MOUSEDRAG(self,event):
		self.get_content().dispatch_MOUSEDRAG(event)
		self.draw()

	def dispatch_KEYDOWN(self,event):
		self.get_content().dispatch_KEYDOWN(event)
		self.draw()


class Button_Box(BASE_BOX):
	"""
	このBOXインターフェースは、UI_Buttonオブジェクトに対して、その描画領域と、イベントシグナルの提供を行うためのクラスです。
	実際に、このオブジェクトがイベントシグナルを受け取ったり、描画命令を受けるためには、このオブジェクトがRoot_Containerオブジェクトに関連付けられている(その子BOXである)必要があります。
	このBOXオブジェクトがイベントシグナルないし描画の呼び出しを受けたときは、このオブジェクトの有するボタンオブジェクト、すなわち、self.button_listリストに登録されているすべてのUI_Buttonオブジェクトの、draw()メソッドをそれぞれ呼び出し、実際に描画します。
	"""
	#Changed_by_Win 色の設定
	def __init__(self,parent,id_str,font=None,color=None):
		self.BG_color = color or (255,255,255)
		self.set_parent(parent)
		self.button_list = []
		self.font = font or pygame.font.Font(FONT_NAME,17)
		self.id_str = id_str
		self.height_prefix = True
		self.width_prefix = False
		self._width = 0		#拡張用
		font_size = self.font.size("あ")
		self.MARGINE = 3
		self._height = font_size[1] + self.MARGINE * 2	#規定値によってデフォルトでは、静的な高さで生成される
		self._left_top = (0,0)	#この値はRoot_Containerオブジェクトによってのみ設定可能
	
	def add_button(self,button_object):
		#Changed_by_Win isintanceの修正
		if isinstance(button_object,(UI_Button,Label_For_ButtonBox)):
			self.button_list.append(button_object)
			button_object.set_parent_box(self)
		else:
			raise TypeError("不正なオブジェクトの代入です。")

	def get_button(self,id):
		for button in self.button_list :
			if button.id == id :
				return button
		raise Exception("id,%s を持つBUttonオブジェクトはありません"%(id_str))

	def draw(self):
		"""
		"""
		rect = self.get_rect()
		surface = pygame.Surface(self.get_size())
		surface.fill(self.BG_color)
		left_top = (self.MARGINE,self.MARGINE)	#細かい見た目の設定と、BOXサーフェスに対する貼り付け位置
		#ボタンの描画
		for button in self.button_list:
			button.draw(surface,left_top,self.font)
			left_top = (left_top[0]+button._width+self.MARGINE,left_top[1])
		self.get_father().screen.blit(surface,rect)
		pygame.display.update(rect)	

	def dispatch_MOUSEBUTTONDOWN(self,event):
		if event.button == 1 :
			my_left_top = self.get_left_top()
			x = event.pos[0] - my_left_top[0]
			y = event.pos[1] - my_left_top[1]
			for button in self.button_list :
				if button.collide_point((x,y)):
					button.dispatch_MOUSEBUTTONDOWN(event)
					self.draw()
					break
	
	def dispatch_MOUSEMOTION(self,event):
		pass

	def dispatch_MOUSEDRAG(self,event):
		pass


class Content(object):
	"""
	コンテンツの基底クラス
	"""
	def __init__(self):
		self._parent_box = None

	def get_parent_box(self):
		return self._parent_box
	
	def set_parent_box(self,parent):
		self._parent_box = parent
	
#Changed By Windows - ボタンBOX用のラベルオブジェクト。UI_BUTTOnのサイズについてのインターフェイスの必要性。
class Label_For_ButtonBox(Content):
	"""
	"""
	def __init__(self,string):
		Content.__init__(self)
		self.string = unicode(" "+string+" ","utf-8")
		self.button_color = (255,255,255)
		self._left_top =(0,0)
		self._width = 0
		self._height = 0
		self.id=None

	#Changed_by_Win widthなどの情報はButton_boxの描画メソッド内でも使う。また、surfaceにはカラーキーの設定
	def draw(self,target_surface,left_top,font):
		"""
		UI_Buttonのまね
		"""
		surface = font.render(self.string,True,(0,0,0),self.button_color)
		surface.set_colorkey((255,255,255))
		target_surface.blit(surface,left_top)
		#動的に決定される描画領域についての保存。多くイベントのdispatchで用いられる。
		self._width = surface.get_width()
		self._height = surface.get_height()
		self._left_top = left_top

	def collide_point(self,pos):
		"""
		イベント処理は不要
		"""
		pass

class UI_Button(Content):
	"""
	このアプリのユーザーインターフェースにおける"ボタン"を表すオブジェクトで、このオブジェクトは、Root_Containerオブジェクトに関連付けられた(ーつまり、その子BOXである)Button_Boxオブジェクトに関連付けられることにより、Root_Containerからのイベントの補足(シグナル)、及び描画(関数)の呼び出しを受けることができる。
	"""
	def __init__(self,string,id_str,command):
		Content.__init__(self)
		self.string = unicode(" "+string+" ","utf-8")
		self.id = id_str	#ボタンを識別するためのID文字列。外部との接続に必要
		self.command = command	#ボタンが押された時に起動する関数オブジェクト
		self.state = False	#押されているかいないか
		self._left_top = (0,0)	#以下3つのプロパティはButton_Boxオブジェクトにより描画時、動的に与えられる。
		self._width = 0
		self._height = 0

	def draw(self,target_surface,left_top,font):
		"""
		このメソッドの呼び出し元、すなわち、Button_Boxオブジェクトから提供される描画領域としてのサーフェスにボタンを描画する。
		また、この際決定されるボタンサイズ、親Button_Boxオブジェクトにおける座標位置、についての情報をメンバ変数として格納する。
		"""
		button_color =  (255,0,0) if self.state else (255,255,255)
		surface = font.render(self.string,True,(0,0,0),button_color)
		pygame.draw.rect(surface,(0,0,0),surface.get_rect(),1)
		target_surface.blit(surface,left_top)
		#動的に決定される描画領域についての保存。多くイベントのdispatchで用いられる。
		self._width = surface.get_width()
		self._height = surface.get_height()
		self._left_top = left_top

	def collide_point(self,pos):
		x = pos[0]
		y = pos[1]
		if self._left_top[0] <= x <= self._width+self._left_top[0] and self._left_top[1]+self._height >= y >= self._left_top[1] :
			return True
		else :
			return False

	def dispatch_MOUSEBUTTONDOWN(self,event):
		"""
		ボタンの状態を変える前に定義されたコマンドを実行し、そのコマンドが正常に実行されたら、ボタンの状態を変える。
		"""
		if event.type == pygame.USEREVENT : 
			#ボタンの状態を変更
			self.state = not self.state
		else : 
			success = self.command(self) 
			if success :
				self.state = not self.state
		self.get_parent_box().draw()


class No_Swith_Button(UI_Button):
	"""
	このオブジェクトはUI_Buttonの派生オブジェクトで、UI_Buttonオブジェクトと違い、「状態」の概念を持たないボタンです。
	つまり、ON,OFFの状態が付随しない、ファンクショナルなボタンを表現します。

	このオブジェクトはただ、イベントを処理するメソッドだけをオーバーライドします。
	"""
	def __init__(self,string,id_str,command):
		UI_Button.__init__(self,string,id_str,command)
		self.state = None	#このオブジェクトは状態を持たない

	def dispatch_MOUSEBUTTONDOWN(self,event):
		"""
		このオブジェクトは状態を持たないので、ただ、ボタンが押された時には、規定のバインド関数を実行します。それ以上は何もしません。
		"""
		self.command(self)


class Tab(object):
	"""
	このオブジェクトは、コンテナボックスをまたいで、コンテンツをまとめるためのオブジェクトで、同じタブを有するコンテンツは、内部で同じデータを共有する。

	また、GUIにおけるTAB機能も提供する。
	"""
	def __init__(self):
		self.data_dict = {}

	def get_data_list(self):
		return self.data_dict.keys()
	
	def get_data(self,key):
		if self.data_dict.has_key(key):
			return self.data_dict[key]
		else :
			raise Exception("Tabにそのデータは保管されていません。チェックはdata_in_tab()を使ってください")

	def set_data(self,data_id,data):
		self.data_dict[data_id] = data

	def data_in_tab(self,data):
		"""
		指定のデータが保存されいるかどうかを確認するためのメソッドです
		"""
		if self.data_dict.has_key(data) :
			return True
		else :
			return False

class Horizontal_Ruler(object):
	"""
	Stock_Chartオブジェクトにおいて用いられる水平バーを表現するオブジェクト。
	"""
	def __init__(self,chart,price,color):
		"""
		"""
		if not isinstance(chart,Stock_Chart) :
			raise Exception("不正な型です")
		self.chart = chart	#親となるチャート
		self.price = price
		self.color = color
		self._drawing_rect = None	#描画範囲を表現するRectで、描画時設定される。インターフェイスを用いてアクセスする。

	def draw_to_surface(self,surface,font) :
		"""
		水平ルーラーを描画するメソッド。
		引数として与えられたサーフェスに直接描画する
		このメソッドの呼び出し元は、このメソッド終了後、サーフェスをY軸方向にフリップするのでテキストは予めフリップしておく必要がある
		"""
		drawing_height = self.chart.price_to_height(self.price)
		price_renderd = font.render(unicode(str(self.price),"utf-8"),True,(0,0,0))
		flipped = pygame.transform.flip(price_renderd,False,True)
		drawing_price_renderd_H = drawing_height - (price_renderd.get_height()/2)
		drawing_rect = pygame.Rect((0,drawing_price_renderd_H),price_renderd.get_size())
		self.set_drawing_rect(drawing_rect,surface.get_height())	#描画範囲の保存

		pygame.draw.line(surface,self.color,(0,drawing_height),(surface.get_width(),drawing_height),2)
		pygame.draw.rect(surface,self.color,drawing_rect,0)
		surface.blit(flipped,(0,drawing_price_renderd_H))

	def set_drawing_rect(self,rect,surface_height):
		"""
		描画範囲を保存しておく為のメソッド。
		実際に描画されるサーフェスは、フリップされたものなので、それに適合させるための変換処理を行う
		"""
		if not isinstance(rect,pygame.Rect) :
			raise Exception("不正な型です")

		left_top = (0,surface_height - rect.bottomleft[1])
		transformed_rect = pygame.Rect((left_top),rect.size)
		self._drawing_rect = transformed_rect

	def get_drawing_rect(self):
		"""
		描画範囲を表すrectを返す
		親チャートオブジェクトのイベント処理において衝突判定のために用いられる
		"""
		return self._drawing_rect

	def set_price(self,price):
		self.price = price

	def collide(self,pos):
		"""
		与えられたposと衝突しているか否かを返す
		"""
		rect = self.get_drawing_rect()
		if rect.collidepoint(pos) :
			return True
		else :
			return False

class Moving_Average(object):
	"""
	移動平均についてのデータの算出と描画を担当するオブジェクトで、それを定義するためのいくつかのプロパティを有する。
	"""
	def __init__(self,parent,days,price_type,color):
		"""
		"""
		self.parent = parent	#親のStock_Chartオブジェクト
		self.days = days	#移動平均日数
		self.price_type = price_type	#終値その他の価格タイプを表す文字列"C","H"他
		self.color = color	
		self.point_list = []	#描画する点の座標値のリスト
		self.least_days = round( self.days * 2/3 )	#指定日数の3/2以上のデータ数が確保できれば許容

	def calc(self,start_index,end_index):
		"""
		移動平均値を算出し、描画する
		"""
		self.point_list = []	#初期化
		price_list = self.parent.stock_price_list
		target_price_type = self.parent.pricetype2index(self.price_type)
		#左端から移動平均線を描画する為に算出範囲を広げる。->start_indexをいじる
		if start_index >= self.days :
			start_index -= self.days
		for index in range(start_index,end_index+1) :
			if index - start_index < self.days :
				continue
			else :
				moving_prices = []	#X日間の指定の価格データの一時保管リスト
				Xdays_ago = index - self.days
				for MA_index in range(index,Xdays_ago,-1) :
					price = price_list[MA_index][target_price_type]
					if price :	#株価データがないときはパス
						moving_prices.append(price)
				#該当期間にある程度以上価格情報があれば
				if len(moving_prices) >= self.least_days :
					price_sum = 0
					for price in moving_prices :
						price_sum += price

					moving_average = round(float (price_sum) / len(moving_prices))
					#indexと移動平均価格値から、描画する座標値に変換
					pos_x = self.parent.get_index2pos_x(index)	#x値はローソク足描画時にindexに対して定義された値
					pos_y = self.parent.price_to_height(moving_average)	#y値は価格を高さに変換した値
					self.point_list.append((pos_x,pos_y))

	def draw_to_surface(self,surface):
		"""
		self.calc()で算出された座標値にもとづいて与えられたサーフェスに直接描画する
		"""
		pygame.draw.aalines(surface,self.color,False,self.point_list)
				

class Stock_Chart(Content):
	"""
	# 基本概要 #
	このオブジェクトは、実際の株価データを含む、株価チャートについてのすべての情報を有し、また、チャート描画についてのすべての、直接的な描画命令のセットを有するオブジェクトです。
	このオブジェクトは、銘柄コードを表す4桁の数字(security_code)と、そのチャートの表示する足期間を表すint値(term_num)を初期化処理のための引数としてとり、そこから動的にそれに必要とされる株価データをフェッチするためのURLを自動生成し、「外部から」self.download_price_data()メソッドが呼ばれた時その時に、実際の株価データのフェッチ、あるいはその正規化(convert)と、保存を行う。

	# Tab #
	また、このクラスに関連を持つクラスとして、Tabがある。
	これは2つ以上の株価チャート、すなわちデータ構造上のStock_Chartクラスのオブジェクトのデータを共有するためのインターフェイスで、これはself.set_tab()によってオプショナルに設定される。

	# Stock_price_list #
	株価データリストのコレクションとしての配列、stock_price_listは、[日時,始値,高値,安値,終値,出来高,金額]の順のそれぞれの値を表す文字列のリストのリストであり、また、これは「昇順」、つまり、「index=0が、一番古いデータ」を表す形で格納される。つまり、例えば、最新の株価の高値を参照する式は、stock_price_list[len(stock_price_list)][2]となる。
	なお、この「価格の種類」と「インデックス値」の変換にはユーティリティ関数self.pricetype2index()が用いられるべきである。これは価格の種類を表す文字列、「"O","H","L","C"」を引数に渡すと、それに対応するindex値を返す。
	"""
	#Changed_by_Windows ダウンロードサイトの保存
	def __init__(self,security_code,term_num,download_mode,site=DOWNLOAD_SITE_ETC):
		"""
		"""
		#株価情報についてのメンバ変数
		Content.__init__(self)
		self.stock_price_list = []	#ダウンロードされた株価情報。fetch_csv()メソッドにより入力
		self.security_code = security_code	#証券コード文字列
		security_name = ""	#証券名。CSVのフェッチと保存の際に設定される
		self.term_for_a_bar = None	#５分足、１０分足、日足、週足、月足のいずれの情報か
		self.term_for_csv = None	#週足、月足、は日足CSVデータから算出するため、CSVファイルの実態は日足データとなる

		#定められたインターフェイスによってのみ扱われるべき変数
		#チャート描画に関するメンバ変数
		self._zoom_scale = 1 	#イベント用
		self.right_side_padding = 20	#右端のパッディング
		self.left_side_padiing = 14	#左端のパッディング
		self.vertical_padding = 20
		self._drawing_end_index = None	#ロジックの簡略化のため描画される足の終わりのインデックス
		self._drawing_start_index = None
		self._index_posX_table = {}	#株価データリストのインデックスと座標のテーブル。draw()によりのみ変更される。
		self._least_val , self.convert_scale , num_of_candle = None,None,None	#価格の座標への変換のための一時変数。専用のset()メソッドで設定され、self.price_to_height()メソッドでその変換に用いられる。
		self._Y_axis_fixed = False	#Y座標を固定にするかどうかのフラグ。self.get_price_range()で用いられる。
		self._tab = None
		self._highlight_index = 0	#ハイライト表示
		self.horizontal_rulers = []	#価格を表す水平ルーラーのリスト
		self.moving_averages = []	#移動平均オブジェクトのリスト

		#データの保存とフェッチに関するメタ情報を格納するメンバ変数
		self.download_mode = download_mode	#ローカル環境に株価データがあればそれを用いる
		self.download_site = site
		self.file_header = []	#ローカルファイルに保存するためのファイルヘッダ

		#イベントに関するフラグ変数
		self.focused_horizontal_ruler = None #Horizontal_Rulerオブジェクトが格納される

		#初期化関数
		self.set_term(term_num)	#２つのterm変数のセッターメソッド
		self.set_zoom_scale()	#ズームスケールのデフォルト値の設定

	def set_zoom_scale(self,scale=None):
		"""
		ズームスケールの設定を行う。
		ズームスケールが引数に渡されなかった場合、足期間に応じてデフォルト値を設定する
		"""
		if scale :
			self._zoom_scale = scale
		else:
			#デフォルト値の設定
			if self.term_for_a_bar == TERM_DICT["日足"] :
				self._zoom_scale = 1
			elif self.term_for_a_bar == TERM_DICT["週足"] :
				self._zoom_scale = 2
			elif self.term_for_a_bar == TERM_DICT["5分足"] :
				self._zoom_scale = 1.5
			elif self.term_for_a_bar == TERM_DICT["1分足"] :
				self._zoom_scale = 0.5

	def get_zoom_scale(self):
		return self._zoom_scale

	def set_tab(self,tab):
		"""
		タブの設定
		"""
		self._tab = tab

	def get_tab(self):
		return self._tab 

	def set_term(self,term_num):
		"""
		self.term_for_a_bar変数及び、self.term_for_csv変数のセッターメソッド。
		週足、月足、は日足のCSVデータから動的に生成するため、両者の変数は、この場合に限り、値が異なることになる。
		このメソッドは足ごとの期間termを引数に取り、適切な「期間」を表す値をそれぞれの変数に格納する。
		"""
		self.term_for_a_bar = term_num
		if term_num in range(1,3):	#termが週足、月足、を表す場合には
			self.term_for_csv = TERM_DICT["日足"]
		else :
			self.term_for_csv = term_num

	def set_drawing_index(self,dummy=None,start=None,end=None):
		"""
		描画すべきチャート範囲を保持するためのデータのインターフェイス
		"""
		if dummy :
			raise Exception("引数は明示的に宣言してください")
		if start != None :
			self._drawing_start_index = start
		elif end :
			if end >= len(self.stock_price_list) :
				raise Exception("endが大き過ぎます")
			self._drawing_end_index = end
		else :
			raise Exception("いかなる値も与えられていません")

	def get_drawing_index(self):
		"""
		描画されている（あるいは描画されるべき）チャート範囲のデータindexを返す。
		"""
		return self._drawing_start_index , self._drawing_end_index

	def download_price_data(self):
		"""
		CSVデータのダウンロードを行うインターフェイスです。
		このオブジェクトのfetch,save,downloadメソッドは、その株価データ（のコンテナself.stock_price_list)を直接編集します。
	これはそのデータ構造が単純で、また、その利用形式、登録するデータの形式が単一であり、データへのアクセスや設定のためのむつかしいインターフェイスが全く必要ないためです。
		"""
		#Tabにデータがあったらそこから読み出す。
		if self.read_from_tab() :
			return True	#もはやダウンロードの必要はない。制御を返す。
		#Tabになかったらフェッチし、保存する。
		self.stock_price_list = []	#初期化
		#Changed_by_Windows - ダウンロードモード機構の変更:モードとサイトの２重構造にする---------------
		if self.download_mode == DOWNLOAD_MODE_LOCAL :
			#ローカルモードであり、対象のファイルがローカルにあれば
			if self.exist_stock_price_file() :
				if not self.download_price_data_from_file() :	return False
			else :
				return False
		elif self.download_mode == DOWNLOAD_MODE_DIFF :
			#差分ダウンロード
			raise Exception("未定義です")
		elif self.download_mode == DOWNLOAD_MODE_DOWNLOAD :
			#強制ダウンロード
			if self.download_site == DOWNLOAD_SITE_KDB :
				if not self.download_price_data_from_kdb() :	return False
			else :
				raise Exception("未定義のサイトです")
		else :
			raise Exception("未定義のモードです")
		#--------------------------------------------------------------

		#最後のエラー補足。株価データが正常かを確認
		if not self.stock_price_list :
			return False
		self.set_drawing_index( end=len(self.stock_price_list)-1 )
		self.synchro_with_tab()	#tabに同期
		#週足、月足についてはtabを介して変換されたデータを得る。
		if TERM_DICT[self.term_for_a_bar] in ("週足","月足") :
			self.read_from_tab()

		return True
	
	def download_price_data_from_file(self):
		"""
		ローカルファイルから株価情報をインポートします。失敗すればFalseを返します
		"""
		filename = self.convert_self_to_filename()
		fileobj = open(filename,"r")
		csv_text = fileobj.read()
		fileobj.close()
		if not self.save_csv_data(csv_text,from_file=True):
			return False
		return True

	def exist_stock_price_file(self):
		"""
		このオブジェクトに適合する株価データがローカル環境に保存されているかどうかを返す
		"""
		return os.path.isfile(self.convert_self_to_filename())
	
	def convert_self_to_filename(self):
		"""
		このオブジェクトをその意味するファイル名に変換する
		"""
		filename = CSV_DIR + "/%s-T%s.csv" % (self.security_code,TERM2URL_DICT[TERM_DICT[self.term_for_csv]])
		return filename

	def download_price_data_from_kdb(self):
		"""
		k-db.comよりCSVデータのフェッチと設定を行う
		なお、自動でローカルにファイルを生成し、そのデータを保存する
		"""
		url_list = []
		#urlの設定
		if TERM_DICT[self.term_for_csv] in ("日足","前場後場") :
			url_term_phrase = TERM2URL_DICT[TERM_DICT[self.term_for_csv]]
			if url_term_phrase :	url_term_phrase = "/" + url_term_phrase
			for year in range(2016,2012,-1) :
				url = "http://www.k-db.com/stocks/%s-T%s?year=%d&download=csv" % (self.security_code,url_term_phrase,year)
				url_list.append(url)
		else :
			url_list = self.get_urls(self.term_for_csv)
			if url_list == False :
				return False
		#CSVのフェッチとコンバート、保存を行い、何らかのエラーが出た時にはFalseを返す。
		for url in url_list:
			if not self.fetch_csv(url):
				return False
		self.stock_price_list.reverse()	#逆順、つまり日時において昇順にします
		self.save_csv_to_local()	#ローカルファイルに保存
		return True

	def get_urls(self,term_num):
		"""
		日足以外のCSVデータのURLを自動で生成する
		"""
		#まずurlを得るために解析を行うHTML文章のダウンロード
		url_term_phrase = TERM2URL_DICT[TERM_DICT[term_num]]
		base_url = "http://k-db.com/stocks/%s-T/%s" % (self.security_code,url_term_phrase)
		request = urllib2.Request(base_url)
		#HTTPヘッダの偽装
		UserAgent = "Mozilla/5.0 (X11; Linux x86_64; rv:30.0) Gecko/20100101 Firefox/30.0"
		request.add_header("User-agent",UserAgent)	
		#HTTPリクエストの送信と、レスポンスについてのチェック
		try:
			respose = urllib2.urlopen(request)
		except urllib2.URLError,e:
			print e.reason	#デバッグプリント
			tkMessageBox.showerror(message="CSVのダウンロードに失敗しました。")
			return False
		#hTML文章のパーシング
		parser = Get_Url_Parser()
		date_list = parser.get_dates(respose.read())
		if len(date_list) == 0 :
			return False
		#urlの動的生成
		url_list = []
		for date in date_list :
			format_date = "2016-%s" % (date.replace("/","-"))
			url = "%s?date=%s&download=csv" % (base_url,format_date)
			url_list.append(url)
		return url_list

	def synchro_with_tab(self):
		"""
		Tabにデータを同期する
		"""
		#Tabにデータを同期。または読み出し。
		tab = self.get_tab()
		if tab :
			#日足ならそのデータ、またはそれを週足、月足に変換したデータをそれぞれtabに同期
			csv_term = TERM_DICT[self.term_for_csv]
			if csv_term == "日足" :
				tab.set_data(self.term_for_a_bar,self.stock_price_list)	#日足の同期
				tab.set_data(TERM_DICT["週足"],self.convert_daily_to_weekly())
				tab.set_data(TERM_DICT["月足"],self.convert_daily_to_monthly())
			#ただの同期
			elif csv_term in ("1分足","5分足","前後場足") :
				tab.set_data(self.term_for_a_bar,self.stock_price_list)	#日足の同期

	def read_from_tab(self):
		"""
		Tab「から」データを同期。すなわちデータをtabから読み出す。
		Tabにデータが保管されていたのならば、Trueを、さもなくばFalseを、返す。
		"""
		tab = self.get_tab()
		if tab :
			if TERM_DICT[self.term_for_a_bar] in ("週足","月足") and tab.data_in_tab(self.term_for_a_bar):
				self.stock_price_list = tab.get_data(self.term_for_a_bar)
				self.set_drawing_index(end=len(self.stock_price_list)-1)
				return True
		return False

	def fetch_csv(self,url):
		"""
		株価データダウンロードサイトk-db.comから株価データをCSV形式でフェッチする。
		正常にダウンロードの完了したCSV文章は、データ構造をリスト形式に変換され、self.stock_price_listに保存される。
		この処理は、実際にはself.save_csv_data()メソッドによって行われ、同時にデータチェックも行われる。

		データ取得の失敗 : このメソッドは、CSVデータのダウンロードに失敗した時、あるいは、ダウンロードされたCSVデータが予期された形式でない時、Flase値をReturnする。あるいは、正常に処理が完了した場合にはTrue値を返す。
		"""
		#URLの動的生成と、Requestオブジェクトの生成。
		request = urllib2.Request(url)
		#HTTPヘッダの偽装
		UserAgent = "Mozilla/5.0 (X11; Linux x86_64; rv:30.0) Gecko/20100101 Firefox/30.0"
		request.add_header("User-agent",UserAgent)	
		#HTTPリクエストの送信と、レスポンスについてのチェック
		try:
			respose = urllib2.urlopen(request)
		except urllib2.URLError,e:
			print e.reason	#デバッグプリント
			tkMessageBox.showerror(message="CSVのダウンロードに失敗しました。")
			return False
		csv_text = unicode(respose.read(),"Shift-Jis").encode("utf-8")	#Shift-JisからUnicode文字列へ
		if DEBUG_MODE :
			open("debug_stockfile.txt","w").write(csv_text)
			print "フェッチしたファイル debug_stockfile.txt を現ディレクトリに生成しました。"
		#self.save_csv_data()メソッドを呼び出し、データチェックに引っかかったらFalseをリターンする
		if not self.save_csv_data(csv_text) :
			tkMessageBox.showerror(message="証券コードが間違っているか、予期せぬCSV形式です。")
			return False
		return True	#フェッチとデータ格納完了

	def save_csv_data(self,csv_text,from_file=False):
		"""
		引数に与えられたCSV文章を数値型にコンバートして、self.stock_price_listメンバ変数に株価リストとして保存する。
		また、同時にデータフォーマットのチェックを行い、予期せぬデータであった場合はFalse値を返す。

		CSV１行目と２行目の書式:
		1: 2315-T,JQスタンダード,SJI,日足
		2: 日付,始値,高値,安値,終値,出来高,売買代金
		日足以外
		2:日付,時刻,始値,高値,安値,終値,出来高,売買代金
		"""
		i = 1 	#行数を表す一時変数。
		is_daily_data = ( TERM_DICT[self.term_for_csv] == "日足" )	#日足データであるか否か
		for line in csv_text.split("\n") :
			tmp_list = line.split(",")	#CSV文章の各行をリスト化
			#１行目:予期される正しいCSV文章かのチェックと株名の保存
			if i == 1 :
				if ( not tmp_list[0] == str(self.security_code)+"-T" ) or ( not tmp_list[3].strip() == TERM_DICT[self.term_for_csv] ) :
					return False
				else: 
					self.security_name = tmp_list[2]
					if not line in self.file_header :	
						self.file_header.append(line)
					i+=1
					continue
			#２行目:pass
			elif i == 2 :	
				if not line in self.file_header :	
					self.file_header.append(line)
				i+=1
				continue
			#3行目以降:第２フィールド以下をintに変換してself.stock_price_listにappend
			else :
				if line.strip() == "" :
					continue
				csv_converted_list = []
				for field_num in range(0,len(tmp_list)) :
					#日足の第一フィールドと、それ以外の足の第一、第二フィールドは日時を表す文字列
					if field_num == 0 :
						if is_daily_data or from_file :
							csv_converted_list.append(tmp_list[0])
					elif field_num == 1 and not is_daily_data and not from_file:
						csv_converted_list.append(tmp_list[0]+"-"+tmp_list[1])
					#データがないと"-"これは0で保存
					elif tmp_list[field_num] == "-":
						csv_converted_list.append(0)
					else :
						csv_converted_list.append(int(tmp_list[field_num]))
				self.stock_price_list.append(csv_converted_list)
		return True 

	def save_csv_to_local(self):
		"""
		ローカルファイルにダウンロードされた株価情報をアウトプットします。
		書式として、ファイルの1,2行目には、ダウンロードされたファイルの1,2行目の文字列をそのまま書き出します。
		"""
		filename = self.convert_self_to_filename()
		fileobj = open(filename,"w")
		for line in self.file_header :
			fileobj.write(line+"\n")
		for price_list in self.stock_price_list :
			str_list = [price_list[0]] + (map (str,price_list[1:]))
			fileobj.write(",".join(str_list)+"\n")
		fileobj.close()
		print "Download and Save : ",filename

	def convert_daily_to_weekly(self):
		"""
		日足データを週足に変換してリターンする
		ここで定義する「週足」とは、「ある月曜の１日から「５日間」の４本値を集積する足」である。この定義では必然的に、土日以外に市場が停止しているか、あるいはそのデータが欠落していた場合、厳密な「週足」を必ずしも意味しなくなる。
		"""
		#チェック
		if self.term_for_csv != TERM_DICT["日足"] :
			raise Exception("週足に変換する為のデータが、日足ではありません。")
		#変換
		weekly_price_list = []
		tmp_list = []
		daily_list = self.stock_price_list
		for index in range(0,len(daily_list)) :
			date = self.get_date2int_list(index)	#[year,month,day]のリスト
			if Date(date[0],date[1],date[2]).weekday() == 0 :	#月曜なら
				tmp_list = daily_list[index:index+5]
				high , low , price_range = self.get_price_range(tmp_list)
				opning , closing = self.get_opning_closing_price(tmp_list)
				date_str = "%s〜%s" % (tmp_list[0][0],tmp_list[-1][0][tmp_list[-1][0].find("-")+1:])
				l = (date_str,opning,high,low,closing)
				weekly_price_list.append(l)

		return weekly_price_list

	def convert_daily_to_monthly(self):
		"""
		日足データを月足に変換してリターンする
		"""
		#チェック
		if self.term_for_csv != TERM_DICT["日足"] :
			raise Exception("月足に変換する為のデータが、日足ではありません。")
		#変換
		monthly_price_list = []
		tmp_list = []
		daily_list = self.stock_price_list
		pass

	def set_Y_axis_fixed(self,boolean):
		"""
		このチャートのY軸の固定についての設定
		"""
		self._Y_axis_fixed = boolean

	def get_Y_axis_fixed(self):
		return self._Y_axis_fixed

	def draw(self,surface,font,bold_font):
		"""
		ローソク足と、それに付随するいくつかの要素の描画を行うメソッド。
		まず、描画に必要ないくつかの動的に決定される値の算出を行い、この値を用いて実際の描画を行う。
		描画を行う実際のメソッドは、それぞれの担当する要素ごとにわかれていて、それぞれのメソッドは、それぞれに内部で新たなサーフェスを生成し、これを最後にこのメソッド内で大もとのサーフェスに貼り付ける。という手順で描画が行われる。
		この為、単にサーフェスに重ねて描画していくのに比べ処理に大きく時間がかかることになる。
		"""
		if not self.stock_price_list :
			raise Exception("株価データが存在しません")
		#描画についての諸設定値の算出と設定。
		surface_size = surface.get_size()
		candle_width , padding_size = self.get_drawing_size()
		side_padding = self.left_side_padiing + self.right_side_padding
		num_of_candle = int ( float(surface.get_width() - side_padding ) / (candle_width + padding_size) ) 
		start_index , end_index = self.get_drawing_index()
		start_index = end_index - num_of_candle
		if start_index < 0 :
			start_index = 0
		self.set_drawing_index(start=start_index)	#start_indexを保存しておく

		#価格データの座標への変換のための値の算出と設定。
		high_price , low_price , price_range = self.get_price_range(self.stock_price_list[start_index : end_index])
		convert_scale = float(surface.get_height()-self.vertical_padding) / price_range 	#価格１あたりのy(高さ)増加値
		self.set_temporary_drawing_information(convert_scale,low_price,num_of_candle)
		#株価データのリストのindex値に対する描画地点Xの設定
		self.set_index_posX_table()

		#ローソク足の描画
		surface_drawn_candle = self.draw_candle(surface_size)
		#移動平均線の描画
		surface_drawn_moving_average = self.draw_moving_average(surface_size)
		#出来高の描画
		surface_drawn_dekidaka = self.draw_dekidaka(surface_size,font)
		#座標の線などその他要素の描画
		surface_drawn_axis = self.draw_coordinate_axis(surface_size,high_price,low_price,font)
		surface_drawn_yaxis = self.draw_y_axis(surface_size,font)	
		#追加情報の描画
		surface_drawn_additonal_information = self.draw_additional_information(surface_size,bold_font)
		surface_drawn_additonal_setting_info = self.draw_additional_setting_info(surface_size,bold_font)
		#動的な要素の描画
		surface_drawn_highlight = self.draw_highlight(surface_size)
		surface_drawn_horizontal_rulers = self.draw_horizontal_rulers(surface_size,font)
		#諸サーフェスのblit;blit順で全面背面の関係性が決定
		surface.blit(surface_drawn_highlight,(0,0))
#		surface.blit(surface_drawn_dekidaka,(0,surface.get_height() * (float(1)/3) ))
		surface.blit(surface_drawn_dekidaka,(0,0))
		surface.blit(surface_drawn_axis,(0,0))
		surface.blit(surface_drawn_yaxis,(0,0))
		surface.blit(surface_drawn_additonal_information,(0,0))
		surface.blit(surface_drawn_additonal_setting_info,(0,0))
		surface.blit(surface_drawn_horizontal_rulers,(0,0))
		surface.blit(surface_drawn_candle,(0,0))
		surface.blit(surface_drawn_moving_average,(0,0))

	#Changed_by_Windows 
	def draw_additional_setting_info(self,surface_size,font):
		"""
		セッティングについての情報の描画。サーフェスサイズについては、普通の情報描画についても同じことをしてもいいかもしれない
		つまり、ぴったりのサーフェスを作る。という処理方法。
		右から順番に押し込んでいく。そのためアルゴリズムが若干面倒くさくなる
		1,移動平均線についての情報。
		2,Y-prefix
		"""
		v_padding = self.vertical_padding
		side_padding = self.right_side_padding
		height = font.size("あ")[1] + v_padding
		surface = self.get_surface((surface_size[0],height))
		right = surface_size[0] - side_padding
		if self._Y_axis_fixed == True :
			renderd = font.render(u"Y軸固定",True,(100,100,100))
			right = right - renderd.get_width() - side_padding/2 
			surface.blit(renderd,(right,v_padding))
		for MA in self.moving_averages :
			color = MA.color
			days = "%d日移動平均" % (MA.days)
			days = unicode(days,"utf-8")
			renderd = font.render(days,True,color)
			right = right - renderd.get_width() - side_padding/2
			surface.blit(renderd,(right,v_padding))
			 
		return surface

	#Changed_by_Windows
	def draw_dekidaka(self,surface_size,font):
		"""
		出来高の描画
		"""
		#半分
		half_size = (surface_size[0],surface_size[1])
		half_surface = self.get_surface(half_size)
		#出来高の価格幅の算出
		start , end = self.get_drawing_index()
		dekidaka_list = []	#ここ別の記法?
		for price_list in self.stock_price_list[start:end+1] :
			dekidaka_list.append(price_list[5])	#pricetype2indexを使うべき
		high , low , price_range = self.get_price_range_dekidaka(dekidaka_list)
		#convert_scaleの生成
		convert_scale =  float(half_surface.get_height()) / price_range

		#横線の描画
#		y_axis_surface = self.draw_y_axis_dekidaka(surface_size,font,high,low,convert_scale)
#		half_surface.blit(y_axis_surface,(0,0))
		#いざ描画
		now_index = start	#アルゴリズム変える
		for dekidaka in dekidaka_list :
			x = self.get_index2pos_x(now_index)
			height = self.price_to_height_dekidaka(convert_scale,low,dekidaka)
			candle_width , padding = self.get_drawing_size()
			rect = pygame.Rect((x-(candle_width/2),0 ),(candle_width,height))
			pygame.draw.rect(half_surface,(255,200,200),rect,candle_width)
			now_index += 1

		flipped = pygame.transform.flip(half_surface,False,True)
		return flipped

	#Changed_by_Windows
	def price_to_height_dekidaka(self,convert_scale,least_val,price):
		"""
		出来高用のprice_to_height
		これも後で変える
		"""
		return int(round(( float(price) * convert_scale ) - ( float(least_val) * convert_scale )))

	#Changed_by_Windows 
	def get_price_range_dekidaka(self,dekidaka_list):
		"""
		price_rangeを返す関数。これも枠組みを変えるべきだろう
		"""
		for index in range(len(dekidaka_list)-1,1,-1) :
			if dekidaka_list[index] == 0 or dekidaka_list[index-1] == 0:
				continue
#			val = dekidaka_list[index] / dekidaka_list[1] 
			val=1
			#最近の出来高から言って法外な値でなければ初期値の設定
			if val < 10 :
				high_price , low_price = dekidaka_list[index] , dekidaka_list[index]
				break

		for dekidaka in dekidaka_list :
			if dekidaka == 0 :
				continue
			if dekidaka > high_price and float(dekidaka) / high_price < 30:
				high_price = dekidaka
			elif dekidaka < low_price  and float(low_price) /dekidaka < 30:
				low_price = dekidaka

		return high_price , low_price , high_price-low_price

	#Changed_by_Windows
	def draw_y_axis_dekidaka(self,surface_size,font,high,low,convert_scale):
		"""
		出来高の横線の描画
		ここも大きく枠組みを変えるべきでしょう
		というかいらないな。いるとしても工夫がいる。
		"""
		surface = self.get_surface(surface_size)
		price_range = high - low
		for i in range(1,6):
			price = price_range * (float(i)/6) + low
			y = self.price_to_height_dekidaka(convert_scale,low,price )
			pygame.draw.aaline(surface,(255,200,200),(0,y),(surface_size[0],y))
		return surface

	def get_drawing_size(self):
		zoom_scale = self.get_zoom_scale()
		candle_width = int(zoom_scale * 4)
		padding_size = int(zoom_scale * 4)
		return candle_width,padding_size
	
	def get_surface(self,surface_size,color_key=(255,255,255)):
		surface = pygame.Surface(surface_size)
		surface.set_colorkey(color_key)
		surface.fill((255,255,255))
		return surface

	def set_index_posX_table(self):
		"""
		株価データのリストself.stock_price_listのindex値に対する、与えられたサーフェスにおける描画すべきX座標値の設定行う。
		設定情報はself._index_posX_tableに保持する。
		このメソッドのみが、唯一、このオブジェクトに描画される諸オブジェクトのX座標値を決定せしめることができるため、つまり、すべての実際に描画を行う関数は、このメソッドの「後」に呼び出されなければならない。
		"""
		self._index_posX_table = {}
		start_index , end_index = self.get_drawing_index()
		candle_width , padding = self.get_drawing_size()
		now_x = self.left_side_padiing
		for index in range(start_index,end_index+1) :
			self._index_posX_table[index] = now_x
			now_x += (candle_width/2  + padding + candle_width/2)

	def get_index2pos_x(self,index):
		"""
		self._index_posX_tableからデータを取り出す為のインターフェイス
		"""
		return self._index_posX_table[index]

	def draw_candle(self,surface_size):
		"""
		ローソク足を描画したサーフェスを返す
		"""
		surface = self.get_surface(surface_size)
		candle_width , padding_size = self.get_drawing_size()
		zoom_scale = self.get_zoom_scale()
		#ローソク足の描画
		start_index , end_index = self.get_drawing_index()
		for index in range(start_index,end_index+1) :
			#描画する価格データ
			price_list = self.stock_price_list[index]
			opning_price , closing_price = self.get_opning_closing_price(price_list)
			high_price , low_price , price_range = self.get_price_range(price_list)
			upper , lower , candle_color = (opning_price,closing_price,(255,0,0)) if closing_price > opning_price else (closing_price,opning_price,(0,0,255))	
			#描画
			pos_x = self.get_index2pos_x(index)
			rect = pygame.Rect((pos_x-candle_width/2,self.price_to_height(upper)),(candle_width,self.price_to_height(lower)-self.price_to_height(upper)))	#pygameは上が(0,0)(=小さい値)なので、lower(大きい値)からupperを引いてheightとします。
			pygame.draw.rect(surface,candle_color,rect,candle_width)
			line_start_pos = (pos_x , self.price_to_height(high_price) )
			line_end_pos = (pos_x , self.price_to_height(low_price) )
			line_width = int(zoom_scale*2)
			pygame.draw.line(surface,candle_color,line_start_pos,line_end_pos,line_width)
		surface = pygame.transform.flip(surface,False,True)
		return surface

	def set_default_moving_averages(self):
		"""
		"""
		self.moving_averages = []	#初期化
		if TERM_DICT[self.term_for_a_bar] in ("日足","前場後場") :
			short_MA = Moving_Average(self,5,"C",(255,0,0))
			middle_MA = Moving_Average(self,25,"C",(0,0,255))
			long_MA =Moving_Average(self,75,"C",(0,255,0))
			morelong_MA =Moving_Average(self,135,"C",(255,255,0))

			self.moving_averages.append(short_MA)
			self.moving_averages.append(middle_MA)
			self.moving_averages.append(long_MA)
			self.moving_averages.append(morelong_MA)

		#Changed_by_Windows - 分足とかにもMA使えるかな。
		elif TERM_DICT[self.term_for_a_bar] in ("5分足","1分足") :
			short_MA = Moving_Average(self,5,"C",(255,0,0))
			middle_MA = Moving_Average(self,10,"C",(0,0,255))
#			long_MA =Moving_Average(self,75,"C",(0,0,0))

			self.moving_averages.append(short_MA)
			self.moving_averages.append(middle_MA)
#			self.moving_averages.append(long_MA)

	def draw_moving_average(self,surface_size):
		"""
		移動平均線の描画
		MAオブジェクトの中でself.index_posX_tableを使います。
		"""
		surface = self.get_surface(surface_size)
		start_index , end_index = self.get_drawing_index()
		if not self.moving_averages:
			self.set_default_moving_averages()
		#移動平均値の算出と描画
		for MA in self.moving_averages :
			MA.calc(start_index,end_index)
			MA.draw_to_surface(surface)

		flipped_surface = pygame.transform.flip(surface,False,True)	#pygameでは(0,0)が左上なのでフリップ
		return flipped_surface

	def draw_highlight(self,surface_size):
		"""
		ハイライト表示加工をしたサーフェスを返す。
		"""
		surface = self.get_surface(surface_size)
		if not self._index_posX_table :
			raise Exception("インデックスーX座標のテーブルが定義されていません")
		highlight_index = self.get_highlight_index()
		#ハイライト対象が描画領域内にあれば描画
		start_index , end_index = self.get_drawing_index()
		if highlight_index in range(start_index,end_index+1) :
			candle_width , padding = self.get_drawing_size()
			highlight_pos_x = self.get_index2pos_x(highlight_index)
			highlight_rect = pygame.Rect((highlight_pos_x-padding-(candle_width/2),0),(candle_width+padding*2,surface_size[1]))
			pygame.draw.rect(surface,(255,255,0),highlight_rect,0)

		return surface
			
	def get_price_range(self,stock_price_list):
		"""
		与えられた株価のリスト(あるいはそのリスト)から、最高値、最安値、値幅、をそれぞれ算出し、そのタプルを返す。
		"""
		#高値、安値を表すindex値
		high_index = self.pricetype2index("H")
		low_index = self.pricetype2index("L")
		#株価リストのリストなら
		if isinstance(stock_price_list[0],(list,tuple)) :
			#Y軸固定の場合、価格範囲はすべてのデータを対象とする。
			if self._Y_axis_fixed :
				stock_price_list = self.stock_price_list
			#基準となる高値、安値を得る。ただし不明値0だと困るのでforで0以外を探す
			high_price , low_price = 0,0
			for index in range(len(stock_price_list)-1,0,-1) :
				if not high_price :
					high_price = stock_price_list[index][high_index]
				if not low_price :
					low_price = stock_price_list[index][low_index]
				if high_price and low_price :
					break
			#高値と安値の算出
			for price_list in stock_price_list :
				if high_price < price_list[high_index] and price_list[high_index] < high_price * 5:
					high_price = price_list[high_index]
				if low_price > price_list[low_index] and price_list[low_index] > low_price / 5:
					low_price = price_list[low_index]
		#単に株価リストなら
		else :
			high_price = stock_price_list[high_index]
			low_price = stock_price_list[low_index]

		price_range = high_price - low_price
		return high_price,low_price,price_range

	def get_opning_closing_price(self,stock_price_list):
		"""
		株価の始値と終値をセットで返す関数
		もちろん株価データリストのコレクションを渡されたらその始めの要素における始値と、その最後の要素における終値を、セットで返す。
		"""
		opning_index = self.pricetype2index("O")
		closing_index = self.pricetype2index("C")
		#引数が１つ以上の株価データのリストを要素として有するコレクションならば
		if isinstance(stock_price_list[0],(list,tuple)) :
			opning_price = stock_price_list[0][opning_index]	#一番古い株価の始値
			closing_price = stock_price_list[-1][closing_index]	#一番新しい株価の終値
			return opning_price , closing_price
		#単に株価のリストであれば
		else :
			opning_price = stock_price_list[opning_index]	#始値
			closing_price = stock_price_list[closing_index]	#終値
			return opning_price , closing_price

	def price_to_height(self,price):
		"""
		株価をY座標値に変換します。
		この変換には、３つの値が用いられ、そのうち２つはself.set_convert_scale()メソッドによって動的に設定されます。
		1,convert_scale : 価格１あたりの高さ(=y座標)増加値。
		2,least_val : 価格の最小値。 
		3,price : 実際に変換する価格値。
		"""
		convert_scale = self._convert_scale
		least_val = self._least_val
		abs_height = convert_scale * price 
		relative_height = abs_height - (least_val * convert_scale) + self.vertical_padding/2
		return relative_height
		
	def set_temporary_drawing_information(self,convert_scale,least_val,num_of_candle):
		"""
		ユーティリティ関数であり、株価データを座標値に変換するのに必要な値を一時的にこのオブジェクトに格納します。
		"""
		self._convert_scale = convert_scale
		self._least_val = least_val
		self._num_of_candle = num_of_candle

	def draw_additional_information(self,surface_size,font):
		"""
		追加情報をチャート描画領域に描画します。
		具体的には、
		1，表示してる足期間
		2，描画している期間
		3，ズームスケール
		"""
		surface = self.get_surface(surface_size)
		additional_informations = []	#追加情報を表す文字列の一時リスト
		padding = self.left_side_padiing
		#Changed_by_Windows サーフェスサイズ、paddingのわずかな修正。
		v_padding = self.vertical_padding
		start_index , end_index = self.get_drawing_index()
		start_date = self.stock_price_list[start_index][0].replace("-","/")	#描画している一番初めの日時
		end_date = self.stock_price_list[end_index][0].replace("-","/")	#描画している一番最後の日時
		#文字列の生成とadditional_informationsへの登録
		bar_term_str = unicode(TERM_DICT[self.term_for_a_bar],"utf-8")	#足期間
		additional_informations.append(bar_term_str)
		how_long_str = unicode("%s〜%s"%(start_date,end_date),"utf-8")	#表示期間についての情報
		additional_informations.append(how_long_str)
		zoom_scale_str = unicode("x%.1f"%(self.get_zoom_scale()),"utf-8")	#ズームスケール
		additional_informations.append(zoom_scale_str)
		#レンダリングとサーフェスの生成、描画
		left = padding
		for info_str in additional_informations:
			renderd = font.render(info_str,True,(255,0,0))
			surface.blit(renderd,(left,v_padding))
			left += padding + renderd.get_width()

		return surface

	def draw_horizontal_rulers(self,surface_size,font):
		"""
		水平ルーラーを描画する。
		なお、水平ルーラーが未定義の場合には、描画範囲の最安値と最高値でルーラーオブジェクトを生成する
		"""
		surface = self.get_surface(surface_size)
		#水平ルーラーが未定義の時にはデフォルトで定義
		if len(self.horizontal_rulers) == 0 :
			self.set_default_horizontal_rulers()
		#個々のルーラーオブジェクトに水平ルーラーを描画させる
		for ruler in self.horizontal_rulers :
			ruler.draw_to_surface(surface,font)	#サーフェスに直接描画

		flipped_surface = pygame.transform.flip(surface,False,True)
		return flipped_surface

	def set_default_horizontal_rulers(self):
		"""
		デフォルトの設定で水平ルーラを定義します。
		ただし、描画するindex値から適当な価格を動的に算出するので、描画領域がすでに確定されている必要があります。
		具体的には、描画範囲における最高値と最安値、また、最も最近の終値を表すルーラーを定義します。
		"""
		self.horizontal_rulers = []	#初期化
		start , end = self.get_drawing_index()
		high_price , low_price , price_range = self.get_price_range(self.stock_price_list[start:end])
		last_day_closing_price = self.stock_price_list[-1][self.pricetype2index("C")]
		high_ruler = Horizontal_Ruler(self,high_price,(255,100,100))
		low_ruler = Horizontal_Ruler(self,low_price,(100,100,255))
		close_ruler = Horizontal_Ruler(self,last_day_closing_price,(100,255,100))
		self.horizontal_rulers.append(high_ruler)
		self.horizontal_rulers.append(low_ruler)
		self.horizontal_rulers.append(close_ruler)
	
	def draw_coordinate_axis(self,surface_size,high_price,low_price,font):
		"""
		座標の線を引くメソッド。
		適当な間隔を動的に算出して、描画したサーフェスを返す
		引数には描画する線の高値値と安値値をとる。
		"""
		surface = self.get_surface(surface_size)
		price_range = high_price - low_price
		axis_interval = ( price_range / 20 ) or 1	#値幅をX等分
		surface_width = surface.get_width()
		surface_height = surface.get_height()
		convert_scale = self._convert_scale

		#座標線のインターバル値、あるいははじめに引く最安座標線を切りのいい値にする。
		while ( price_range >= 100 and axis_interval % 10 != 0 ) or ( price_range <= 100 and axis_interval % 2 != 0) :
			axis_interval += 1
		while ( low_price % axis_interval != 0) :
			low_price += 1	#もはや安値は意味しない
		for i in range(low_price,high_price+axis_interval,axis_interval) :
			pos_y = self.price_to_height(i)
			pygame.draw.line(surface,(0,0,0),(0,pos_y),(surface_width,pos_y),1)	#横線
			text_surface = font.render(str(i),True,(0,0,0))
			text_size = font.size(str(i))
			flipped_surface = pygame.transform.flip(text_surface,False,True)	#最後の座標の反転のため
			surface.blit(flipped_surface,(surface_width-text_size[0],pos_y-text_size[1]))	#文字

		return pygame.transform.flip(surface,False,True)

	def draw_y_axis(self,surface_size,font):
		"""
		日時を表す縦線描画のための中間インターフェイス。
		足によって条件処理が全く異なるために意外と面倒。
		実際の描画を行うメソッドには引数をそのまま継承して渡して、コールする。
		すべてのこのメソッドに隷属的な描画命令セットは最後にその描画されたサーフェスを返す。
		"""
		if self.term_for_a_bar == TERM_DICT["日足"] or self.term_for_a_bar == TERM_DICT["前場後場"] :
			drawn_surface = self.draw_y_daily_axis(surface_size,font)
		elif self.term_for_a_bar == TERM_DICT["週足"]:
			drawn_surface = self.draw_y_weekly_axis(surface_size,font)
		elif self.term_for_a_bar == TERM_DICT["5分足"]:
			drawn_surface = self.draw_y_minutely_axis(surface_size,font)
		elif self.term_for_a_bar == TERM_DICT["1分足"]:
			drawn_surface = self.draw_y_minutely_axis(surface_size,font)
		else :
			raise Exception("処理が定義されていません")

		return drawn_surface

	def draw_y_daily_axis(self,surface_size,font):
		"""
		日足用の縦線描画
		また、前場後場足についてもその縦線を描画する。
		月単位で縦線を描く
		"""
		surface = self.get_surface(surface_size)
		start_index , end_index = self.get_drawing_index()
		for index in range(start_index,end_index+1) :
			date = self.get_date2int_list(index)
			if date[2] > 6 :	#日にち６までやる
				continue
			#月初めであるかどうかを判定;いずれかがTrueであればtestはパスである
			#内容はindexが０であるか、あるいは１つ前のデータが「前の月」のものであるかどうかを判定する
			test1 = (index == 0)
			if index != 0 :
				last_date = self.get_date2int_list(index-1)
				last_date_next_month = last_date[1]+1 if last_date[1] != 12 else 1
				test2 = (date[1] == last_date_next_month)
			else :	test2 = False
			#もし月の最も初めのデータであるならば描画
			if test1 or test2 :
				date_str = "%s/%s/%s" % (date[0],date[1],date[2])
				self.draw_actual_y_axis(surface,font,index,date_str)
		return surface

	def draw_y_weekly_axis(self,surface_size,font):
		"""
		週足用の縦線描画関数
		半年単位で線を描く。
		"""
		surface = self.get_surface(surface_size)
		start_index , end_index = self.get_drawing_index()
		for index in range(start_index,end_index+1) :
			date = self.get_date2int_list(index)
			#もし３月ごとの始めの週の葦であれば縦線の描画
			if date[1] % 3 == 0  and date[2] <= 7 :
				date_str = "%s/%s" % (date[0],date[1])
				self.draw_actual_y_axis(surface,font,index,date_str)
		return surface

	def draw_y_minutely_axis(self,surface_size,font):
		"""
		分足の縦線を描画する関数
		１時間ごとの線を描く
		"""
		surface = self.get_surface(surface_size)
		start_index , end_index = self.get_drawing_index()
		for index in range(start_index,end_index+1) :
			date = self.get_date2int_list(index)
			if date[4] >= 15 :
				continue
			predate = False if index == 0 else self.get_date2int_list(index-1)
			if ( not predate ) or ( predate[3] != date[3] and date[3] != 9) :
				date_str = u"%s時" % (date[3]) if self.term_for_a_bar == TERM_DICT["5分足"] else u"%s日%s時" % (date[2],date[3])
				color = (255,0,0) if date[3] == 15 else (0,0,0)	#15時は赤にしとく
				self.draw_actual_y_axis(surface,font,index,date_str,color=color)
		return surface
	
	def draw_actual_y_axis(self,surface,font,index,date_str,color=None) :
		"""
		実際に縦線の描画を行うメソッドで、足期間ごとに定義された条件判断のための中間メソッドから呼び出される。
		このメソッドは単に上位のメソッドの共通部分を関数化したものであり、その点、直接サーフェスを引数に取り、それに描画する。
		引数はサーフェスオブジェクト、フォントオブジェクトの他に実際に描画を行う地点のindex値、あるいはその線の情報を表す日時の文字列をとる。
		"""
		surface_height = surface.get_height()
		pos_x = self.get_index2pos_x(index)
		font_width,font_height = font.size(date_str)
		text_surface = font.render(date_str,True,(0,0,0))
		line_end_Y = surface_height - font_height - 2
		line_color = color if color else (0,0,0)	#デフォルトは黒

		pygame.draw.line(surface,line_color,(pos_x,0),(pos_x,line_end_Y),1)
		surface.blit(text_surface,(pos_x-font_width/2,surface_height-font_height-1))

	def get_date2int_list(self,index):
		"""
		与えられたindexで指示される株価データのリストについて、その日付を表す文字列を、評価用にint値に変換したもののリストを返す、ユーティリティ関数
		1,日足、前後場足は「年、月、日」のリスト。
		2,週足はその足の表すはじめの日を表す、上のフォーマットをもったリスト。
		3,分足は「年、月、日、時間、分」の形式のリスト。
		を、それぞれ返す。
		"""
		if self.term_for_a_bar == TERM_DICT["日足"] :
			date_str_list = self.stock_price_list[index][0].split("-")
			return map ( int,date_str_list )
		elif self.term_for_a_bar == TERM_DICT["前場後場"] :
			date_str_list = self.stock_price_list[index][0].split("-")[:-1]
			return map ( int,date_str_list )
		elif self.term_for_a_bar == TERM_DICT["週足"] :
			date_str_list = self.stock_price_list[index][0].split("〜")[0].split("-")
			return map ( int,date_str_list )
		elif self.term_for_a_bar == TERM_DICT["5分足"] or self.term_for_a_bar == TERM_DICT["1分足"] :
			#分足については「Y,M,D,H,M」の５つの要素を返す
			date_str_list = self.stock_price_list[index][0].replace(":","-").split("-")
			return map ( int,date_str_list )

	def pricetype2index(self,price_type):
		"""
		価格の種類に呼応したstock_price_listにおけるそれを表す値を指示するindex値を返すユーティリティ関数。
		"""
		if price_type == "O" :
			return 1
		elif price_type == "H" :
			return 2
		elif price_type == "L" :
			return 3
		elif price_type == "C" :
			return 4
		else :
			raise Exception("引数が価格の種類を表していません")

	def inherit(self,term_num):
		"""
		このオブジェクトの「銘柄コード」、「銘柄名」、「Tab」を継承(共有)する新たなStock_Chartオブジェクトを返す。
		"""
		#Changed_by_Windows 
		brother = Stock_Chart(self.security_code,term_num,self.download_mode,self.download_site)	#兄弟に当たる新しいオブジェクト
		brother.security_name = self.security_name
		tab = self.get_tab()
		if tab :
			brother.set_tab(tab)
		return brother

	def set_highlight_index(self,index):
		"""
		"""
		self._highlight_index = index

	def get_highlight_index(self):
		#Changed_by_Windows 未定義時の自動設定 別のところに書いたほうがよさそう
		if not self._highlight_index :
			endindex = self.get_drawing_index()[1]
			self.set_highlight_index(endindex)
			self.print_highlight_price_information()
		return self._highlight_index

	def height_to_price(self,pos_y):
		"""
		現在設定されている描画情報に基づいて、Y座標値を対応する価格値に変換する
		"""
		convert_scale = self._convert_scale
		least_val = self._least_val
		#価格上昇1に対する高さの上昇数算出のための変換式(convert_scale)から逆算する
		price_increacement_for_height = pos_y / convert_scale
		price_for_height = least_val + price_increacement_for_height
		return price_for_height

	#Changed_by_Windows - 出来高の表示。売買価格の表示
	def print_highlight_price_information(self):
		"""
		ジェネラルラベルに株価情報を表示します
		表示するデータは、indexで指示されるself.stock_price_list[index]の株価データです。
		"""
		#ラベルに詳細情報の表示
		parent = self.get_parent_box()
		highlight_index = self.get_highlight_index()
		price_list = self.stock_price_list[highlight_index]
		date = price_list[0]
		opning , closing = self.get_opning_closing_price(price_list)
		high , low , NoUse = self.get_price_range(price_list)

		#Changed_by_Windows - 出来高の表示。売買価格の表示 - pricetype2indexを使う
		dekidaka = price_list[5]
		kinngaku = price_list[6]

		general_label_box = parent.get_label_box("General")
		general_labels = general_label_box.label_list
		general_labels[0].set_string("%s %s %s" % (self.security_code,self.security_name,date))
		general_labels[1].set_string("高: %d  安: %d 始: %d  終: %d  出来高: %d 売買高: %d" % (high,low,opning,closing,dekidaka,kinngaku))
		general_label_box.draw()

	def dispatch_MOUSEBUTTONDOWN(self,event):
		"""
		"""
		#水平ルーラーにコライドしているのならフラグを上げる
		for ruler in self.horizontal_rulers :
			parent_lefttop_onroot = self.get_parent_box().get_left_top_on_root()
			pos = (event.pos[0]-parent_lefttop_onroot[0],event.pos[1]-parent_lefttop_onroot[1])
			if ruler.collide(pos) :
				self.focused_horizontal_ruler = ruler
				break
			self.focused_horizontal_ruler = None	#コライドしてないならフラグを下げる
		#ハイライトして再描画
		parent = self.get_parent_box()
		candle_width , NoUse = self.get_drawing_size()
		start , end = self.get_drawing_index()
		for index in range(start,end+1) :
			pos_x = self.get_index2pos_x(index)
			if pos_x-candle_width <= event.pos[0] <= pos_x+candle_width:
				self.set_highlight_index(index)
				parent.draw()
				break
		self.print_highlight_price_information()

	def dispatch_MOUSEMOTION(self,event):
		pass	

	def dispatch_MOUSEDRAG(self,event):
		"""
		ドラッグでチャート画面を移動させる。
		または水平ルーラーを移動させる
		"""
		#フォーカスされている水平ルーラーがあるならその高さを変更する
		if self.focused_horizontal_ruler :
			#Event.posYをこのチャートオブジェクトにおけるY座標値に変換し、それをflip(左下が(0,0)の形に変換)する。
			left_top_onroot = self.get_parent_box().get_left_top()
			top_margin = self.vertical_padding / 2
			pos_y_on_chart = self.get_parent_box().get_height() - ( event.pos[1] - left_top_onroot[1] ) - top_margin
			#算出された仮想Y座標値に対する、設定された価格値を算出する。
			price_for_posY = self.height_to_price(pos_y_on_chart)
			self.focused_horizontal_ruler.set_price( int( round(price_for_posY) ) )
			return True

		#チャートを移動させる
		moving_val = event.rel[0] / 2
		NoUse , end_index = self.get_drawing_index()
		if end_index - self._num_of_candle - moving_val >= 0 and len(self.stock_price_list) > end_index - moving_val :
			self.set_drawing_index( end=end_index - moving_val )

	def dispatch_KEYDOWN(self,event):
		"""
		矢印キーでオプションの設定を行う
		"""
		start_index,end_index = self.get_drawing_index()
		highlight_index = self.get_highlight_index()
		if event.key == pygame.K_LEFT :
			self.set_highlight_index(highlight_index-1)
			self.print_highlight_price_information()
		elif event.key == pygame.K_RIGHT and highlight_index < len(self.stock_price_list)-1:
			self.set_highlight_index(highlight_index+1)
			self.print_highlight_price_information()
		elif event.key == pygame.K_UP :
			self.set_zoom_scale(self.get_zoom_scale()+0.5)
		elif event.key == pygame.K_DOWN and self._zoom_scale >= 1:
			self.set_zoom_scale(self.get_zoom_scale()-0.5)
		else :
			pass

class Get_Url_Parser(HTMLParser):
	"""
	日足以外のCSVデータのURLを得るためのHTMLパーサークラス
	"""
	def __init__(self):
		HTMLParser.__init__(self)
		self.date_list = []
		self.F_in_target_element = False	#フラッグ

	def handle_starttag(self,tag,attrs):
		"""
		目的のHTML要素を探すメソッド
		"""
		if tag.lower() == "div" :
			attrs_dict = dict(attrs)
			if "id" in attrs_dict and attrs_dict["id"] == "ymenu" :
				self.F_in_target_element = True

	def handle_endtag(self,tag):
		"""
		目的の要素を抜ける時のメソッド
		"""
		if self.F_in_target_element and tag.lower() == "div" :
			self.F_in_target_element = False

	def handle_data(self,data):
		"""
		日付を得るメソッド
		"""
		if self.F_in_target_element and data[0].isdigit():
			self.date_list.append(data)
	
	def get_dates(self,html_str):
		self.feed(html_str)
		return self.date_list
				

class Setting_Tk_Dialog(object):
	"""
	ユーザーに銘柄コードの入力と、チャートについての設定を求めるダイアログを生成し、実際に株価データを保持するオブジェクトの生成、またはそのオブジェクトへの表示領域の提供を行うためのインターフェイスとしてのクラスです。

	1,インスタンス生成時、初期化メソッド中でGUI(Tk)のメインループ（無限ループ）を呼び出し、ユーザーに銘柄コードの入力及びチャートについての設定値の入力を求めます。
	2,その諸設定値は(入力終了時に)このオブジェクトのメンバ変数に保存されます。
	3,ユーザーによる入力が完了すると、実際に株価データのフェッチ、コンバート、保持を行うStock_Chartオブジェクトを生成します。
	4,これらのデータに関する処理が正常に終了したら、このStock_Chartオブジェクトに表示領域を提供するBOXオブジェクトを生成し、また、そのBOXオブジェクトをこのコンストラクタの呼び出し元であるBOXオブジェクトに関連付けます。
	これによってユーザーの情報の入力から、実際の表示領域の確保までの実際の橋渡しが終了します。
	5,最後にTkのメインループをBreakし、この設定画面の呼び出し元に制御を返します。
	"""
	def __init__(self,parent):
		"""
		インスタンス変数の作成と、ユーザーに情報の入力を求めるためのTkウィンドウの起動を行う。具体的には、
		1,Tk.Tk()によりTkルートウィンドウの作成
		2,Tkウィジェットの作成と、パッキング
		4,入力終了時に呼び出すバインド関数の登録
		5,root.mainloo()でTkメインループの呼び出し
		"""
		#Changed_by_Windows isinstanceの修正。チェック機構はそれぞれのsettingメソッドに拡張する
		if not isinstance(parent,(BASE_BOX,Root_Container,Stock_Chart)) :
			raise TypeError("引数がBOXオブジェクトあるいはRoot_Containerオブジェクトでありません")
		self.parent = parent	#呼び出し元オブジェクト
		event_attrs = {"from":self}
		self.dummy_event = pygame.event.Event(pygame.USEREVENT,event_attrs)	#ダミーのイベントオブジェクト

		#Tkの呼び出し 
		self.root = Tk.Tk()	#Tkのルートウィンドウ
		self.root.title("設定画面")

	#Changed_by_Windows 
	def additional_chart_setting(self):
		"""
		チャートについての追加設定用画面
		"""
		#(フォーカスのある)Stock_Chartから呼ばれるべき？？Boxのほうがいい？ -> 現在の枠組みだと設定内容を持ってるのがチャートobjだからそっちかな
		if not isinstance(self.parent,(BASE_BOX,Stock_Chart)) :
			raise TypeError("少なくともBOXかチャートobj")
		pass

	def done_additional_chart_setting(self,Nouse):
		"""
		追加設定終了時の完了メソッド
		"""
		self.root.destroy()	#Tkルートウィンドウを破棄
		

	#Changed_by_Windows Setting_Tk_Dialogオブジェクトの枠組みの変革。オブジェクトの生成側が、明示的に呼び出すようにする。
	def initial_chart_setting(self):
		"""
		チャート設定の初期画面。
		株価チャートを入力させる。
		"""
		#ROOTかBOXオブジェクトから呼ばれるべき
		if not isinstance(self.parent,(BASE_BOX,Root_Container)) :
			raise TypeError("引数がBOXオブジェクトあるいはRoot_Containerオブジェクトでありません")
		#TkVariables
		#Changed_by_Windows　デフォルト値の設定に変数を使おう。
		self.security_code_Tkvar = Tk.StringVar()
		self.term_for_a_bar_Tkvar=Tk.IntVar()
		self.term_for_a_bar_Tkvar.set(TERM_DICT["日足"])
		self.download_mode_Tkvar = Tk.IntVar()
		self.download_mode_Tkvar.set(DOWNLOAD_MODE_LOCAL)
		#TkWidgets
		#Entry:証券コード入力欄
		security_code_entry = Tk.Entry(self.root,textvariable=self.security_code_Tkvar)	
		security_code_entry.pack()
		security_code_entry.focus()
		security_code_entry.bind("<Return>",self.done_initial_setting)

		#Changed_by_Windows - ダウンロードモードとサイトの選択機構の変更----------------
		#また、ローカルの場合は関数にバインドさせてサイト設定要素を無効にすべき。
		self.download_site_Tkvar = Tk.IntVar()
		self.download_site_Tkvar.set(DOWNLOAD_SITE_KDB)
		#Radiobutton:データダウンロードについてのモード選択
		download_mode_radiobutton_labelframe = Tk.LabelFrame(self.root,text="ダウンロードモードの設定")
		download_mode_radiobutton_labelframe.pack()
		Tk.Radiobutton(download_mode_radiobutton_labelframe,text="ローカルモード",variable=self.download_mode_Tkvar,value=DOWNLOAD_MODE_LOCAL).pack(side="left")
		Tk.Radiobutton(download_mode_radiobutton_labelframe,text="差分モード",variable=self.download_mode_Tkvar,value=DOWNLOAD_MODE_DIFF).pack(side="left")
		Tk.Radiobutton(download_mode_radiobutton_labelframe,text="通常ダウンロード",variable=self.download_mode_Tkvar,value=DOWNLOAD_MODE_DOWNLOAD).pack(side="left")
		#Radiobutton:データダウンロードについてのサイト選択
		download_site_radiobutton_labelframe = Tk.LabelFrame(self.root,text="データの参照先")
		download_site_radiobutton_labelframe.pack()
		Tk.Radiobutton(download_site_radiobutton_labelframe,text="kdb.com",variable=self.download_site_Tkvar,value=DOWNLOAD_SITE_KDB).pack(side="left")

		#--------------------------------

		#Radiobutton:足ごとの期間の設定ボタン
		term_for_a_bar_radiobutton_labelframe=Tk.LabelFrame(self.root,text="１足あたりの期間")	#足期間設定フレーム
		term_for_a_bar_radiobutton_labelframe.pack()
		for term in TERM_LIST :
			Tk.Radiobutton(term_for_a_bar_radiobutton_labelframe,text=term,value=TERM_DICT[term],variable=self.term_for_a_bar_Tkvar).pack(side="left")
		#Button:OKボタン
		Tk.Button(self.root,text="done",command=self.done_initial_setting).pack()	#Button:入力終了時self.done()が呼ばれる。
		#Tk main_loop
		self.root.mainloop()

	def done_initial_setting(self,NoUse=None):
		"""
		ユーザーによる情報入力完了時に呼び出されるメソッドで、証券コードチェックの後、株価情報のフェッチと保存をし、フェッチしたCSVデータに問題がなければ、チャート描画のためのオブジェクトの作成を行う。

		データのダウンロード : 実際の株価情報を表すCSVデータのフェッチと検証、あるいはコンバートとそのデータの保持を行うのはStock_Chartクラスのインスタンスである。
		データのチェック : そのフェッチとコンバート、あるいは保存の過程で問題があれば、各関連メソッドはFalse値を返し、その場合には作成したオブジェクトを破棄し、エラーダイアログを出した後、このdone()の呼び出しをなかったことにする。（実際にはこのメソッドはただ、その時、「何も変更しない」だけだが。）
		チャート表示領域の確保 : 株価のダウンロードについての諸処理が正常に終了したら、そのデータの保持するStock_Chartオブジェクトにチャート表示領域を提供するためのBOXオブジェクトを生成し、このSetting_Tk_Dialogオブジェクトの生成元のBOXオブジェクトself.parentに関連付ける。
		
		"""
		security_code = self.security_code_Tkvar.get()	#証券コード入力エントリー
		term_num = self.term_for_a_bar_Tkvar.get()	#足期間
		download_mode = self.download_mode_Tkvar.get()
		download_site = self.download_site_Tkvar.get()
		#証券コードのチェック
		if security_code.isdigit() and int(math.log10(int(security_code))+1) == 4 :
			#stock_chartオブジェクト、tabオブジェクトの生成と初期設定
			tab = Tab()
			stock_chart_object = Stock_Chart(security_code,term_num,download_mode,site=download_site) #CSVをフェッチし、データを保持するオブジェクト
			stock_chart_object.set_tab(tab)
			#株価CSVデータのフェッチと保存が成功したらTkrootウィンドウを破棄し、
			if stock_chart_object.download_price_data() :
				box = Container_Box(self.parent,stock_chart_object)	#stock_chartオブジェクトを格納したBOXオブジェクト
				self.parent.add_box(box)	#呼び出し元のBOXに追加
				#buttonを押す
				buttons_for_term = self.parent.get_button_box("buttons_for_term")	#term用のbutton_boxをサーチ
				term_button = buttons_for_term.get_button(term_num)	#選択termのボタンをサーチ
				term_button.dispatch_MOUSEBUTTONDOWN(self.dummy_event)

				self.root.destroy()	#Tkルートウィンドウを破棄
			#Changed_by_Windows エラー処理をしよう
			else :
				tkMessageBox.showerror(message="データのダウンロードに失敗しました。")
		else :
			tkMessageBox.showerror(message="証券コード：数字4桁を入力してください。")


#General Functions-----

#Changed_by_Windows - 色の設定。ラベルの追加
def add_default_buttons(root):
	"""
	"""
	#足期間のショートカットボタン
	button_box = Button_Box(root,"buttons_for_term",color=(255,200,200))
	button_box.add_button(Label_For_ButtonBox("足期間"))
	for term in TERM_LIST :
		button = UI_Button(term,TERM_DICT[term],pressed_term_button)
		button_box.add_button(button)
	root.add_box(button_box)

	#チャートについての詳細設定
	button_box = Button_Box(root,"buttons_for_chart_setting",color=(200,255,200))
	button_box.add_button(Label_For_ButtonBox("チャート設定"))
	button_informations = []	#(id_str,bind_function,swiching)の情報を格納する一時変数
	button_informations.append( ("Y-Prefix",pressed_Y_axis_fix_button,True) )
	button_informations.append( ("Ruler-Default",pressed_set_ruler_default,False) )

	for id_str , bind_function , swiching in button_informations :
		if swiching :
			button = UI_Button(id_str,id_str,bind_function)
		else:
			button = No_Swith_Button(" "+id_str+" ",id_str,bind_function)
		button_box.add_button(button)
	root.add_box(button_box)

def add_default_labels(root):
	"""
	"""
	label_box = Label_box(root)
	label1 = Label(color=(255,0,0))
	label2 = Label("現在時刻：",color=(0,0,255))
	label_box.add_label(label1)
	label_box.add_label(label2)
	root.add_box(label_box)

def pressed_term_button(button):
	"""
	Root_Container名義で新たなStock_Chartオブジェクトを、新たなContainer_Boxに配置して、それをrootの子BOXとして追加する。
	"""
	term_num = button.id
	root = button.get_parent_box().get_father()
	if button.state == False :
		#OFFからONになる時、チャートオブジェクトの生成
		focused_content = root.get_focused_box().get_content()
		#Container_Box,Stock_Chartオブジェクトの生成と設定
		new_container_box = Container_Box(root)
		new_stock_chart = focused_content.inherit(term_num) #フォーカスされているコンテンツから継承
		new_stock_chart.download_price_data()
		#ボックスへの登録
		new_container_box.set_content(new_stock_chart)
		root.add_box(new_container_box)
		return True

	elif button.state == True :
		#ONからOFFになる時、チャートオブジェクトの破棄。
		for container_box in root.get_all_container_box() :
			if container_box.get_content().term_for_a_bar == term_num :
				success = root.remove_box(container_box)
				return success
		raise Exception("予期せぬ動き：該当のコンテナBOXが見つからない")

def pressed_Y_axis_fix_button(button):
	"""
	株価チャートのY軸固定オプション
	"""
	root = button.get_parent_box().get_father()
	focused_box = root.get_focused_box()	#フォーカスのあるコンテンツのBOX
	focused_box.get_content().set_Y_axis_fixed(not button.state)
	focused_box.draw()
	return True

def pressed_set_ruler_default(button):
	"""
	フォーカスチャートの水平ルーラーを規定価格の位置に戻す
	"""
	root = button.get_parent_box().get_father()
	focused_box = root.get_focused_box()
	focused_box.get_content().set_default_horizontal_rulers()
	focused_box.draw()
	return True


#Main Functions-----
def main():
	"""
	1,pygameを初期化
	2,screenサーフェスの作成と設定
	3,メインループを包括するStock_Chart()インスタンスの生成と、そのメインループを呼び出す。
	4,行儀よくexit
	"""
	pygame.init()
	pygame.display.set_caption("株チャートテクニカル分析")
	pygame.display.set_mode(SCREEN_SIZE,pygame.RESIZABLE)
	root = Root_Container()
	root.main_loop()
	pygame.quit()
	sys.exit()


if __name__ == "__main__":
	if DEBUG_MODE:
		print "IN DEBUG MODE"
	main()
