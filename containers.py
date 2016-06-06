#! /usr/bin/python
#-*- coding: utf-8 -*-

"""
	コンテナーに共通するオブジェクトの枠組みを提供する基底クラス群に関するモジュール。

	#ContainerとContained
	このモジュールは、Containerオブジェクト及び、Containedオブジェクトからなります。
	Containerオブジェクトが格納するすべてのオブジェクトは、Containedオブジェクトである必要があります。

	#コンテナの多様性
	このモジュールは、ユーザー定義型が、２つ以上コンテナ実装型(Base_Container以外のすべてのコンテナ型)を継承することをサポートしています。
	このコンテナの"多様性"の為にBase_Container及び各実装型の諸メソッド内において、
	「有効実装型」の設定と、そのチェックを行うための文脈を定義しています。

	#クラス階層
	*Contained	=被コンテイン共通インターフェイス	=_container
		->Base_Container	=多様性および共通ロジックのサポート
			->Single_Container = _child
			->Plural_Container = _children
			->Container_Of_Container = _child_containers
"""

class Contained(object):
	"""
	コンテナオブジェクトの子オブジェクト(=被コンテイン型)となる型のインターフェイス
	"""
	def __init__(self):
		self._container = None

	def _set_container(self,container):
		if self.get_container() is not None :
			raise Exception("既に親コンテナを持っています。")
		self._container = container

	def get_container(self):
		return self._container


class Base_Container(Contained):
	"""
	コンテナオブジェクトの最小抽象基底クラス。
	すべてのコンテナオブジェクトは、被コンテナでもある。つまり、この最小基底クラスはContainedを継承する。
	"""
	#Methods
	def __init__(self):
		"""
		すべてのコンテナ実装型がこの初期化ルーチンを呼ばなくてはならない。
		この初期化ルーチンでは、コンテナの多様性に関する初期化処理を行う。
		"""
		self.implement_types = (
			Single_Container,
			Plural_Container,
			Container_Of_Container,
			)#コンテナ実装型のタプル
		#コンテナinコンテナのサポートのためContainedの初期化処理の呼び出し
		Contained.__init__(self)

		#格納を許可するオブジェクトの型のリスト。要素がないならテストを無視。多様性のために有効実装型ごとに格納
		self.valid_types = { implement_type:[] for implement_type in self.implement_types }
		self.valid_container_type = None	#コンテナの多様性をもたせる為の枠組み。現在有効な(ただ１つの)コンテナ型の情報。
		self.need_container_diversity = False	#コンテナ多様性の必要性

		#initial subroutine
		self.set_valid_container_type()	#有効実装型の初期設定。２つ以上の実装型が継承されているときには未定義にしておく
	
	def __iter__(self):
		"""
		イテラブルにします。
		コンテナ多様性のために隠蔽されたクラスのメソッドを呼び出します。
		"""
		self.test_valid_container_type()	#有効コンテナ型が定義済か確認
		return iter(self.get_children())

	def get_children(self):
		"""
		オーバーライド禁止。連鎖的に然るべきオブジェクトの隠蔽された_get_children()を呼ぶ。
		"""
		return self.get_valid_container_type()._get_children(self)

	def _get_children(self):
		"""
		基底メソッド。オーバーライド必須。
		多様性のための冗長な隠蔽メソッド。
		"""
		raise Exception("オーバーライド必須です")

	def test_child(self,child,implement_type=None):
		"""
		与えられた引数childがこのContainerに適合する型であるかを判別し、そうでないならエラーを送出します。
		"""
		valid_list = self.valid_types[self.get_valid_container_type()]
		if not isinstance(child,Contained) :
				raise TypeError("引数がContainedオブジェクトでありません")
		elif valid_list and not any( isinstance(child,type) for type in valid_list ) :
			raise TypeError("引数が許可された型のオブジェクトではありません")

		return True

	def test_valid_container_type(self):
		"""
		ちゃんと有効コンテナ型が定義されているか確認するユーティリティ
		"""
		if self.valid_container_type is None :
			raise Exception("有効コンテナ型が未定義です。")

	def add_valid_type(self,valid_type,implement_type=None):
		"""
		子オブジェクトの型指定を行う。
		引数には型オブジェクトかあるいは、そのタプルをとる。
		"""
		#旧型クラスのダミー。クラスオブジェクトであるかどうかを確認する為
		class OldStyleClass :
			pass

		#引数調整
		if implement_type is  None :
			implement_type = self.get_valid_container_type()
			if implement_type is None :
				raise Exception("子オブジェクトの型指定について、有効型が設定されておらず、かつ有効実装型も未定義です。")

		#引数がタプルなら要素ごとの再起呼び出しを行い、あるいは型オブジェクトでなければ例外を送出
		if isinstance(valid_type,tuple) :
			for each_type in valid_type :
				self.add_valid_type(each_type)
		elif type(valid_type) is not type and type(valid_type) is not type(OldStyleClass) :
			raise TypeError("型オブジェクトでありません")
		else :
			self.valid_types[implement_type].append(valid_type)	#登録

	def set_valid_container_type(self,valid_type=None):
		"""
		現在有効なコンテナ型を設定する。
		デフォルトの初期化処理では明示的な型指定はなしで呼ばれ、
		もし、ただ唯一のコンテナ実装型のみがこのメソッドの呼び出し元に継承されていれば、それをデフォルトで設定する。
		"""
		#初期化処理
		def set_valid_container_type_default():
			#継承している実装型を真偽値で表すリスト
			inherited = [ isinstance(self,container_type) for container_type in self.implement_types ]

			if inherited.count(True) == 1 :
				#継承されているコンテナ実装型が唯一ならば、それを有効コンテナ型に設定
				index_of_inherited = (lambda(index):
					(index_of_inherited(index+1) if not inherited[index] else index))
				index = index_of_inherited(0)
				#設定
				self.valid_container_type = self.implement_types[index]
				self.need_container_diversity = False
			elif not any(inherited) :
				#いかなる実装型も継承されていなければ例外を送出
				raise Exception("いかなるコンテナ実装型も継承されていません")
			else :
				self.need_container_diversity = False	#コンテナ多様性は必要である
				return	#複数継承。有効型は未定義で返す

		#明示的な有効コンテナ型の設定
		def set_valid_container_type_explicit():
			if not isinstance(self,valid_type) :
				raise TypeError("継承していない型を有効型にはできません")
			#設定
			self.valid_container_type = valid_type

		#Do Setting
		if valid_type is None :
			set_valid_container_type_default()
		else :
			set_valid_container_type_explicit()

	def get_valid_types(self):
		return self.valid_types
	
	def get_valid_container_type(self):
		return self.valid_container_type

	def is_valid_container_type(self,container_type,error=True):
		"""
		有効コンテナ型かどうか。
		"""
		self.test_valid_container_type()	#そもそも、ちゃんと定義済かどうかのチェック
		if self.valid_container_type is container_type :
			return True
		else :
			if error :
				raise TypeError("%sは有効コンテナ型ではありません。" % container_type)
			return False

		
class Single_Container(Base_Container):
	"""
	１つの何らかのオブジェクトを「内包」するための枠組みを提供する抽象規定クラス
	「１つ以上」のオブジェクトを格納するには、このクラスの継承クラスplural_containerを用いる
	"""
	def __init__(self):
		Base_Container.__init__(self)
		self._child = None

	def set_child(self,content):
		self.is_valid_container_type(Single_Container)
		self.test_child(content)
		self._child = content
		content._set_container(self)

	def _get_children(self):
		return self._child

class Plural_Container(Base_Container):
	"""
	１つ以上の任意の個数のオブジェクトを格納するするためのコンテナオブジェクトに関する枠組みを規定する抽象規定クラス
	"""
	def __init__(self):
		Base_Container.__init__(self)
		self._children = []

	def add_child(self,content):
		self.is_valid_container_type(Plural_Container)
		self.test_child(content)
		self._children.append(content)
		content._set_container(self)

	def _get_children(self):
		return self._children


class Container_Of_Container(Base_Container):
	"""
	１つ以上のコンテナオブジェクトを有するコンテナオブジェクトを定義するための抽象基底クラス。
	機能的にはPlural_Containerのサブセットだが、コンテナ多様性のためにあえて全く別のクラスとして実装
	"""
	def __init__(self):
		Base_Container.__init__(self)
		self._child_containers = []
		self.add_valid_type(Base_Container,Container_Of_Container)

	def add_container(self,container):
		self.is_valid_container_type(Container_Of_Container)
		self.test_child(container)
		self._child_containers.append(container)
		container._set_container(self)

	def _get_children(self):
		return self._child_containers


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
	tester = Tester()
	tester.test_all()


