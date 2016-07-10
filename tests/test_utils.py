#! /usr/bin/python
#-*- coding: utf-8 -*-

import unittest
import sys

"""
テストに関する統一的な枠組みを提供するモジュール
"""

class TestFailed(Exception):
	""" テストケースの独自エラー型。"""
	pass

class TestOrderError(Exception):
	""" テスト順序の誤りを表す単純例外 """
	pass

class TestPreprocessError(Exception):
	""" テストに関するプリプロセス中に生じた問題を表現する例外 """
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
		if not expr :
			raise self.Failure("%s is not True" % expr)

	def assertFalse(self, expr):
		"""
		式が偽かどうか
		"""
		if expr :
			raise self.Failure("%s is not False" % expr)

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
		self.filtered_names , self.except_testCaseNames = self.extractTestMethodNames(testCaseClass,bases)
		#順序解決されたテスト名リスト
		self.ordered_testnames = self.generate_ordered_tests()
		#テストケースをまたいだ全テストに関する情報
		self.comprehenive_processed = 0
		self.comprehenive_failed = 0
		self.comprehenive_skipped = 0
		#実行済みテストケースに関する情報
		self.processed_testcase = 0
		self.skipped_testcase = 0


	# Context Manager protocol
	def __enter__(self):
		#初期化レポート
		self.print_initial_report()
		return self

	def __exit__(self,*excinfo):
		#再初期化レポート
		print "\n"
		print Paragraph(Paragraph.H1).get_horizontalstr()
		self.report_result()


	# Profilling Report
	def print_initial_report(self):
		"""
		初期化レポートの表示
		"""
		initial_report = \
			"\n\n\n"\
			"Test Profiler"\
			"\ntestClass : %s\n" % (self.testCaseClass.__name__,)\
			+"ExclusionClass : %s" % (self.bases and self.bases.__name__)
			
		print initial_report

	def report_result(self):
		"""
		テストの総合リザルトの表示
		"""
		result_report = \
			"すべてのテストケースが終了しました\n"\
			"TestCase: %d\tPassed: %d\tFailed: %d" % (
				self.processed_testcase -self.skipped_testcase,
				self.comprehenive_processed-self.comprehenive_failed,
				self.comprehenive_failed
				)
		print "\n"
		print result_report


	# Testing
	def test(self,ins=None,errorstop=True):
		"""
		実際のテストを呼び出すメソッド。
		オプションでそのテストメソッドの呼び出しを行うコンテキストとしてのTestCaseオブジェクトを定義できる
		"""
		# Check args
		if ins is None :
			ins = self.testCaseClass()	#引数なしで初期化
		elif not isinstance(ins,self.testCaseClass) :
			raise TypeError("引数insは定義されたテストクラスのインスタンスでなければなりません")

		# テストの実行と、結果の出力
		with Paragraph(Paragraph.H1,title="テストケース %d" % (self.processed_testcase+1),end_horizontal=False) as para :
			para.write("対象オブジェクト :\n\t%s\n\n" % ins)

			# テストメソッドの呼び出し
			processed ,skipped = 0 ,0
			for methodname in self.ordered_testnames :
				method = self.testname2method(methodname)
				method = self.testmethod2result_reporter(method)
				processed += 1
				method(ins)

			# 失敗したテストに関する出力
			if self.errors :
				self.show_error()	#エラーが送出されていればその詳細情報の表示。
			# 結果の出力
			para.write("\nテストが終了しました。\\")
			self.show_result(processed,len(self.errors),skipped)
			para.write("除外メソッド:\n\t%s" % self.except_testCaseNames)

		# エラー発生時それ以降のテストケースをパスする。
		if errorstop and self.errors:
			self.stop_profiling()
		# テスト結果の保存と更新
		self.update_processiong_info(processed,skipped)


	def update_processiong_info(self,processed,skipped):
		"""テスト処理数についての総合情報の更新"""
		self.comprehenive_processed += processed
		self.comprehenive_failed += len(self.errors)
		self.comprehenive_skipped += skipped
		self.processed_testcase += 1
		self.errors = [] # エラーリストの初期化


	# Show Result
	def show_error(self):
		"""
		たまったエラーの出力
		"""
		with Paragraph(Paragraph.H2,"Errors") as para:
			for error in self.errors :
				para.write( "%s : %s" % (error.test_name,error.exc_type) )
				para.write( "\t-> %s\n" % (error) )

	def show_result(self,numof_processed,numof_errors,numof_skipped):
		"""
		テスト結果の出力
		"""
		print "Passed: %d  Error: %d  Skipped: %d" % (numof_processed-numof_errors, numof_errors,numof_skipped)


	# Extraction and Settings of Test-Methods
	def extractTestMethodNames(self,testCaseClass,bases=None):
		"""
		テスト対象となるメソッドの抽出機
		unittest.testLoaderを用いる。
		"""
		testLoader = unittest.TestLoader()
        	testCaseNames = testLoader.getTestCaseNames(testCaseClass)
        	except_testCaseNames = testLoader.getTestCaseNames(bases) if bases is not None else []

		inExceptNames = ( lambda methodname : methodname not in except_testCaseNames )
        	filtered_names = filter(inExceptNames,testCaseNames)
        	return filtered_names,except_testCaseNames

	def testname2method(self,testname):
		"""
		テスト名を引数にとり、その名前で定義されたテストメソッドを、定義されたテストケースクラスから抽出する。
		冗長な名前チェックを行うので、単純な名前のテストメソッドとしても用い得る。
		"""
		#テスト名のチェック
		check_testname(testname)
		if not hasattr(self.testCaseClass,testname) :
			raise TestPreprocessError("テスト名 %s はこのテストプロファイラに対応定義されたテストケース %s に実装されていません。")\
				% (testname,self.testCaseClass)

		#テストメソッドの抽出とチェック
		testmethod = getattr(self.testCaseClass,testname)
		if not callable(testmethod):
			raise TestPreprocessError("テストケース %s に定義されたテスト名 %s に対する %s は呼び出し可能でありません。")\
				%(self.testCaseClass,testname,testmethod)

		return testmethod

	def testmethod2result_reporter(self,testmethod):
		"""
		テストメソッドを引数にとり、それをテスト結果報告関数としてラッピングした関数を返す
		結果報告関数は、内部でテストメソッドを実行し、テストが異常なしに成功すればそれを出力。
		何らかの例外が送出されれば、それを出力し、このオブジェクトのerrorリストに保存する。
		"""
		if not callable(testmethod):
			raise TypeError("コーラブルでアリません")

		testfunc_name = testmethod.func_name	#テストメソッド名
		#テスト結果報告関数
		def result_report_wrapper(arg):
			"""テストメソッドの実行結果を監視するラッパ"""
			try :
				testmethod(arg)	#テストを実行

			#テスト失敗時、それを出力してテストエラーリストに情報を保管する。
			except Exception as e :
				print "%s : Failed\\" % testfunc_name
				# エラーに関する情報の設定と格納 
				e.test_name = testfunc_name
				e.exc_type = e.__class__.__name__
				self.errors.append(e)	# テストエラーリストにエラー情報を格納
			else :
				#正常にテストが終了したらそれを出力して制御を返す
				print "%s : Passed\\" % testfunc_name
			finally :
				#順序に関する情報
				has_beforeOf = hasattr(testmethod,"beforeOf_preseted")
				has_afterOf = hasattr(testmethod,"afterOf_preseted")
				if has_beforeOf :
					print "\t( before '%s' )" % " , '".join(testmethod.beforeOf_preseted)
				if has_afterOf :
					print "\t( after '%s' )" % " ,' ".join(testmethod.afterOf_preseted)
				if not any([
					has_beforeOf,has_afterOf
					]) :
					print ""

		return result_report_wrapper


        # Order Resolution
	def generate_ordered_tests(self):
		"""
		順序解決されたテスト名のリストを返す。
		"""
		#順序解決
		def resolve_order(test):
			if not hasattr(test,"beforeOf") :
				return
			for test_afterward_this in test.beforeOf :
				#起点となるテストより"前"にafterward_testsが定義されていれば順序を変更しなければならない
				if ordered_testnames.index(test_afterward_this) < ordered_testnames.index(test.__name__) :
					ordered_testnames.remove(test_afterward_this)
					ordered_testnames.insert(ordered_testnames.index(test.__name__)+1,test_afterward_this) # afterward_testをtestの後ろに

		#テストの抽出
		tests = [ self.testname2method(testname) for testname in self.filtered_names ]

		#テストの順序解決
		#after要素の変換と名前衝突のチェック
		filter(self.after2before,tests) #after要素をbefore要素に変換
		filter(self.check_order_fliction,tests) #すべてのテストについて順序衝突が起こっていないかチェック
		# beforeOf 要素内のテスト名のチェック
		for test in tests :
			hasattr(test,"beforeOf") and filter(self.testname2method,test.beforeOf)
				
		#順序解決
		ordered_testnames = list(self.filtered_names) #順序付けられた名前リスト
		filter(resolve_order,tests)

		return ordered_testnames

        def after2before(self,testmethod):
        	"""
        	テストメソッドを引数にとって、そのオブジェクトに設定されたテスト順序情報afterを順序指定先テストメソッドのbeforeに変換する。
        	"""
        	if not hasattr(testmethod,"afterOf"):
        		return
        	# すべての定義されたテストメソッドの前に実行されなければならないテストメソッドについて、
		# 自分自身を、それらのメソッドの前に実行されるように定義する
		# つまり test_before_this -> testmethod にする
        	for test_forward_this in testmethod.afterOf :
        		testmethod_forward_this = self.testname2method(test_forward_this)
        		#beforeの設定
			if not hasattr(testmethod_forward_this,"beforeOf") :
				testmethod_forward_this.im_func.beforeOf = []
			if testmethod.__name__ not in testmethod_forward_this.beforeOf :
				testmethod_forward_this.im_func.beforeOf.append(testmethod.__name__)

	def check_order_fliction(self,test,order_list=[]):
		"""
		テストメソッドを引数にとり、これを起点としてテスト順序衝突を検出する。
		"""
		if hasattr(test,"beforeOf") :
			#すべての順序付けられたテストについて
			#それが順序付けられたテストのリストに内包されていれば、これは順序衝突である。
			#さもなくば、再帰的に順序衝突を確認しなければならない。
			for afterward_test in test.beforeOf :
				#順序衝突
				if afterward_test in order_list :
					message = \
						"順序衝突が検出されました。\n\n"\
						+"衝突順序関係 : before -> after\n"\
						+"\t"+" -> ".join(order_list +[test.__name__] +[afterward_test])
					raise TestPreprocessError(message)

				#オーダーリストに自分を追加して再帰呼び出し
				else :
					#自らを追加したオーダーリストのコピーを生成
					orderlist_include_this = list(order_list + [test.__name__])
					#それをコンテキストに再帰呼び出し
					self.check_order_fliction(self.testname2method(afterward_test),orderlist_include_this)


        # Stop Profilling
        def stop_profiling(self):
        	"""
        	以降のテスト実行呼び出しセンテンスを無視する。
        	"""
        	def ignore_test(ins=None,Nouse1=None,Nouse2=None,**kwargs) :
        		"""以降のテストを無視するために代替えするテストダミー関数"""
			# Check args
			if ins is not None :
				assert isinstance(ins,self.testCaseClass)
			else :
				ins = self.testCaseClass()	#引数なしで初期化

			# スキップのレポート
			with Paragraph(Paragraph.H1,title="テストケース %d" % (self.processed_testcase+1),end_horizontal=False) as para :
				print "対象オブジェクト:\n\t%s" % repr(ins)
				print ""
        			print "TestFail Skipping : このテストケースは前のテストケースの失敗に基づき、スキップされます。"
        			self.processed_testcase += 1
        			self.skipped_testcase += 1

        	self.test = ignore_test


# Test Option Decorator
def create_decorator(*testnames,**order) :
	"""
	beforeOf,afterOfデコレータの共通論理部分。
	指定された順序の登録をクロージャーとしてデータを内包して行う、デコレーターを生成して返す
	"""
	# 引数チェック
	order = order["order"]
	assert order in ("beforeOf","afterOf")
	filter(check_testname,testnames)

	# 任意のテストメソッドを引数に取り、定義された情報に基づいて順序登録情報を修飾してそれを返すデコレータ関数
	def decorator(test_function):
		# 順序指定用のリストが定義されていないのなら、初期化
		if not hasattr(test_function,order) :
			setattr(test_function,order,[])
			setattr(test_function,order+"_preseted",[])
		# 順序指定するテスト名の登録 
		for testname in testnames :
			getattr(test_function,order).append(testname)
			getattr(test_function,order+"_preseted").append(testname)
		return test_function # 順序登録したテストメソッドを返す

	return decorator #クロージャーとしてデータの付されたデコレーターの返却

def beforeOf(*testnames):
	"""
	テスト名testnameを引数にとり、
	デコレートされるテスト関数を、そのtestnameテストの「前」に実行すべきものとして定義する。
	"""
	if not testnames :
		raise Exception("1つ以上のテストメソッド名を定義してください")
	return create_decorator(*testnames,order="beforeOf")

def afterOf(*testnames):
	"""
	テスト名testnameを引数にとり、
	デコレートされるテスト関数を、そのtestnameテストの「後」に実行すべきものとして定義する。
	"""
	if not testnames :
		raise Exception("1つ以上のテストメソッド名を定義してください")
	return create_decorator(*testnames,order="afterOf")


# Util
def check_testname(testname,error=True):
	"""引数がテスト名についての条件を充足しているか否かをチェック"""
	# Check Args
	assert isinstance(testname,str)
	if not testname.startswith("test") :
		if error :
			raise TestPreprocessError("テスト名はtestから始まらなければなりません。")
		else :
			return False



# Output Formatter
class Paragraph(object):
	"""
	段落を表現する出力フォーマット用オブジェクト。
	with文において用いる。
	"""
	H1 = 100
	H2 = 80
	H3 = 60
	def __init__(self,width,title=None,start_horizontal=True,end_horizontal=True):
		if not 0 <= width <= 150 :
			raise Exception("段落幅が大きすぎます")

		#水平線に関する情報
		self.width = width
		self.br = "\n" *(width /30)
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
		print self.br
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


