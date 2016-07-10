#! /usr/bin/python
#-*- coding: utf-8 -*-

import setup
from test_utils import *
from containers import *

"""
containersモジュールのテスト
"""
RANDOM_BUILTIN_OBJECTS = ("str",1,573,(5,6),list(),object(),{1:3,5:8})

# TestCases
class ContainersTestCase(
	TestCase,
	Single_Container,
	Plural_Container,
	Container_Of_Container
	):
	"""
	テスト用の基底クラス
	"""
	def __init__(self,implement_type):
		"""
		"""
		implement_type.__init__(self)
		self.set_valid_container_type(implement_type)
		self.add_method = implement_type._add
		self.containeds = []

	def __repr__(self):
		return "%s : valid_type is %s" % (self.__class__.__name__,self.get_valid_container_type().__name__)

	def test_add(self):
		""" addメソッドのテスト """
		#10回テスト
		for i in range(10) :
			# Container of Container
			if self.get_valid_container_type() is Container_Of_Container :
				containeds = (Single_Container(),Plural_Container(),Container_Of_Container())
				for contained in containeds :
					self.add_method(self,contained)
					self.containeds.append(contained)
			#その他コンテナオブジェクト
			else :
				contained = Contained()
				self.add_method(self,contained)
				self.containeds.append(contained)

	def test_add_fail(self):
		"""addの失敗テスト"""
		#不正な型オブジェクトの代入
		for error_obj in RANDOM_BUILTIN_OBJECTS :
			self.assertRaises(TypeError,self.add_method,(self,error_obj))
		#コンテナコンテイナーに非コンテナオブジェクトの代入
		contained = Contained()
		if self.get_valid_container_type() is Container_Of_Container :
			self.assertRaises(TypeError,self.add_method,(self,contained))

	@afterOf("test_add")
	def test_remove(self):
		"""removeメソッドのテスト"""
		if not self.get_children() :
			raise TestOrderError("このメソッドはaddテストのあとに呼ばれなければなりません")

		#すべての要素を取り除く
		for child in self :
			self.remove(child)
		self.assertFalse(self.get_children())


def testcase_generator():
	for implement_type in IMPLEMENT_CONTAINER_TYPE :
		testcase = ContainersTestCase(implement_type)
		yield testcase


if __name__ == '__main__':
	with Test_Profiler(ContainersTestCase,Base_Container) as test_profiler :
		for testcase in testcase_generator() :
			test_profiler.test(testcase)

