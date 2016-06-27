#! /usr/bin/python
# -*- coding: utf-8 -*-

import pygame
import pygamebox

"""
pygameのラベルコンテンツ実装モジュール。
"""

# PygameBox For Labelcontent
class LabelBox(pygamebox.SubBox):
	"""
	文字情報の描画を行うLabelオブジェクトにその描画領域を提供するオブジェクト
	また、その実際の描画命令も、このオブジェクトのdraw()メソッドから間接的に呼ばれることになる。
	このオブジェクトに必要な高さ(確保しなくてはならない描画領域)は、このオブジェクトの有する子ラベルオブジェクトにより一意に決まる
	"""
	def __init__(self,root,boxid=None):
		pygamebox.SubBox.__init__(self,root,Plural_Container,boxid)
		self.init_attr()

	def init_attr(self):
		"""属性値の初期化"""
		self.set_size_prefix()
		self.bgcolor = (255,255,255)

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
		surface = self.get_surface(bgcolor=self.bgcolor)
		for label in self :
			label.draw(surface,left_top)
			left_top = (left_top[0],left_top[1]+label.height)
		self.update(surface)

# Pygame Label Content
class Label(pygamebox.PygameBox_Content):
	"""
	文字列の描画を行うオブジェクトです。
	1,描画される文字列self.stringの設定を行う。
	2,描画に必要な範囲をフォントサイズから算出し、self.heightに格納
	3,描画
	"""
	def __init__(self,string="",fgcolor=None,font=None) :
		pygamebox.PygameBox_Content.__init__(self)
		self.font = font or pygame.font.Font(FONT_NAME,14)	#文字の描画に用いられるフォント
		self.fgcolor = fgcolor or (0,0,0)
		self.MARGINE = 1
		self.init_attr()
		self.set_own_height()	#self.heightの動的な算出

	def set_own_height(self) :
		"""
		フォントサイズからその描画に必要な高さを動的に算出し、self.heightに格納する。
		"""
		self.height = self.font.size(self.string)[1] + self.MARGINE * 2

	def set_string(self,string) :
		assert(string,str)
		self.string = string
		self.set_own_height()	#描画領域の再計算

	def draw(self,surface,left_top):
		"""
		与えられたサーフェスに、透明な文字列を描画する。
		背景色については親BOXのLabel_BOXオブジェクトの属性値に拠る
		"""
		decoded = unicode(self.string,"utf-8")	#日本語の貼り付けにはデコードが必要。
		text_surface = self.font.render(decoded,True,self.str_color)
		left_top = (20+left_top[0],self.MARGINE+left_top[1])
		surface.blit(text_surface,left_top)



