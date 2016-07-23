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
	# Settings
	def __init__(self,implement_type):
		"""
		"""
		implement_type.__init__(self)
		self.set_valid_container_type(implement_type)
		self.containeds = []

	def __repr__(self):
		""" ヒューマンリーダブルなテストケース情報を提供 """
		return "%s ( valid_type is %s )" % (self.__class__.__name__,self.get_valid_container_type().__name__)


	# Utils
	def is_validtype(self,implement_type):
		""" シンタックスシュガー """
		return self.get_valid_container_type() is implement_type

	def get_valid_add_method(self):
		""" 有効型のaddメソッド取得ユーティリティ """
		# シングルコンテナ
		if self.is_validtype(Single_Container) :
			valid_add_method = self.set_child
		# Pluralコンテナ
		elif self.is_validtype(Plural_Container) :
			valid_add_method = self.add_child
		# コンテナコンテナ
		elif self.is_validtype(Container_Of_Container) :
			valid_add_method = self.add_container

		return valid_add_method


	#Test Methods
	def test_add(self):
		""" addメソッドのテスト """
		#10回テスト
		for i in range(10) :
			valid_add_method = self.get_valid_add_method()
			# add呼び出し
			containeds = (Single_Container(),Plural_Container(),Container_Of_Container())
			for contained in containeds :
				valid_add_method(contained)
				self.containeds.append(contained)

	@afterOf("test_add")
	def test_add_fail(self):
		"""addの失敗テスト"""
		#不正な型オブジェクトの代入
		for invalid_obj in RANDOM_BUILTIN_OBJECTS :
			self.assertRaises(TypeError,self.get_valid_add_method(),invalid_obj)

		contained = Contained()
		#コンテナコンテイナーに非コンテナオブジェクトの代入
		if self.is_validtype(Container_Of_Container) :
			self.assertRaises(TypeError,self.add_container,(self,contained))

		# 不正なaddメソッド名の使用
		if self.is_validtype(Single_Container) :
			self.assertRaises(TypeError,self.add_child,contained)
			self.assertRaises(TypeError,self.add_container,contained)
		elif self.is_validtype(Plural_Container) :
			self.assertRaises(TypeError,self.set_child,contained)
			self.assertRaises(TypeError,self.add_container,contained)
		elif self.is_validtype(Container_Of_Container) :
			self.assertRaises(TypeError,self.set_child,contained)
			self.assertRaises(TypeError,self.add_child,contained)

	@afterOf("test_add")
	@afterOf("test_remove")
	def test_add_polymorphism(self):
		""" addの多様性テスト """
		if self.is_validtype(Container_Of_Container) :
			contained = Single_Container()
		else :
			contained = Contained()
		self.add(contained)

	@afterOf("test_add")
	def test_remove(self):
		"""removeメソッドのテスト"""
		# すべての要素を取り除く
		# シングルコンテナなら
		if self.is_validtype(Single_Container) :
			self.remove(self.get_children())
		else :
			for child in list(self.get_children()) :
				self.remove(child)
		# 要素が0か確認
		self.assertFalse(self.get_children())

	@afterOf("test_add")
	@beforeOf("test_remove")
	def test_iterable(self):
		""" イテレートテスト """
		# シングルコンテナならイテレート不能
		if self.is_validtype(Single_Container) :
			with self.assertRaises(TypeError) :
				for Nouse in self :
					pass
		else :
			for contained in self :
				pass

	@afterOf("test_remove")
	def test_type_refusion(self):
		""" 被コンテナオブジェクトの有効型の定義とそれに伴う挙動のテスト """
		valid_add_method = self.get_valid_add_method()

		# Container_Of_Containerなら、validtypeの操作は例外を吐く
		if self.is_validtype(Container_Of_Container) :
			test_types = (Single_Container,Plural_Container,Container_Of_Container)
			for typeObj in test_types :
				self.assertRaises(Exception,self.add_valid_type,typeObj)

		# テスト
		else :
			test_types = DummyCls1 ,DummyCls2 ,DummyCls3 = generate_dummyclass("DummyCls1","DummyCls2","DummyCls3",base=Contained)
			for validtype in test_types :
				# ValidTypeの定義
				self.add_valid_type(validtype)
				self.assertTrue( validtype in self.get_valid_types() )	#設定されたかテスト
				# 適用されているかaddでテスト
				for testtype in test_types :
					# ValidTypeなら成功
					if testtype is validtype :
						valid_add_method(validtype())
					# さもなくばTypeError
					else :
						self.assertRaises(TypeError,valid_add_method,testtype()) # コンテナ実装型はbaseContainerのサブクラスゆえ否例外
				# valid_typeの初期化
				self.set_type_invalid(validtype)

			# 複数の有効型のテスト
			for valid_type in test_types :
				self.add_valid_type(valid_type)
				self.assertTrue( valid_type in self.get_valid_types() )	#設定されたかテスト
				for test_type in test_types :
					if test_type in self.get_valid_types() :
						valid_add_method(valid_type())
					else :
						self.assertRaises(TypeError,valid_add_method,test_type())
			# 最後にリセットのテスト
			self.reset_validtypes()
			self.assertFalse(self.get_valid_types())


	@last
	def test_switch_valid_containertype(self):
		pass



# Utils
def testcase_generator():
	for implement_type in IMPLEMENT_CONTAINER_TYPE :
		testcase = ContainersTestCase(implement_type)
		yield testcase,implement_type


# Main
def main():
	""" テストを実行する """
	with Test_Profiler(ContainersTestCase) as test_profiler :
		for testcase,implement_type in testcase_generator() :
			test_profiler.run_test(testcase,(implement_type,Base_Container))
	


if __name__ == '__main__':
	main()



