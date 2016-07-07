#! /usr/bin/python
#-*- coding: utf-8 -*-

import unittest

"""
"""
class TestFailure(Exception):
	"""
	テストケースの独自エラー型。
	"""
	pass


class TestCase(object):
	"""
	単純なテストケースメソッド。
	"""
	Failure = TestFailure
	def __init__(self):
		pass
	
	def assertTrue(self, expr):
		"""
		式が真かどうか。
		"""
		if not exp :
			raise self.Failure("%s is not True") % expr

	def assertFalse(self, expr):
		"""
		式が偽かどうか
		"""
		if exp :
			raise self.Failure("%s is not False") % expr

	def assertRaises(self, excClass, callableObj, *args, **kwargs):
		"""
		呼び出し可能callableObjを与えられたコンテキストで呼び出し、
		定義された例外execClassを補足する。
		もし定義された例外以外が送出されたのなら、例外のラッパを再送出する。
		"""
		# 引数チェック
		if not issubclass(excClass,BaseException):
			raise TypeError("定義された引数が例外クラスでありません。")
		elif not callable(callableObj) :
			raise TypeError("定義された引数が呼び出し可能でありません")

		# 定義されたコンテキストでcallableの呼び出し
		try :
			callableObj(*args,**kwargs)
		# 既定された例外を送出したらテストパス
		except excClass :
			pass	#定義された例外以外ならキャッチされず上位へ送出される
		# 定義された以外の例外ならエラーメッセージのラップ
		except Exception as e :
			message = "".join(( 
				"定義された例外 %s 以外の例外オブジェクトが送出されました。\n" % excClass,
				"\t%s : %s" % (e.__class__,e)
				))
			raise self.Failure(message)
		else :
			raise self.Failure("定義された例外が送出されませんでした。")

			
class Test_Monitor(object):
	"""
	"""
	def __init__(self,testCaseClass,bases=None):
		if bases is not None :
			if not issubclass(testCaseClass,bases) :
				raise TypeError("除外テストメソッド指定のためのクラス定義は、そのテストクラスの基底でなければなりません")
		#対象テストクラス
		self.testCaseClass = testCaseClass
		self.bases = bases
		#エラー保管リスト
		self.errors = []
		#テスト対象/除外:メソッド名
		self.filtered_names , self.except_testCaseNames =\
			self.extractTestMethodNames(testCaseClass,bases)
		
	def test(self,ins=None):
		"""
		実際のテストを呼び出すメソッド。
		オプションでそのテストメソッドの呼び出しを行うコンテキストとしてのTestCaseオブジェクトを定義できる
		"""
		# Check args
		if ins is None :
			ins = self.testCaseClass()	#引数なしで初期化
		elif not isinstance(ins,self.testCaseClass) :
			raise TypeError("引数insは定義されたテストクラスのインスタンスでなければなりません")

		with Paragraph(Paragraph.H1,"テストケース") :
			print "対象オブジェクト : %s\n" % object.__repr__(ins)
			processed = 0
			for method_name in self.filtered_names :
				processed += 1
				method = self.name2method(method_name)
				method(ins)
			if self.errors :
				print ""
				self.show_error()	#エラーが送出されていればその送出。
			print "テストが終了しました。"
			self.show_result(processed,len(self.errors))
			print ""
			print "除外メソッド:\t%s" % self.except_testCaseNames

	def show_error(self):
		"""
		たまったエラーの出力
		"""
		with Paragraph(Paragraph.H2,"Errors"):
			for methodname,error in self.errors :
				print "%s :%s" % (methodname,error.__class__)
				print "    -> %s" % (error)

	def show_result(self,numof_processed,numof_errors):
		"""
		テスト結果の出力
		"""
		print "Passed: %d  Error: %d" % (numof_processed-numof_errors, numof_errors)

	def name2method(self,name):
		#ラッパ関数
		def result_monitor(method):
			func_name = method.func_name
			if not callable(method):
				raise TypeError("コーラブルでアリません")
			def wrapper(arg):
				try :
					method(arg)
				except Exception as e :
					print "%s : Error" % func_name
					self.errors.append((func_name,e))
				else :
					print "%s : Passed" % func_name

			return wrapper
		#メソッドの取得
		method = getattr(self.testCaseClass,name)
		return result_monitor(method)


	def extractTestMethodNames(self,testCaseClass,bases=None):
		"""
		テスト対象となるメソッドの抽出機
		"""
		testLoader = unittest.TestLoader()
        	testCaseNames = testLoader.getTestCaseNames(testCaseClass)
        	except_testCaseNames = testLoader.getTestCaseNames(bases) if bases is not None else []

		inExceptNames = ( lambda methodname : methodname not in except_testCaseNames )
        	filtered_names = filter(inExceptNames,testCaseNames)
        	return filtered_names,except_testCaseNames


class Paragraph(object):
	"""
	段落を表現する出力フォーマット用オブジェクト。
	with文において用いる。
	"""
	H1 = 40
	H2 = 25
	H3 = 20
	def __init__(self,width,title=None):
		if not 0 <= width <= 40 :
			raise Exception("段落幅が大きすぎます")

		#水平線の設定
		self.horizontal = "-" * width
		if title is not None :
			assert isinstance(title,str)
			#タイトルが定義されているのなら開始水平線の設定
			numof_bar = width - ( len(title.decode("utf-8")) + 2 )
			half_bar = "-" * (numof_bar/2)
			self.start_horizontal = "%s %s %s" % (half_bar,title,half_bar)
		else :
			self.start_horizontal = self.horizontal

	def __enter__(self):
		print self.start_horizontal
	
	def __exit__(self, *exc_info):
		print self.horizontal + "\n"
		
		

if '__name__' == '__main__' :
	print "このモジュールの自己テストを行います"
#	main()


