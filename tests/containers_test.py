#! /usr/bin/python
#-*- coding: utf-8 -*-

import stockchart 

"""
"""


class Tester(object):
	"""
	単体テストクラス
	クラス単一の単位でテストを行う。
	"""
	#Test Classes
	class Container_Inherited_Plural(Plural_Container):
		"""複数格納コンテナを継承するコンテナ実装"""
		def __init__(self):
			Plural_Container.__init__(self)


	class Double_Inherited_Container(Single_Container,Container_Of_Container):
		"""単一オブジェクト格納コンテナおよびコンテナコンテインナーを継承するコンテナ実装"""
		def __init__(self):
			Single_Container.__init__(self)
			Container_Of_Container.__init__(self)

	#Methods
	def __init__(self):
		"""
		実装型のインスタンスの生成。
		"""
		#コンテナオブジェクト
		self.Plural = self.Container_Inherited_Plural()
		self.Double = self.Double_Inherited_Container()
		#Containedオブジェクト
		self.contained_list = []

	def append_contained_list(self,val):
		"""ユーティリティ"""
		self.contained_list.append(val)
		return val

	def test_plural_container(self):
		"""コンテナ実装のテスト"""
		print "pluralコンテナのテストを開始します..."
		for x in range(3) :
			ins = self.append_contained_list(Contained())
			self.Plural.add_child(ins)

		print "\t子オブジェクト"
		for child in self.Plural :
			print "\t",child

		print "Done\n"

	def test_double_container(self):
		"""多様性を有するコンテナ実装のテスト"""
		print "Doubleコンテナのテストを開始します..."

		#Container_Of_Container有効
		print "Container_Of_コンテナを有効にしたテスト"
		self.Double.set_valid_container_type(Container_Of_Container)
		ins = self.append_contained_list(Plural_Container())
		self.Double.add_container(ins)
		print "\t子オブジェクト"
		print "\t",self.Double.get_children()

		#Single Container 有効
		print "Singleコンテナを有効にしたテスト"
		self.Double.set_valid_container_type(Single_Container)
		ins = self.append_contained_list(Contained())
		self.Double.set_child(ins)
		print "\t子オブジェクト"
		print "\t",self.Double.get_children()

		#Container_Of_Container 再有効
		print "Container_Of_コンテナを再び有効にしたテスト"
		self.Double.set_valid_container_type(Container_Of_Container)
		for x in range(3):
			ins = self.append_contained_list(Single_Container())
			self.Double.add_container(ins)

		self.Double.add_container(self.append_contained_list(self.Plural))

		print "\t子オブジェクト"
		for child in self.Double :
			print "\t",child
		print "Done\n"

	def test_contained(self):
		"""Containedのテスト"""
		print "Contaiendのテストを開始します..."""
		for ins in self.contained_list :
			print "\t",ins," 親:",ins.get_container()

		print "Done\n"

	def test_all(self):
		"""Run all tests"""
		print "テストを開始します"
		self.test_plural_container()
		self.test_double_container()
		self.test_contained()
		print "全体のテストが終了しました"


if __name__ == '__main__' :
	print "containersのテストを開始します"
	tester = Tester()
	tester.test_all()
	print "containersのテストが終了しました"

