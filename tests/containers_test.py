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
		self.container_contained_table = {}

	def test_add(self):
		for error_obj in RANDOM_BUILTIN_OBJECTS :
			self.assertRaises(NameError,self.add_method,(self,error_obj))
		for i in range(10):
			contained = Contained()
			if self.get_valid_container_type() is Container_Of_Container :
				self.assertRaises(TypeError,self.add_method,(self,contained))
			else :
				self.add_method(self,contained)
			self.container_contained_table[self.get_valid_container_type] = contained 

def testcase_generator():
	for implement_type in IMPLEMENT_CONTAINER_TYPE :
		testcase = ContainersTestCase(implement_type)
		yield testcase


if __name__ == '__main__':
	test_monitor = Test_Monitor(ContainersTestCase,Base_Container)
	for testcase in testcase_generator() :
		test_monitor.test(testcase)



