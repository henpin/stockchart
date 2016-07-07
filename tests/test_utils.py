#! /usr/bin/python
#-*- coding: utf-8 -*-

import unittest
import sys

"""
テストに関する統一的な枠組みを提供するモジュール
"""

class TestFailed(Exception):
	"""
	テストケースの独自エラー型。
	"""
	pass


class TestCase(object):
	"""
	単純なテストケースメソッド。
	"""
	# Class Global
	Failure = TestFailed

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
			message = (
				"TestFailed : 定義された例外 %s 以外の例外オブジェクトが送出されました。\n" % (excClass.__name__)\
				+"\t%s : %s" % (e.__class__.__name__,e))
				
			raise self.Failure(message)
		else :
			raise self.Failure("定義された例外が送出されませんでした。")

			
class Test_Profiler(object):
	"""
	テストのプロファイリングを行うメソッド。
	"""
	# Initialization
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
		#テストケースをまたいだ全テストに関する情報
		self.comprehenive_processed = 0
		self.comprehenive_failed = 0

		#初期化レポート
		self.print_initial_report()


	# Reportion
	def print_initial_report(self):
		"""
		初期化レポートの表示
		"""
		half_horizontal = "-" *40
		initial_report = \
			"\n"\
			+"%s Test Profiler %s\n" % (half_horizontal,half_horizontal)\
			+"\ttestClass : %s\n" % (self.testCaseClass.__name__,)\
			+"\tExclusionClass : %s" % (self.bases and self.bases.__name__)
			
		print initial_report

	def report_result(self):
		"""
		テストの総合リザルトの表示
		"""
		result_report = \
			"-"*80 +"\n"\
			"すべてのテストケースが終了しました\n"\
			+"\tPassed %d	Failed %d\n" % (self.comprehenive_processed-self.comprehenive_failed,self.comprehenive_failed)

		print "\n"
		print result_report


	# Do Test
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

		self.errors = []
		print "\n"
		with Paragraph(Paragraph.H1,title="テストケース",end_horizontal=False) as para :
			para.write("対象オブジェクト : %s\n" % object.__repr__(ins) )

			# テストメソッドの呼び出し
			processed = 0
			for method_name in self.filtered_names :
				processed += 1
				method = self.name2method(method_name)
				method(ins)

			# 失敗したテストに関する出力
			if self.errors :
				para.write("")
				self.show_error()	#エラーが送出されていればその送出。
			# 結果の出力
			para.write("")
			para.write("テストが終了しました。\\")
			self.show_result(processed,len(self.errors))
			para.write("除外メソッド:\n\t%s" % self.except_testCaseNames)

			# テスト結果の保存
			self.comprehenive_processed += processed
			self.comprehenive_failed += len(self.errors)


	# Show Result
	def show_error(self):
		"""
		たまったエラーの出力
		"""
		with Paragraph(Paragraph.H2,"Errors") as para:
			for error in self.errors :
				para.write( "%s : %s" % (error.func_name,error.exc_type) )
				para.write( "\t-> %s\n" % (error) )

	def show_result(self,numof_processed,numof_errors):
		"""
		テスト結果の出力
		"""
		print "Passed: %d  Error: %d" % (numof_processed-numof_errors, numof_errors)


	# extraction of test-methods 
	def name2method(self,name):
		"""
		定義された名前で定義されたテストメソッドを、
		"""
		#ラッパ関数を生成する一時関数
		def create_result_monitor(method):
			func_name = method.func_name
			if not callable(method):
				raise TypeError("コーラブルでアリません")

			def result_report_wrapper(arg):
				"""テストメソッドの実行結果を監視するラッパ"""
				try :
					method(arg)	#クロージャー
				except Exception as e :
					print "%s : Test Failed" % func_name
					e.func_name = func_name
					e.exc_type = e.__class__.__name__
					self.errors.append(e)
				else :
					print "%s : Passed" % func_name

			return result_report_wrapper

		#メソッドの取得
		method = getattr(self.testCaseClass,name)
		return create_result_monitor(method)

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
	H1 = 80
	H2 = 55
	H3 = 40
	def __init__(self,width,title=None,start_horizontal=True,end_horizontal=True):
		if not 0 <= width <= 100 :
			raise Exception("段落幅が大きすぎます")

		#水平線に関する情報
		self.width = width
		self.title = title
		self.start_horizontal = start_horizontal
		self.end_horizontal = end_horizontal
		#段落内の行情報
		self.lines = []

	def __enter__(self):
		"""
		コンテキストマネージャープロトコル。
		1,標準出力先を自分自身にする。
		2,初期化時の定義に従って水平線を描画
		3,自身を返す
		"""
		#標準出力先の変更
		self.old_stdout = sys.stdout
		sys.stdout = self

		#水平線の描画
		if self.start_horizontal :
			self.write_horizontal(titled=True)
		return self

	def __exit__(self, *exc_info):
		"""
		コンテキストマネージャープロトコル。
		1,標準出力先を自分自身からもとのそれにもどす
		2,標準出力として貯められた出力文字列を整形して出力
		3,初期化時の定義に従って水平線を描画
		"""
		# 標準出力先を元に戻す
		sys.stdout = self.old_stdout

		#水平線の描画
		if self.end_horizontal :
			self.write_horizontal(titled=False)

		#すべての行の出力
		self.print_all()

	def get_horizontalstr(self,title=None):
		"""
		水平線を表す文字列を返す
		"""
		width = self.width
		if title is not None :
			assert isinstance(title,str)
			#タイトルが定義されているのなら開始水平線の設定
			numof_bar = width - ( len(title.decode("utf-8")) + 2 )
			half_bar = "-" * (numof_bar/2)
			return " ".join( (half_bar,title,half_bar) )
		else :
			return "-" * width

	def write(self,string,newline=True,force=False):
		"""
		文字列stringを段落に登録する
		"""
		if string == '\n' and not force :
			return 

		if newline :
			self.lines.append(string)
		else :
			lastline = self.lines.pop()
			joined = '\t'.join((lastline,string))
			self.lines.append(joined)

	def write_horizontal(self,titled):
		"""
		水平線をこの段落に登録
		"""
		if titled :
			title = self.title
		else :
			title = None

		self.write(self.get_horizontalstr(title))

	def print_all(self):
		"""
		このコンテキスト内で貯めこまれた行情報をすべて出力する。
		"""
		for index,line in enumerate(self.lines) :
			#終文字がバックコートなら改行抑制
			if line and line[-1] == '\\' :
				print line.strip('\\'),
			else :
				print line
		

if '__name__' == '__main__' :
	print "このモジュールの自己テストを行います"
#	main()


