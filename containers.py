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
	*Base_Container
		->Single_Container = _child
		->Plural_Container = _children
		->Container_Of_Container = _child_containers
	*Contained
"""

class Base_Container(object):
	"""
	コンテナオブジェクトの最小抽象基底クラス。
	"""
	#Class Global Variables
	implement_types = (
		Single_Container,
		Plural_Container,
		Container_Of_Container,
		)#コンテナ実装型のタプル

	#Methods
	def __init__(self):
		"""
		すべてのコンテナ実装型がこの初期化ルーチンを呼ばなくてはならない。
		この初期化ルーチンでは、コンテナの多様性に関する初期化処理を行う。
		"""
		self.valid_types = []	#格納を許可するオブジェクトの型のリスト。要素がないならテストを無視
		self.valid_container_type = None	#コンテナの多様性をもたせる為の枠組み。現在有効な(ただ１つの)コンテナ型の情報。
		self.need_container_diversity = False	#コンテナ多様性の必要性

		#initial subroutine
		self.set_valid_container_type()	#有効実装型の初期設定。２つ以上の実装型が継承されているときには未定義にしておく
	
	def __iter__(self):
		"""
		イテラブルにします。
		コンテナ多様性のために隠蔽されたクラスのメソッドを呼び出します。
		"""
		self.test_valid_container_type()
		children = self.valid_container_type._get_children(self)
		return iter(children)

	def _get_children(self):
		"""
		基底メソッド。オーバーライド必須。
		多様性のための冗長な隠蔽メソッド。
		"""
		raise Exception("オーバーライド必須です")

	def test_child(self,child):
		"""
		与えられた引数childがこのContainerに適合する型であるかを判別し、そうでないならエラーを送出します。
		"""
		if not isinstance(child,Contained) :
			raise TypeError("引数がContainedオブジェクトでありません")
		elif self.valid_types and not any( isinstance(child,type) for type in self.valid_types ) :
			raise TypeError("引数が許可された型のオブジェクトではありません")

		return True

	def test_valid_container_type(self):
		"""
		ちゃんと有効コンテナ型が定義されているか確認するユーティリティ
		"""
		if self.valid_container_type is None :
			raise Exception("有効コンテナ型が未定義です。")

	def add_valid_type(self,valid_type):
		"""
		子オブジェクトの型指定を行う。
		引数には型オブジェクトかあるいは、そのタプルをとる。
		"""
		#旧型クラスのダミー。クラスオブジェクトであるかどうかを確認する為
		class OldStyleClass :
			pass

		#引数がタプルなら要素ごとの再起呼び出しを行い、あるいは型オブジェクトでなければ例外を送出
		if isinstance(valid_type,tuple) :
			for each_type in valid_type :
				self.add_valid_type(each_type)
		elif type(valid_type) is not type and type(valid_type) is not type(OldStyleClass) :
			raise TypeError("型オブジェクトでありません")
		else :
			self.valid_types.append(valid_type)	#登録

	def set_valid_container_type(self,valid_type=None):
		"""
		現在有効なコンテナ型を設定する。
		デフォルトの初期化処理では明示的な型指定はなしで呼ばれ、
		もし、ただ唯一のコンテナ実装型のみがこのメソッドの呼び出し元に継承されていれば、それをデフォルトで設定する。
		"""
		#初期化処理
		def set_valid_container_type_default():
			#継承している実装型を真偽値で表すリスト
			inherited = [ boolean for container_type in self.implement_types is isinstance(self,container_type) ] 

			if inherited.count(True) == 1 :
				#継承されているコンテナ実装型が唯一ならば、それを有効コンテナ型に設定
				index_of_inherited = (lambda(index):
					(index_of_inherited(index+1) if not inherited[index] or index)
					)(0)	#継承されている唯一の型を表すindexの算出
				#設定
				self.valid_container_type = implement_types[index_of_inherited]
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
		self.add_valid_type(Base_Container)

	def add_child_container(self,container):
		self.is_valid_container_type(Plural_Container)
		self.test_child(container)
		self._child_containers.append(container)
		content._set_container(self)

	def _get_children(self):
		return self._child_containers


class Contained(object):
	"""
	コンテナオブジェクトの子オブジェクトとなる型のインターフェイス
	"""
	def __init__(self):
		self._container = None

	def _set_container(self,container):
		self._container = container

	def get_container(self):
		return self._container


if __name__ == '__main__' :
	print "The Program Is Gone Now"


