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
import math,sys,urllib2,os
import pygame
from pygame.locals import *
import Tkinter as Tk
import tkMessageBox
from datetime import date as Date
from HTMLParser import HTMLParser

#Global STATICS-----
#About Object Sizese
SCREEN_SIZE = (1000,600)
BUTTON_SIZE = (40,30)
#About General Colors
#FOREGROUND_COLOR = (224,235,235)
#BACKGROUND_COLOR = (0,15,30)
FOREGROUND_COLOR = (0,0,0)
BACKGROUND_COLOR = (255,255,255)
#About Chart Term
TERM_LIST = "月足,週足,日足,前場後場,5分足,1分足".split(",")	#数字は半角
TERM_DICT = dict( zip( (TERM_LIST+range(1,7)),(range(1,7)+TERM_LIST) ) )	#相互参照の列挙体としての辞書。 1:月足 2:週足 3:日足 4:前後場足 5:五分足 6:一分足
TERM2URL_DICT = {"日足":"1d","前場後場":"4h","5分足":"5min","1分足":"minutely"}
#About Local Files
FONT_NAME =  os.path.join(os.path.abspath(os.path.dirname(__file__)),"TakaoGothic.ttf") if os.path.isfile( os.path.join(os.path.abspath(os.path.dirname(__file__)),"TakaoGothic.ttf")) else None 
BOLD_FONT_NAME = os.path.join(os.path.abspath(os.path.dirname(__file__)),"BoldFont.ttf") if os.path.isfile( os.path.join(os.path.abspath(os.path.dirname(__file__)),"BoldFont.ttf")) else None 
CSV_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)),"csv")
#About Download Mode
DOWNLOAD_MODE_LOCAL = 1
DOWNLOAD_MODE_AUTO = 2
DOWNLOAD_MODE_DIFF = 3
DOWNLOAD_MODE_DOWNLOAD = 4
DOWNLOAD_MODE_ETC = 5
DOWNLOAD_SITE_KDB = 10
DOWNLOAD_SITE_ETC = 100
#About Lines On Chart
AA_LINE_COLOR = (200,0,0)
MA_COLOR_DICT = {3:(200,120,0),5:(235,0,235),25:(0,0,255),75:(153,235,27),135:(139,0,0),200:(0,235,235)}
DEFAULT_MA_DAYS_ALL = (3,5,25,75,135,200)
f = ( lambda tup : tuple( [ (day,MA_COLOR_DICT[day],visible) for day,visible in tup ] ) )
DEFAULT_MA_DAYS_DAILY = f( ((3,False),(5,False),(25,False),(75,False),(135,False),(200,False)) ) 
DEFAULT_MA_DAYS_WEEEKLY = f( ((3,False),(5,False),(25,False),(75,False)) )
DEFAULT_MA_DAYS_MINUTELY = f( ((3,False),(5,False),(25,False)) )
#Optional
DEBUG_MODE = 0


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
		self.background_color = BACKGROUND_COLOR
		self.keys = pygame.key.get_pressed()	#キー入力の保存リスト、eventloop()で更新。
		self.looping = True	#メインループのスイッチ
		self.clock = pygame.time.Clock()
		self.fps = 10
		self.child_box_list = []	#すべてのGUI要素を含むリスト
		self._focused_box = None	#操作の対象となっているコンテンツの直轄のBOX
		self.prefocused_box = None
		#イベント用定数
		self.keys_control_chart = (pygame.K_LEFT,pygame.K_RIGHT,pygame.K_UP,pygame.K_DOWN)

		#初期化処理
		self.fill_background()
		add_default_buttons(self)	#デフォルトのボタンを配置
		add_default_labels(self)	#デフォルトラベルの配置
		Setting_Tk_Dialog(self).initial_chart_setting()	 #設定画面の呼び出し
	
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

	def get_button_box(self,id_str):
		for box in self.child_box_list :
			if isinstance(box,Button_Box) and box.id_str == id_str :
				return box
		raise Exception("識別子",id_str,"を持ったButton_boxオブジェクトは見つかりませんでした。")

	def fill_background(self,rect=None):
		self.screen.fill(self.background_color,rect)
		pygame.display.update(rect)

	def draw(self):
		for child_box in self.child_box_list:
			child_box.draw()

	def event_loop(self):
		"""
		イベントを補足します。ルートにおける一般的なキー入力については即時性が必要ないので、pygame.Key.get_pressedを用います。
		それ以外はイベントキューを用います。
		"""
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
		self.bgcolor = (255,255,255)

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
			surface = self.get_surface(bgcolor=self.bgcolor)
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
	def __init__(self,string=None,str_color=None,font=None) :
		self.font = font or pygame.font.Font(FONT_NAME,14)	#文字の描画に用いられるフォント
		self.initial_string = "セッティングにはKEYを押してください。"	#文字列非設定時のデフォルト値
		self.str_color = str_color or (0,0,0)
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
		与えられたサーフェスに、透明な文字列を描画する。
		背景色については親BOXのLabel_BOXオブジェクトの属性値に拠る
		"""
		decoded = unicode(self.string,"utf-8")	#日本語の貼り付けにはデコードが必要。
		text_surface = self.font.render(decoded,True,self.str_color)
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
		self.font = font or pygame.font.Font(FONT_NAME,13)
		self.bold_font = pygame.font.Font(BOLD_FONT_NAME,13)
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
		surface = self.get_surface()
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
	def __init__(self,parent,id_str,font=None,bgcolor=None):
		self.bgcolor = bgcolor or BACKGROUND_COLOR
		self.set_parent(parent)
		self.button_list = []
		self.font = font or pygame.font.Font(FONT_NAME,14)
		self.id_str = id_str
		self.height_prefix = True
		self.width_prefix = False
		self._width = 0		#拡張用
		font_size = self.font.size("あ")
		self.MARGINE = 3
		self._height = font_size[1] + self.MARGINE * 2	#規定値によってデフォルトでは、静的な高さで生成される
		self._left_top = (0,0)	#この値はRoot_Containerオブジェクトによってのみ設定可能
	
	def add_button(self,button_object):
		if isinstance(button_object,(Content_of_ButtonBox)):
			self.button_list.append(button_object)
			button_object.set_parent_box(self)
		else:
			raise TypeError("不正なオブジェクトの代入です。")

	def get_button(self,id):
		for button in self.button_list :
			if button.id == id :
				return button
		raise Exception("id,%s を持つBUttonオブジェクトはありません"%(id_str))

	def get_all_buttons(self):
		"""
		このBOXオブジェクトの格納するボタンオブジェクトのリストself.button_listを返すインターフェイス。
		"""
		return self.button_list

	def draw(self):
		"""
		"""
		rect = self.get_rect()
		surface = self.get_surface(bgcolor=self.bgcolor)
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


class Content_of_ButtonBox(Content):
	"""
	Button_Boxオブジェクトに格納されるコンテンツを定義する為の中間インターフェイスとしてのクラス。
	そのコンテンツオブジェクトに共通するコンテンツ文字列self.string,ボタンid=self.idメンバ変数と、サイズについてのインターフェイス、点の衝突判定処理を、共通に継承されるべきメソッドとして定義している。
	"""
	def __init__(self,string,id_str):
		"""
		すべてのButton_Boxオブジェクトのコンテンツに共通する表示文字列、id値の設定を行う。
		すべてのこのクラスを継承するコンテンツオブジェクトは、コンストラクト時、このメソッドを呼ばねばならない。
		"""
		self.string = unicode(" "+string+" ","utf-8")	#エンコードしとく
		self.id = id_str
	
	def collide_point(self,pos):
		"""
		与えられた引数pos=(x,y)の表す地点がこのクラスを継承するオブジェクトの描画範囲に衝突しているか否かについての判定をするメソッド。真偽値を返す。
		"""
		x = pos[0]
		y = pos[1]
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


class Label_of_ButtonBox(Content_of_ButtonBox):
	"""
	Button_Boxオブジェクトに配置可能なラベルを表すコンテンツオブジェクト。
	多く、そのButton_Boxに設定されるボタンについての構造化された包括的なディスクリプションを表すのに用いられる。
	当然、イベント処理は不要で、即ちpassする。
	"""
	def __init__(self,string):
		Content_of_ButtonBox.__init__(self,string,None)	#IDは不要なので渡さない
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

	def dispatch_MOUSEBUTTONDOWN(self,event):
		"""
		イベント処理は不要
		"""
		pass


class UI_Button(Content_of_ButtonBox):
	"""
	このアプリのユーザーインターフェースにおける"ボタン"を表すオブジェクトで、このオブジェクトは、Root_Containerオブジェクトに関連付けられた(ーつまり、その子BOXである)Button_Boxオブジェクトに関連付けられることにより、Root_Containerからのイベントの補足(シグナル)、及び描画(関数)の呼び出しを受けることができる。
	"""
	def __init__(self,string,id_str,command):
		Content_of_ButtonBox.__init__(self,string,id_str)
		self.command = command	#ボタンが押された時に起動する関数オブジェクト
		self.state = False	#押されているかいないか
		#以下の3つのプロパティはButton_Boxオブジェクトにより描画時、動的に与えられる。また、具体地は親のset_size()を用いる
		self._left_top , _width , _height= (0,0) , 0 , 0
		self.synchronize_with_focuse_content = None	#ボタンstate同期用の関数。self.set_synchro_function()で設定する。

	def draw(self,target_surface,left_top,font):
		"""
		このメソッドの呼び出し元、すなわち、Button_Boxオブジェクトから提供される描画領域としてのサーフェスにボタンを描画する。
		また、この際決定されるボタンサイズ、親Button_Boxオブジェクトにおける座標位置、についての情報をset_zize()により納する。
		"""
		button_color =  (255,0,0) if self.state else (255,255,255)
		surface = font.render(self.string,True,(0,0,0),button_color)
		pygame.draw.rect(surface,(0,0,0),surface.get_rect(),1)
		target_surface.blit(surface,left_top)
		#動的に決定される描画領域についての保存。self.collideなどで用いられる。
		w , h = surface.get_width() , surface.get_height()
		self.set_size(left_top,w,h)

	def set_synchro_function(self,func):
		"""
		状態同期の為の関数の定義の為のインターフェイス。
		"""
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

	def set_state(self,state):
		self.state = state

	def get_state(self):
		return self.state

	def switch_state(self):
		"""
		ボタンの状態を変える-逆転させる。
		"""
		self.state = not self.state

	def dispatch_MOUSEBUTTONDOWN(self,event):
		"""
		ボタンの状態を変える前に定義されたコマンドを実行し、そのコマンドが正常に実行されたら、ボタンの状態を変える。
		"""
		success = self.command(self) 
		if success :
			self.switch_state()
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
	このオブジェクトは内部に「価格データ」を格納し、描画関数が呼び出されるたびに座標値へ変換する。
	これは価格の座標値への変換式が動的に生成されるため避けがたい事情がある。

	また、このオブジェクトは「バーのタイプ」を一種のid情報として格納する。
	親チャートオブジェクトはこのタイプの値に基づいて、多数格納されたこのオブジェクト郡から目的のバーを検索することになる。
	"""
	def __init__(self,parent,ruler_type,price,color):
		"""
		"""
		if not isinstance(parent,Stock_Chart) or ( not ruler_type in ("H","L","M") ) :
			raise Exception("不正な型の引数です: parent=%s,ruler_type=%s" % (parent,ruler_type))
		self.type = ruler_type
		self.parent = parent	#親となるチャート
		self.price = price
		self.color = color
		self._drawing_rect = None	#描画範囲を表現するRectで、描画時設定される。インターフェイスを用いてアクセスする。

	def draw_to_surface(self,surface,font):
		"""
		水平ルーラーを描画するメソッド。
		引数として与えられたサーフェスに直接描画する
		このメソッドの呼び出し元は、このメソッド終了後、サーフェスをY軸方向にフリップするのでテキストは予めフリップしておく必要がある
		"""
		drawing_height = self.parent.price_to_height(self.price)
		price_renderd = font.render(unicode(str(self.price),"utf-8"),True,FOREGROUND_COLOR)
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

	def get_price(self):
		return self.price

	def collide(self,pos):
		"""
		与えられたposとこのオブジェクトの価格表示領域が衝突しているか否かを返す
		"""
		rect = self.get_drawing_rect()
		if rect.collidepoint(pos) :
			return True
		else :
			return False


class Chart_Analyser(object):
	"""
	チャートアナライザー。よく決まってない。あとで実装する機能が増えてから実際の構造は考える。
	"""
	def __init__(self):
		pass


class Price_Converter(Chart_Analyser):
	"""
	「価格データの系列を用いて、そのデータを均衡化したようなデータの系列を一意に算出する」ような機能の実装されたすべてのクラスの基底クラス。
	このクラスを継承するすべてのクラスは、Stock_Chartオブジェクトに関係づけられることを前提としています。
	このクラスの子クラスのオブジェクトは、calc()の呼び出しによってそのデータの算出を行い、draw()によってそのデータをグラフィカルに表現します。
	このクラスの子クラスのオブジェクトの有するデータ情報の実態であるlistオブジェクト(実際には効率化のためタプルに変換して格納される)は、親Stock_Chartオブジェクトの有する、価格データの実態たるstock_price_listと完全に対応したデータを格納している。
	即ち、ある値indexにおいてstock_price_list[index]の値は、このクラスのインスタンスのもつデータリストのlist[index]の値と完全に関連づいている
	なお、このデータリストにおいて、「無効な値」はint値「0」として定義され、格納されている。
	"""
	def __init__(self,parent,color,visible):
		"""
		親Stock_Chartオブジェクト、描画に用いるRGB値、可視不可視についての設定。
		"""
		if not isinstance(parent,Stock_Chart) :
			raise Exception("親がStock_Chartオブジェクトでありません")
		self.parent = parent	#親のStock_Chartオブジェクト
		self.color = color 
		self.visible = visible

	def set_visible(self,visible=True):
		self.visible = visible

	def set_imvisible(self):
		self.visible = False

	def is_visible(self):
		return self.visible

	def get_value(self,index):
		"""
		すべての子クラスが実装すべきインターフェイス。
		引数に渡されたindex値に対する価格データ値、valueを返す。
		このindex値は親Stock_Chartオブジェクトの有するstock_price_listにおけるindex値に完全に対応する。
		"""
		return self.datalist[index]	#変数名の関係でオーバーライドはご自由に
	
	def calc(self):
		"""
		すべての子クラスがオーバーライドすべきメソッド
		このメソッドでこのオブジェクトの目的とする価格データの算出及びリストオブジェクへの格納を行う。
		なお、効率化の為にタプル化することが推奨される。
		"""
		raise Exception("オーバーライドしてください")

	def draw_to_surface(self,surface):
		"""
		self.calc()によって算出、格納された価格データ情報に基づいて、与えられたサーフェスに描画するメソッド。
		データリストのインターフェイスが同じなので描画関数は共有できる。
		"""
		raise Exception("変数名を絶対実装すべきインターフェイスとして定義するわけにもいかんのでOverrideしてください。")


class Moving_Average(Price_Converter):
	"""
	移動平均についてのデータの算出と描画を担当するオブジェクトで、それを定義するためのいくつかのプロパティを有する。
	"""
	def __init__(self,parent,days,price_type,color,visible=True):
		"""
		"""
		Price_Converter.__init__(self,parent,color,visible)
		self.days = days	#移動平均日数
		self.price_type = price_type	#終値その他の価格タイプを表す文字列"C","H"他
		self.MAlist = []	#移動平均値の保管リスト
		self.least_days = round( self.days * 2/3 )	#指定日数の3/2以上のデータ数が確保できれば許容
		#移動平均値の算出と格納
		self.calc()

	def get_MA_days(self):
		"""
		何日の移動平均を表現するオブジェクトかを返すインターフェイス
		"""
		return self.days

	def get_value(self,index):
		"""
		引数indexで定義される移動平均値を返す。indexの値は親Stock_Chartオブジェクトのprice_listにおけるindex値と同期されている。
		ただし、無効な値としてそれが定義されていたとき、仮の値として0を返す。
		"""
		return self.MAlist[index]

	def calc(self):
		"""
		全チャート期間における移動平均値を算出し、self.MAlistに格納する。
		"""
		MAlist = []	#一時変数。最後にタプル化したものをself.MAlistに格納
		price_list = self.parent.stock_price_list
		target_index = self.parent.pricetype2index(self.price_type)	#定義された価格タイプを表すprice_listにおけるindex値
		f = ( lambda x : MAlist.append(0) )	#一時関数。無効な値としてindex値に対応させておくためのユーティリティ
		#移動平均値の算出。算出可能なのは、index値が少なくともself.days以上の時。
		for list_index in range(0,len(price_list)+1) :
			if list_index <= self.days :
				#price_listとindex値を完全に同期する為に0を加えておく
				f(0)
			else :
				start , end = list_index-self.days+1 , list_index
				#今のlist_indexからself.days前までにおける、(0でない)(定義された価格種類の)価格値を集計する。
				moving_prices = [ a_price_list[target_index] for a_price_list in price_list[start:end+1] if a_price_list[target_index] ]

				#最低限の要素を満たしているかチェックした後、移動平均値の算出
				if len( moving_prices ) >= self.least_days :
					moving_average = float( sum(moving_prices) ) / len(moving_prices)
					MAlist.append( round(moving_average) )
				else :
					f(0)	#無効な値として0を格納しておく。
		self.MAlist = tuple(MAlist)

	def draw_to_surface(self,surface):
		"""
		self.calc()によって算出、格納された価格データ情報に基づいて、与えられたサーフェスに描画するメソッド。
		"""
		start , end = self.parent.get_drawing_index()
		#描画範囲に含まれるすべての移動平均日において、その移動平均値が0でないならpoint_listに格納
		f = ( lambda  index,price : ( self.parent.get_index2pos_x(index) , self.parent.price_to_height(price) ) )
		point_list = [ f(index,self.MAlist[index]) for index in range(start,end+1) if self.MAlist[index] ]
		pygame.draw.aalines(surface,self.color,False,point_list)


class Actual_Account_Analyser(Price_Converter):
	"""
	株の「実質的価値」を分析、描画するためのクラス。
	中身は単純で、２つ以上の移動平均情報からその平均値を算出するだけ。
	だが少なくともただ１通りの情報から端的に算出された指標よりも、重み分けのなされたより多くの情報源から算出された指標のほうが信ぴょう性は認め得よう。
	"""
	def __init__(self,parent,color,visible=True):
		Price_Converter.__init__(self,parent,color,visible)
		if not isinstance(parent,Stock_Chart) :
			raise Exception("親コンテンツオブジェクトが不正な型です")
		self.AAlist = ()
		self.least_numof_MA = 3		#実質的価値の算出に最低限３つはMAのデータがほしい

	def get_value(self,index):
		"""
		index値に対するAAlistの値を返すインターフェイス
		"""
		return self.AAlist[index]
	
	def calc(self,MAlist):
		"""
		実質的価値を表現する値の算出と格納を行うメソッド。
		ここで生成されるデータリストAAlistのindex値は、親Stock_Chartオブジェクトにおけるstock_price_listにおけるindex値に完全に対応する。
		"""
		AAlist = []
		endindex = len(self.parent.stock_price_list)
		numof_MA = len(MAlist)
		for index in range(endindex+1) :
			MA_values = [ MAlist[i].get_value(index) for i in range(numof_MA) if MAlist[i].get_value(index) ]
			numof_val = len(MA_values)
			if numof_val >= self.least_numof_MA :
				actual_account_price = sum(MA_values) / float(numof_val)
				AAlist.append(int(actual_account_price))
			else :
				AAlist.append(0)	#無効な値として0を定義

		self.AAlist = tuple(AAlist)	#Tuple化して登録

	def draw_to_surface(self,surface):
		"""
		self.calc()によって算出、格納された価格データ情報に基づいて、与えられたサーフェスに描画するメソッド。
		"""
		start , end = self.parent.get_drawing_index()
		#描画範囲に含まれるすべての移動平均日において、その移動平均値が0でないならpoint_listに格納
		f = ( lambda  index,price : ( self.parent.get_index2pos_x(index) , self.parent.price_to_height(price) ) )
		point_list = [ f(index,self.AAlist[index]) for index in range(start,end+1) if self.AAlist[index] ]
		pygame.draw.aalines(surface,self.color,False,point_list)


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

	#データのフェッチと変換と格納# 
	これを一挙に担うインターフェイスとしてのメソッドは、download_price_data()で、これはまずこのオブジェクトに定義された、ダウンロードモードdownload_modeから、どの方法でＣＳＶファイルをインクルードし、あるいはそのリソース源を得るか。ということについて判断する。
	1,DOWNLOAD_MODE_LOCAL:データをもっぱらローカル環境からインクルードする。トラフィックのロスがないが、最新情報としての信ぴょう性がない。
	2,DOWNLOAD_MODE_DIFF:まずローカル環境のファイルを捜索し、それがないか、あるいは古いタイムスタンプのファイルであると判定されたら定義されたdownload_siteからそれをフェッチする。
	3,DOWNLOAD_MODE_DOWNLOAD:ローカルのファイルのいかんに問わず、データを指定されたさいとからフェッチする。
	続いて、実際のデータのインクルードが行われる。ローカルからのインクルードの場合、使われるメソッドは、download_price_data_from_file()で、これは単純にインクルードを行う。べつリソースからのダウンロードの場合、download_price_data_from_web()が呼ばれ、ここにおいて定義されたサイトself.download_siteが参照され、実際のデータのロケーターを算出する。
	で、それぞれのダウンロードメソッドは、それぞれ、対象のリソース名、すなわち前者では、ファイル名、後者ではURLを自動生成し、これに対して実際のインクルード処理をおこなう。
	で、その処理が正常に終了したら、続いて「その個々のメソッド内で」convert_csv_data()メソッドが呼ばれる。このメソッドは、csvデータを表す(つまり、今インクルードされた)文字列を引数に取り、これをしかるべきデータ型に変換。そしてこれをこのオブジェクト内のstock_price_listメンバ変数に格納する。
	最後にdownload_price_data()メソッドに制御を戻し、このデータの最終チェックを行って、正しく処理が完了していればTrueを返す。
	#階層図 :
	1, download_price_data = 最上層のデータのフェッチ、変換、格納、ローカルへの吐き出し、タブとの同期、エラー補足、についてのインターフェイス。
		->2, read_from_tab() : タブに既にデータがあれば読み込み。
		->3, download_price_data_from_file : ファイルからデータを読み出し、変換、格納。
				->4, convert_self_to_filename : ファイル名の取得
						-> 6,convert_csv(fromfile=True) : csvの変換と格納。
		->3, download_price_data_from_web : インターネットからデータをフェッチする際の中間インターフェイス。ここで種差を吸収する。
			->4, download_price_data_from_kdb : ダウンロードサイトkbdからデータをフェッチ、変換、格納。
				->5, get_urls : urlの取得。
					-> 6,fetch_csv : csvデータのフェッチ
						-> 7,convert_csv() : csvの変換と格納
		->6,synchro_with_tab() : タブと同期

	エラー文の出力は、処理階層における末端の処理部分が担う。それより下は単にFalseを階層的に返し続け、呼び出しもとにそれを返す。
	"""
	def __init__(self,security_code,term_num,download_mode,site=DOWNLOAD_SITE_ETC):
		"""
		"""
		#株価情報についてのメンバ変数
		Content.__init__(self)
		self.stock_price_list = []	#ダウンロードされた株価情報。fetch_csv()メソッドにより入力
		self.security_code = security_code	#証券コード文字列
		self.security_name = ""	#証券名。CSVのフェッチと保存の際に設定される
		self.term_for_a_bar = None	#５分足、１０分足、日足、週足、月足のいずれの情報か
		self.term_for_csv = None	#週足、月足、は日足CSVデータから算出するため、CSVファイルの実態は日足データとなる

		#定められたインターフェイスによってのみ扱われるべき変数
		#チャート描画に関するメンバ変数
		self._zoom_scale = 1 	#イベント用
		self.zoom_scale_step = 0.5
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
		self.AA_analyser = None		#実質的価値の解析オブジェクト

		#データの保存とフェッチに関するメタ情報を格納するメンバ変数
		self.download_mode = download_mode	#ローカル環境に株価データがあればそれを用いる
		self.download_site = site
		self.file_header = []	#ローカルファイルに保存するためのファイルヘッダ

		#イベントに関するフラグ変数
		self.focused_horizontal_ruler = None #Horizontal_Rulerオブジェクトが格納される

		#静的な値の初期化設定メソッド
		self.set_term(term_num)	#２つのterm変数のセッターメソッド
		self.set_zoom_scale()	#ズームスケールのデフォルト値の設定

	def initialize_data(self,reload_data=False):
		"""
		動的なデータに関する初期化処理。
		1,対象データのフェッチ、コンバート、格納を行う
		2,設定された株価データをもとに、移動平均オブジェクトmoving_averagesの設定。
		3,設定されたmoving_averagesを元に、実質的価値算出オブジェクトAA_analyserの設定。
		処理に失敗した場合はこの関数はFalseを返し、正常に終了すればTrueを返す。

		また、いつでも再初期化可能である。
		なお、データそのものを外部リソースから再読み込みする場合は、self.download_price_data()メソッドを単独で用いるか、このメソッドのreload引数を用いること。
		"""
		#Tabに関する設定:Tabが設定されていなければオブジェクトを生成し、関連付ける。
		if not self.get_tab() :
			tab = Tab()
			self.set_tab(tab)
		#データのフェッチと格納
		#タブにデータが存在すればそこから読み込み、なければフェッチする
		if reload_data or not self.read_from_tab() :
			#データのフェッチに失敗すればFalseを返す
			if not self.download_price_data() :
				return False
		#チャート上オシレーターの初期化
		self.set_default_moving_averages()
		self.set_AA_analyser()
		return True

	def get_moving_averages(self):
		"""
		関連付けられた移動平均オブジェクトのリストself.moving_averagesを返すインターフェイス。
		"""
		return self.moving_averages

	def get_AA_analyser(self):
		"""
		関連づけられた実質的価値算出オブジェクトを返すインターフェイス。
		"""
		return self.AA_analyser

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

	def set_price_data(self,data):
		"""
		self.stock_price_listのセッターメソッド。
		drawing_indexの設定もここで行う。
		"""
		if isinstance(data,(list,tuple)) and data :
			self.stock_price_list = tuple(data)
			self.set_drawing_index( end =len(data) -1 )

	def download_price_data(self):
		"""
		CSVデータのダウンロードを行うインターフェイスです。
		このメソッドは、設定されたダウンロードモード、データリソースのダウンロード元、に基づいて、実際のデータのフェッチと格納を行う子downloadメソッドを呼び出します。
		その子downloadメソッド郡は、内部でデータの取り込み作業を行う諸関数群を呼び出し、取り込まれた株価データを表現するテキストデータはそれをこのプログラムに適合するデータ型に変換するconvertメソッドを通り、最終的なデータの調整、確認の後、set_price_dataメソッドによって実際に生きた形で格納されます

		つまるところ、このメソッドは、ダウンロードモード及びリソース先の分岐の選択から、実際のデータのフェッチ、変換、確認、格納、あるいはTABへの動機、ひいては日足の週足への変換まで、データの直接的な設定に関するおおよその処理のほとんどすべての面倒を見ます
		"""
		#定義されたダウンロードモードに基づく処理の分岐
		if self.download_mode == DOWNLOAD_MODE_LOCAL :
			#ローカルモード
			if not self.download_price_data_from_file() :
				return False
		elif self.download_mode == DOWNLOAD_MODE_AUTO :
			#オートモード:ローカルにファイルがあればそのデータを使い、さもなくばフェッチする。
			if self.exist_stock_price_file() :
				if not self.download_price_data_from_file() :
					return False
			else :
				if not self.download_price_data_from_web() :
					return False
		elif self.download_mode == DOWNLOAD_MODE_DIFF :
			#差分ダウンロード:ファイルが存在し、且つ最新の状態ならそれを用い、さもなくばwebからダウンロード。
			if self.exist_stock_price_file(check_latest=True) :
				if not self.download_price_data_from_file() :
					return False
			else :
				if not self.download_price_data_from_web() :
					return False
		elif self.download_mode == DOWNLOAD_MODE_DOWNLOAD :
			#強制ダウンロードモード。
			if not self.download_price_data_from_web() :
				return False
		else :
			raise Exception("未定義のモードです")

		self.synchro_with_tab()	#tabに同期
		#週足、月足についてはtabを介して変換されたデータを得る。
		if TERM_DICT[self.term_for_a_bar] in ("週足","月足") :
			if not self.read_from_tab() :
				tkMessageBox.showerror(message="tabに週足または月足のデータが保存されていません。予期せぬ動きです")
				return False
		#最後のエラー補足。株価データが正常かを確認
		if not self.stock_price_list :
			return False

		return True
	
	def download_price_data_from_file(self):
		"""
		ローカルファイルから株価情報をインポートします。失敗すればFalseを返します
		"""
		#ファイルの確認
		if not self.exist_stock_price_file() :
			tkMessageBox.showerror(message="ローカルに対象のファイルが存在しません。")
			return False
		#ファイル名の生成と読み込み、変換。
		filename = self.convert_self_to_filename()
		fileobj = open(filename,"r")
		csv_text = fileobj.read()
		fileobj.close()
		price_list = []
		if not self.convert_csv_data(csv_text,price_list,from_file=True):
			return False	#csvの変換の失敗
		self.set_price_data(price_list)	#価格データの保存
		return True

	def exist_stock_price_file(self,check_latest=False):
		"""
		このオブジェクトに適合する株価データがローカル環境に保存されているかどうかを返す
		また、オプション引数latestに真値が与えられた時、それが最新のデータかどうかも確認する。
		"""
		existing = os.path.isfile(self.convert_self_to_filename())
		if existing and check_latest :
			#タイムスタンプを見て今日更新されたものであればTrue、さもなくばFalseを返す
			epoctime = os.stat(self.convert_self_to_filename()).st_mtime
			date = Date.fromtimestamp(epoctime)
			today = Date.today()
			return today == date
		else :
			return existing
	
	def convert_self_to_filename(self):
		"""
		このオブジェクトをその意味するファイル名に変換する
		"""
		filename = CSV_DIR + "/%s-T%s.csv" % (self.security_code,TERM2URL_DICT[TERM_DICT[self.term_for_csv]])
		return filename

	def download_price_data_from_web(self):
		"""
		オンラインからのデータのフェッチのための中間インターフェイス。諸所のサイトにおける種差はここで吸収する。
		"""
		if self.download_site == DOWNLOAD_SITE_KDB :
			if not self.download_price_data_from_kdb() :
				return False
		else :
			raise Exception("未定義のサイトです")
		self.save_csv_to_local()	#ローカルへ保存
		return True

	def download_price_data_from_kdb(self):
		"""
		k-db.comよりCSVデータのフェッチとその変換、格納を行う
		"""
		url_list = []
		#urlの設定
		if TERM_DICT[self.term_for_csv] in ("日足","前場後場") :
			url_term_phrase = TERM2URL_DICT[TERM_DICT[self.term_for_csv]]
			if url_term_phrase :
				url_term_phrase = "/" + url_term_phrase
			for year in range(2016,2013,-1) :
				url = "http://www.k-db.com/stocks/%s-T/%s/%d?download=csv" % (self.security_code,url_term_phrase,year)
				url_list.append(url)
		else :
			url_list = self.get_urls(self.term_for_csv)
			if url_list == False :
				tkMessageBox.showerror(message="kdb.comについて、分足のデータに関するurlの自動補足ができませんでした。")
				return False
		#CSVのフェッチとコンバート、保存を行い、何らかのエラーが出た時にはFalseを返す。
		price_list = []
		for url in url_list:
			csv_text = self.fetch_csv(url)
			if not ( csv_text and self.convert_csv_data(csv_text,price_list) ) :
				return False	#CSVテキストが異常か、その変換に失敗した
		price_list.reverse()	#逆順、つまり日時において昇順にします
		self.set_price_data(price_list)	#データの登録
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
		if tab and tab.data_in_tab(self.term_for_a_bar):
			data = tab.get_data(self.term_for_a_bar)
			self.set_price_data(data)
			return True
		else :
			return False

	def fetch_csv(self,url):
		"""
		定義されたulrから株価データをCSV形式でフェッチする。
		正常にフェッチされた場合にはそのテキストデータを返り値として返す。
	さもなくばー即ち、そのCSVデータのダウンロードに失敗したか、あるいはそのフェッチされた文章データが予期されるべき形式をとっていなかった場合、その時には、False値を返す。
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
			tkMessageBox.showerror(message="%s : CSVのダウンロードに失敗しました。" % (url))
			return False
		csv_text = unicode(respose.read(),"Shift-Jis").encode("utf-8")	#Shift-JisからUnicode文字列へ
		if DEBUG_MODE :
			print csv_text
			debug_file = os.path.join(os.path.abspath(os.path.dirname(__file__)),"debug.txt")
			open(debug_file,"w").write(csv_text)
			print "フェッチしたファイル debug.txt をプロジェクトディレクトリに生成しました。"
		#csv_textのチェック。問題があればエラー文を表示し、Falseを返す。
		if not csv_text : 
			tkMessageBox.showerror(message="csv_textが空な文字列です。データのフェッチに失敗したようです。")
			return False
		return csv_text

	def convert_csv_data(self,csv_text,price_list,from_file=False):
		"""
		引数に与えられたCSV文章を数値型にコンバートして、与えられたリストオブジェクトへの参照、price_listに格納する。
		また、同時にデータフォーマットのチェックを行い、予期せぬデータであった場合はFalse値を返す。

		CSV１行目と２行目の書式:
		1: 2315-T,JQスタンダード,SJI,日足
		2: 日付,始値,高値,安値,終値,出来高,売買代金
		日足以外
		2:日付,時刻,始値,高値,安値,終値,出来高,売買代金
		"""
		if not isinstance(price_list,list) :
			raise Exception("不正な引数です")
		i = 1 	#行数を表す一時変数。
		is_daily_data = ( TERM_DICT[self.term_for_csv] == "日足" )	#日足データであるか否か
		for line in csv_text.split("\n") :
			tmp_list = line.split(",")	#CSV文章の各行をリスト化
			#１行目:予期される正しいCSV文章かのチェックと株名の保存
			if i == 1 :
				#サイトの構造変更の為チェックができなくなった
				"""
				if ( not tmp_list[0] == str(self.security_code)+"-T" ) or ( not tmp_list[3].strip() == TERM_DICT[self.term_for_csv] ) :
					tkMessageBox.showerror(message="予期せぬデータの書式です。デバッグ情報を確認してください。")
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
				"""
				i = i + 1
				continue
			#3行目以降:第２フィールド以下をintに変換してprice_listにappend
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
						csv_converted_list.append(int(float(tmp_list[field_num])))
#						csv_converted_list.append(int(tmp_list[field_num]))
				price_list.append( tuple(csv_converted_list) )
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
		turnover_index , amount_index = self.pricetype2index("T") , self.pricetype2index("A")
		for index in range(0,len(daily_list)) :
			date = self.get_date2int_list(index)	#[year,month,day]のリスト
			if Date(date[0],date[1],date[2]).weekday() == 0 :	#月曜なら
				tmp_list = daily_list[index:index+5]
				high , low , price_range = self.get_price_range(tmp_list)
				opning , closing = self.get_opning_closing_price(tmp_list)
				date_str = "%s〜%s" % (tmp_list[0][0],tmp_list[-1][0][tmp_list[-1][0].find("-")+1:])
				turnover = sum( [ ls[turnover_index] for ls in tmp_list] )
				amount_ofmoney = sum( [ ls[amount_index] for ls in tmp_list] )
				l = (date_str,opning,high,low,closing,turnover,amount_ofmoney)
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
		#実質的価値表現線の描画
		surface_drawn_actual_account = self.draw_actual_account(surface_size)
		#出来高の描画
		surface_drawn_turnover = self.draw_turnover(surface_size,font)
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
		surface.blit(surface_drawn_turnover,(0,0))
		surface.blit(surface_drawn_axis,(0,0))
		surface.blit(surface_drawn_yaxis,(0,0))
		surface.blit(surface_drawn_additonal_information,(0,0))
		surface.blit(surface_drawn_additonal_setting_info,(0,0))
		surface.blit(surface_drawn_horizontal_rulers,(0,0))
		surface.blit(surface_drawn_candle,(0,0))
		surface.blit(surface_drawn_moving_average,(0,0))
		surface.blit(surface_drawn_actual_account,(0,0))

	def get_drawing_size(self):
		"""
		"""
		zoom_scale = self.get_zoom_scale()
		candle_width = int(round(zoom_scale * 4))
		padding_size = int(round(zoom_scale * 4))
		return candle_width,padding_size
	
	def get_surface(self,surface_size,color_key=BACKGROUND_COLOR):
		"""
		サーフェスを得るためのユーティリティ関数。
		チャートの描画に関しては、諸所の要素を諸所の描画メソッドにおいて描画し、そのサーフェスを持ち寄る形を取るから、透明設定が必要である
		通常、背景色の設定は背景色として静的に定義して問題はないが、背景色を前景として描画しうる余地を残してオプション引数を設定している。
		"""
		surface = pygame.Surface(surface_size)
		surface.set_colorkey(color_key)
		surface.fill(color_key)
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
			line_width = int(zoom_scale * 2)
			pygame.draw.line(surface,candle_color,line_start_pos,line_end_pos,line_width)
		surface = pygame.transform.flip(surface,False,True)
		return surface

	def set_default_moving_averages(self):
		"""
		デフォルトの移動平均線の登録を行う
		"""
		self.moving_averages = []	#初期化
		if TERM_DICT[self.term_for_a_bar] in ("日足","前場後場") :
			ma_days = DEFAULT_MA_DAYS_DAILY
		elif TERM_DICT[self.term_for_a_bar] in ("1分足","5分足") :
			ma_days = DEFAULT_MA_DAYS_MINUTELY
		elif TERM_DICT[self.term_for_a_bar] in ("週足") :
			ma_days = DEFAULT_MA_DAYS_WEEEKLY
		for day,color,visible in ma_days :
			MA = Moving_Average(self,day,"C",color)
			if not visible :
				MA.set_imvisible()
			self.moving_averages.append(MA)

	def draw_moving_average(self,surface_size):
		"""
		移動平均線の描画
		MAオブジェクトの中でself.index_posX_tableを使います。
		"""
		surface = self.get_surface(surface_size)
		start_index , end_index = self.get_drawing_index()
		#移動平均値の算出と描画
		for MA in self.moving_averages :
			if MA.is_visible() :
				MA.draw_to_surface(surface)

		flipped_surface = pygame.transform.flip(surface,False,True)	#pygameでは(0,0)が左上なのでフリップ
		return flipped_surface

	def set_AA_analyser(self) :
		"""
		実質的価値の分析を担当するActual_Account_Analyserクラスを生成し、このオブジェクトに登録する。
		また、このメソッド内でActual_Account_Analyserのcalc()を呼び出し、実質的価値を表す株価の算出もすます。
		"""
		if len(self.moving_averages) < 3 :
			print "Error : 実質的価値の算出に用いる移動平均オブジェクトオブジェクトが十分な数Stock_Chartオブジェクトに登録されていません。"\
				"\n実質的価値の算出を中止します。"
			return False

		color = (255,100,50)
		AA_analyser = Actual_Account_Analyser(self,color)
		AA_analyser.calc(self.moving_averages)
		self.AA_analyser = AA_analyser

	def draw_actual_account(self,surface_size):
		"""
		"""
		surface = self.get_surface(surface_size)
		if self.AA_analyser.is_visible() :
			self.AA_analyser.draw_to_surface(surface)

		flipped_surface = pygame.transform.flip(surface,False,True)	#pygameでは(0,0)が左上なのでフリップ
		return flipped_surface

	def draw_turnover(self,surface_size,font):
		"""
		出来高の描画
		"""
		surface = self.get_surface(surface_size)
		#出来高リストの生成
		start , end = self.get_drawing_index()
		turnover_index = self.pricetype2index("T")
		turnover_list = [ price_list[turnover_index] for price_list in self.stock_price_list[start:end+1] ]
		#出来高の価格幅の算出
		#出来高の基本参考値の算出。最近の0でない出来高値を参考値とする
		f = ( lambda x : turnover_list[x] or f(x-1) )
		high = low = f(-1)
		for turnover in turnover_list :
			if turnover == 0 :
				continue
			elif turnover > high and turnover/20 < high :
				high = turnover
			elif turnover < low and turnover*20 > low :
				low =turnover
		#convert_scale,price_to_heightの生成
		turnover_range = high - low
		convert_scale =  float(surface_size[0]) / turnover_range
		turnover_to_height = ( lambda price : round(( price * convert_scale ) - ( low * convert_scale )) )
		#横線の描画
		"""
		for i in range(1,6):
			price = turnover_range * (float(i)/6) + low
			y = turnover_to_height(price)
			pygame.draw.aaline(surface,(255,200,200),(0,y),(surface_size[0],y))
		"""
		#出来高の描画。self.stock_price_listのindex値とturnover_listのindex値を同期しながら大きくしていく。
		now_index = start
		candle_width , padding = self.get_drawing_size()
		for turnover in turnover_list :
			x = self.get_index2pos_x(now_index)
			height = turnover_to_height(turnover)
			rect = pygame.Rect((x-(candle_width/2),0 ),(candle_width,height))
			pygame.draw.rect(surface,(255,200,200),rect,candle_width)
			now_index += 1

		flipped = pygame.transform.flip(surface,False,True)
		return flipped

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
		#一時関数 : 適当な間隔で描画するにはこの関数に適当な引数を与えるだけで良い。
		def f(string,color,right):
			rendered = font.render(unicode(string,"utf-8"),True,color)
			right = right - ( rendered.get_width() + side_padding/2 )
			surface.blit(rendered,(right,v_padding))
			return right
		#描画
		if self._Y_axis_fixed == True :
			string , color = "Y軸固定" , (100,100,100)
			right = f(string,color,right)
		for MA in self.moving_averages :
			days = "MA-%d" % (MA.days)
			color = MA.color if MA.is_visible() else FOREGROUND_COLOR
			right = f(days,color,right)
		#Actual-Account
		AA = self.AA_analyser
		string = "AA-line" 
		color = AA.color if AA.is_visible() else FOREGROUND_COLOR
		right = f(string,color,right)
			 
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

	def get_horizontal_ruler(self,ruler_type):
		"""
		水平ルーラーのタイプを表現する文字列"H"/"L"/"M"を引数に、そのルーラータイプで定義されたHorizontal_Rulerオブジェクトを返します。
		"""
		if not ruler_type in ("H","L","M") :
			raise Exception("不正な引数です")
		for ruler in self.horizontal_rulers :
			if ruler.type == ruler_type :
				return ruler
		raise Exception("指示された要素が見つかりませんでした")

	def set_horizontal_rulers_price(self,ruler_type,price):
		"""
		引数で指示された水平ルーラータイプで定義されたルーラーオブジェクトの価格を設定するインターフェイス
		"""
		ruler = self.get_horizontal_ruler(ruler_type)
		ruler.set_price(price)

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
		high_ruler = Horizontal_Ruler(self,"H",high_price,(255,100,100))
		low_ruler = Horizontal_Ruler(self,"L",low_price,(100,100,255))
		close_ruler = Horizontal_Ruler(self,"M",last_day_closing_price,(100,255,100))
		self.horizontal_rulers.append(high_ruler)
		self.horizontal_rulers.append(low_ruler)
		self.horizontal_rulers.append(close_ruler)

	def set_horizontal_rulers_prices_default(self):
		"""
		水平ルーラーの価格状態をデフォルトー即ち「描画領域中の最高値」、「描画領域中の最安値」、「最近の終値」に再設定します。
		"""
		start , end = self.get_drawing_index()
		high_price , low_price , price_range = self.get_price_range(self.stock_price_list[start:end])
		last_day_closing_price = self.stock_price_list[-1][self.pricetype2index("C")]
		#Do setting
		self.set_horizontal_rulers_price("H",high_price)
		self.set_horizontal_rulers_price("L",low_price)
		self.set_horizontal_rulers_price("M",last_day_closing_price)

	def set_middle_horizontal_rulers_price_center(self):
		"""
		中間の水平ルーラーとして定義されているルーラーオブジェクトの価格を、
		定義されている高値のルーラーと安値のルーラーのちょうど中間値に来るように再定義します。
		"""
		high_ruler_price = self.get_horizontal_ruler("H").get_price()
		low_ruler_price = self.get_horizontal_ruler("L").get_price()
		average = float( high_ruler_price + low_ruler_price ) / 2
		#Do setting
		self.set_horizontal_rulers_price("M",float(average))
	
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
			pygame.draw.line(surface,FOREGROUND_COLOR,(0,pos_y),(surface_width,pos_y),1)	#横線
			text_surface = font.render(str(i),True,FOREGROUND_COLOR)
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
		if self.term_for_a_bar == TERM_DICT["日足"] :
			drawn_surface = self.draw_y_daily_axis(surface_size,font)
		elif self.term_for_a_bar == TERM_DICT["前場後場"] :
			drawn_surface = self.draw_y_sessionly_axis(surface_size,font)
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
		月単位で縦線を描く
		"""
		if self.get_zoom_scale() >= 1.5 :
			return self.draw_y_sessionly_axis(surface_size,font)
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

	def draw_y_sessionly_axis(self,surface_size,font):
		"""
		前後場足用の縦線描画メソッド
		週単位で描く。
		"""
		if self.get_zoom_scale() <= 0.5 :
			return self.draw_y_daily_axis(surface_size,font)
		surface = self.get_surface(surface_size) 
		start_index , end_index = self.get_drawing_index()
		for index in range(start_index,end_index+1,2) :
			date = self.get_date2int_list(index)
			if Date(date[0],date[1],date[2]).weekday() == 0 :
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
		text_surface = font.render(date_str,False,FOREGROUND_COLOR)
		line_end_Y = surface_height - font_height - 2
		line_color = color or FOREGROUND_COLOR	#デフォルトは黒

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
		elif price_type == "T" :
			return 5
		elif price_type == "A" :
			#Amount of Money
			return 6
		else :
			raise Exception("引数が価格の種類を表していません")

	def inherit(self,term_num):
		"""
		このオブジェクトの「銘柄コード」、「銘柄名」、「Tab」を継承(共有)する新たなStock_Chartオブジェクトを返す。
		"""
		brother = Stock_Chart(self.security_code,term_num,self.download_mode,self.download_site)	#兄弟に当たる新しいオブジェクト
		brother.security_name = self.security_name
		tab = self.get_tab()
		if tab :
			brother.set_tab(tab)
		return brother

	def set_highlight_index(self,index):
		"""
		ハイライト表示する要素のindex値の定義を行うインターフェイス。
		"""
		self._highlight_index = index

	def get_highlight_index(self):
		"""
		定義されたハイライト表示する要素のindex値を取得するインターフェイス。
		ハイライトするindexが未定義の時、デフォルトで最も最近のチャート足を表現するindex値を定義する。
		"""
		if not self._highlight_index :
			self.set_highlight_index_default()
		return self._highlight_index

	def set_highlight_index_default(self):
		"""
		ハイライト表示するチャート足を表すindex値をデフォルト値として定義する。
		また、ハイライトされた足についての株価情報を表示するラベルと情報を同期するためにprint_highlight_price_information()を呼ぶ。
		なお、デフォルトのindex値は、直近のチャート足である。
		"""
		endindex = self.get_drawing_index()[1]
		self.set_highlight_index(endindex)
		self.print_highlight_price_information()

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

	def print_highlight_price_information(self):
		"""
		ジェネラルラベルに株価情報を表示します
		表示するデータは、indexで指示されるself.stock_price_list[index]の株価データです。
		"""
		#ラベルに詳細情報を表示するためのいくつかの値の取得
		parent = self.get_parent_box()
		highlight_index = self.get_highlight_index()
		price_list = self.stock_price_list[highlight_index]
		#日付と価格情報の取得
		date = price_list[0]
		opning , closing = self.get_opning_closing_price(price_list)
		high , low , NoUse = self.get_price_range(price_list)
		turnover = get_human_readable( price_list[self.pricetype2index("T")] )
		kinngaku = get_human_readable( price_list[6] )
		#描画
		general_label_box = parent.get_label_box("General")
		general_labels = general_label_box.label_list
		general_labels[0].set_string("%s %s %s" % (self.security_code,self.security_name,date))
		general_labels[1].set_string("高: %d  安: %d  始: %d  終: %d  出来高: %s  売買高: %s" % (high,low,opning,closing,turnover,kinngaku))
		general_label_box.draw()

	def zoom_up(self,step=1):
		"""
		チャートにおける個々の足の大きさを定義するズームスケールを拡大させる
		どれだけ拡大させるかはself.zoom_scale_stepと、この引数に与えられたstep量によって決まる。
		"""
		new_scale = self.get_zoom_scale() + ( step * self.zoom_scale_step )
		if new_scale > 3 :
			return False
		self.set_zoom_scale(new_scale)

	def zoom_down(self,step=1):
		"""
		チャートにおける個々の足の大きさを定義するズームスケールを縮小させる
		どれだけ縮小させるかはself.zoom_scale_stepと、この引数に与えられたstep量によって決まる。
		"""
		new_scale = self.get_zoom_scale() - ( step * self.zoom_scale_step )
		if new_scale <= 0 :
			return False
		self.set_zoom_scale(new_scale)

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
			self.zoom_up()
		elif event.key == pygame.K_DOWN :
			self.zoom_down()
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
	
	1,このクラスのオブジェクトが生成されると、内部でTkのルートオブジェクトを生成し、このオブジェクトのrootメンバ変数に格納します。
	2,外からこのオブジェクトのsettingメソッドが呼ばれると、適当なGUI要素を格納した、Tkのwindowが生成され、これがこのプログラムのメインループを占有します。
	3,ユーザーによる入力が完了すると、呼び出されたsettingメソッドに対応するdoneメソッドが呼び出され、実際に株価データのフェッチ、コンバート、保持を行うStock_Chartオブジェクトを生成したり、あるいは既存のそれに対するいくつかの設定を行います。
	4,特に、チャートオブジェクトの初期化設定のプロセスにおいては、これらのデータに関する処理が正常に終了したら、このStock_Chartオブジェクトに表示領域を提供するBOXオブジェクトを生成し、また、そのBOXオブジェクトをこのコンストラクタの呼び出し元であるBOX(or Root)オブジェクトに関連付けます。
	これによってユーザーの情報の入力から、実際の表示領域の確保までの実際の橋渡しが終了します。
	5,最後にTkのメインループをBreakし、この設定画面の呼び出し元に制御を返します。

	#階層#
	1,__init__ : TkのRootウィンドウの生成と保持
		->2,settingメソッド : 定義されたＧＵＩ要素を格納したTk-windowのメインループを呼び出す。制御はpygameからこちらに完全にうつる。
			->3,doneメソッド : 再初期化処理。ユーザーからの入力を解釈して実際の設定文を実行する。設定プロセスが正常に完了したら、tkのメインループを止め、rootをdestroyする。また、入力にエラーがあれば、それをユーザーに知らせ、制御を元のtkメインループに戻す。
	"""
	def __init__(self,parent):
		"""
		1,Tkルートオブジェクトを生成し、self.rootに格納する。
		2,実際にこれに制御を渡すのはーすなわち、self.root.mainloop()を呼ぶのは、そのGUI要素の格納と、それについてのデータの設定を行う個々のsetting()メソッドにおいてである。
		3,最後(ユーザーからの入力終了時)にそのsetting()メソッドに関連付けられたdone()メソッドがよばれ、ここで実際の設定プロセスおよびエラー処理と、rootのdestroy()すなわち、制御の返し処理が行われる。
		"""
		if not isinstance(parent,(BASE_BOX,Root_Container,Stock_Chart)) :
			raise TypeError("引数がBOXオブジェクトあるいはRoot_Containerオブジェクトでありません")
		self.parent = parent	#呼び出し元オブジェクト
		#Tkの呼び出し
		self.root = Tk.Tk()	#Tkのルートウィンドウ
		self.root.title("設定画面")

	def additional_chart_setting(self):
		"""
		チャートについてのオプショナルな要素についての追加設定用画面
		"""
		if not isinstance(self.parent,Stock_Chart) :
			raise TypeError("Stock_Chartオブジェクト以外からの呼び出しです。")
		pass

	def done_additional_setting(self,Nouse):
		"""
		追加設定終了時の完了メソッド
		"""
		self.root.destroy()	#Tkルートウィンドウを破棄

	def initial_chart_setting(self):
		"""
		チャート設定についての初期化設定画面。
		銘柄コード、ダウンロードモード、ダウンロードサイトについての設定を行う。
		"""
		#ROOTかBOXオブジェクトから呼ばれるべき
		if not isinstance(self.parent,(BASE_BOX,Root_Container)) :
			raise TypeError("引数がBOXオブジェクトあるいはRoot_Containerオブジェクトでありません")

		#TkVariables
		self.security_code_Tkvar = Tk.StringVar()
		self.term_for_a_bar_Tkvar = Tk.IntVar()
		self.download_mode_Tkvar = Tk.IntVar()
		self.download_site_Tkvar = Tk.IntVar()
		#デフォルト値の設定
		self.term_for_a_bar_Tkvar.set(TERM_DICT["日足"])
		self.download_mode_Tkvar.set(DOWNLOAD_MODE_AUTO)
		self.download_site_Tkvar.set(DOWNLOAD_SITE_KDB)
		#TkWidgets
		#Entry:証券コード入力欄
		security_code_entry = Tk.Entry(self.root,textvariable=self.security_code_Tkvar)	
		security_code_entry.pack()
		security_code_entry.focus()
		security_code_entry.bind("<Return>",self.done_initial_setting)
		#Radiobutton:データダウンロードについてのモード選択
		download_mode_radiobutton_labelframe = Tk.LabelFrame(self.root,text="ダウンロードモードの設定")
		download_mode_radiobutton_labelframe.pack()
		Tk.Radiobutton(download_mode_radiobutton_labelframe,text="ローカルモード",variable=self.download_mode_Tkvar,value=DOWNLOAD_MODE_LOCAL).pack(side="left")
		Tk.Radiobutton(download_mode_radiobutton_labelframe,text="オートモード",variable=self.download_mode_Tkvar,value=DOWNLOAD_MODE_AUTO).pack(side="left")
		Tk.Radiobutton(download_mode_radiobutton_labelframe,text="差分モード",variable=self.download_mode_Tkvar,value=DOWNLOAD_MODE_DIFF).pack(side="left")
		Tk.Radiobutton(download_mode_radiobutton_labelframe,text="通常ダウンロード",variable=self.download_mode_Tkvar,value=DOWNLOAD_MODE_DOWNLOAD).pack(side="left")
		#Radiobutton:データダウンロードについてのサイト選択
		download_site_radiobutton_labelframe = Tk.LabelFrame(self.root,text="データの参照先")
		download_site_radiobutton_labelframe.pack()
		Tk.Radiobutton(download_site_radiobutton_labelframe,text="k-db.com",variable=self.download_site_Tkvar,value=DOWNLOAD_SITE_KDB).pack(side="left")
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
			#stock_chartオブジェクトの生成と初期設定
			stock_chart_object = Stock_Chart(security_code,term_num,download_mode,site=download_site) #CSVをフェッチし、データを保持するオブジェクト
			#株価CSVデータのフェッチと保存が成功したらTkrootウィンドウを破棄し、
			if stock_chart_object.initialize_data() :
				box = Container_Box(self.parent,stock_chart_object)	#stock_chartオブジェクトを格納したBOXオブジェクト
				self.parent.add_box(box)	#呼び出し元のBOXに追加
				#buttonを押す
				buttons_for_term = self.parent.get_button_box("buttons_for_term")	#term用のbutton_boxをサーチ
				term_button = buttons_for_term.get_button(term_num)	#選択termのボタンをサーチ
				term_button.set_state(True)
				buttons_for_term.draw()

				self.root.destroy()	#Tkルートウィンドウを破棄
			else :
				print "データのダウンロードに失敗しました"
		else :
			tkMessageBox.showerror(message="証券コード：正しい数字4桁を入力してください。")


#General Functions-----
#Initializations : Create and Set Default UI Objects
def add_default_buttons(root):
	"""
	"""
	#足期間のショートカットボタン
	button_box = Button_Box(root,"buttons_for_term",bgcolor=(255,200,200))
	button_box.add_button(Label_of_ButtonBox("足期間"))
	for term in TERM_LIST :
		button = UI_Button(term,TERM_DICT[term],pressed_term_button)
		button_box.add_button(button)
	root.add_box(button_box)

	#チャートについての詳細設定
	button_box = Button_Box(root,"buttons_for_chart_setting",bgcolor=(200,255,200))
	button_box.add_button(Label_of_ButtonBox("チャート設定"))
	button_informations = []	#(id_str,bind_function,swiching,synchro_func)の情報を格納する一時変数
	button_informations.append( ("Y-Prefix",pressed_Y_axis_fix_button,True,synchronize_Y_axis_fix) )
	button_informations.append( ("RulerDefault",pressed_set_ruler_default,False,None) )
	button_informations.append( ("RulerMiddle",pressed_set_middle_ruler_center,False,None) )
	button_informations.append( ("AA-line",pressed_AA_button,True,synchronize_AA) )
	#登録
	for id_str , bind_function , swiching , synchro_func in button_informations :
		if swiching :
			button = UI_Button(id_str,id_str,bind_function)
			if synchro_func :
				button.set_synchro_function(synchro_func)
		else:
			button = No_Swith_Button(" "+id_str+" ",id_str,bind_function)
		button_box.add_button(button)
	#移動平均線についてのショートカット
	for MA_day in DEFAULT_MA_DAYS_ALL :
		id_str = "MA-%d" % (MA_day)
		label_str = "MA-%d" % (MA_day)
		button = UI_Button(label_str,id_str,pressed_MA_setting_shortcut)
		button.set_synchro_function(synchronize_MA)
		button_box.add_button(button)

	root.add_box(button_box)

def add_default_labels(root):
	"""
	"""
	label_box = Label_box(root)
	label1 = Label(str_color=(255,0,0))
	label2 = Label("Hello StockChart",str_color=(0,0,255))
	label_box.add_label(label1)
	label_box.add_label(label2)
	root.add_box(label_box)

#Binded Functions associated with UI_BUTTON objects
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
		if not new_stock_chart.initialize_data() :
			tkMessageBox.showerror(message="データの初期化に失敗しました")
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
	focused_box.get_content().set_horizontal_rulers_prices_default()
	focused_box.draw()
	return True

def pressed_set_middle_ruler_center(button):
	"""
	フォーカスチャートの水平ルーラーのうち、中間のルーラーとして定義されたオブジェクトの価格状態を、
	高値として定義されたそれと安値のそれとして定義されたそれの中間値に再設定する。
	"""
	root = button.get_parent_box().get_father()
	focused_box = root.get_focused_box()
	focused_box.get_content().set_middle_horizontal_rulers_price_center()
	focused_box.draw()
	return True

def pressed_MA_setting_shortcut(button):
	"""
	移動平均線設定のためのショートカット
	"""
	root = button.get_parent_box().get_father()
	focused_box = root.get_focused_box()
	focused_content = focused_box.get_content()

	MA_days = int( button.id[button.id.find("-")+1:] )
	for MA in focused_content.moving_averages :
		if MA.days == MA_days :
			MA.set_visible(not button.state)

	focused_box.draw()
	return True

def pressed_AA_button(button):
	"""
	実質的価値を表現するグラフのvisibilityの設定
	"""
	root = button.get_parent_box().get_father()
	focused_box = root.get_focused_box()
	focused_content = focused_box.get_content()

	focused_content.get_AA_analyser().set_visible(not button.state)
	focused_box.draw()
	return True

#Synchronizing Functions : those will be call'd when focused-object is changed
def synchronize_Y_axis_fix(button):
	"""
	フォーカスが移動したときに呼ばれるボタン状態シンクロ関数。Y軸固定オプションボタンについて定義。
	"""
	root = button.get_parent_box().get_father()
	focused_content = root.get_focused_box().get_content()
	if isinstance(focused_content,Stock_Chart) :
		state = focused_content.get_Y_axis_fixed()
		button.set_state(state)
	else :
		print "フォーカスの写ったオブジェクトがチャートオブジェクトでありません。"

def synchronize_MA(button):
	"""
	フォーカスが移動したときに呼ばれるボタン状態シンクロ関数。移動平均設定ショートカットボタンについて定義。
	"""
	root = button.get_parent_box().get_father()
	focused_content = root.get_focused_box().get_content()
	if isinstance(focused_content,Stock_Chart) :
		for MA in focused_content.get_moving_averages() :
			if button.id == "MA-%d" % (MA.get_MA_days()) :
				button.set_state(MA.is_visible())
				break
	else :
		print "フォーカスの写ったオブジェクトがチャートオブジェクトでありません。"

def synchronize_AA(button):
	"""
	フォーカスが移動したときに呼ばれるボタン状態シンクロ関数。AA-lineボタンについて定義。
	"""
	root = button.get_parent_box().get_father()
	focused_content = root.get_focused_box().get_content()
	if isinstance(focused_content,Stock_Chart) :
		visibility = focused_content.get_AA_analyser().is_visible()
		button.set_state(visibility)
	else :
		print "フォーカスの写ったオブジェクトがチャートオブジェクトでありません。"
	
#Ulils
def get_human_readable(num):
	"""
	int値をとり、それをヒューマンリーダブルなunicode文字列に変換したものを返す。
	"""
	no_human_readable = str(num)
	human_readable = ""
	digit = math.log10(num)
	#億以上なら
	if digit >= 8 :
		human_readable = no_human_readable[0:-8]
		human_readable += "億"
		#10億以上ならそのまま返す
		if digit >= 9 :
			return human_readable
	#万以上なら
	if digit >= 4 :
		start = -7 if digit >= 8 else 0
		human_readable += no_human_readable[start:-4]
		human_readable += "万"
		return human_readable
	else :
		return no_human_readable


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

