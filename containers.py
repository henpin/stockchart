#! /usr/bin/python
#-*- coding: utf-8 -*-

"""
	コンテナーに共通するオブジェクトの枠組みを提供する基底クラス群に関するモジュール。

	#ContainerとContained
	このモジュールは、Containerオブジェクト及び、Containedオブジェクトからなります。
	Containerオブジェクトが格納するすべてのオブジェクトは、Containedオブジェクトである必要があります。

	#コンテナの多様性
	このモジュールは、ユーザー定義型が、２つ以上コンテナ実装型(Base_Container以外のすべてのコンテナ型)を継承することをサポートしています。
	このコンテナの"多様性"の為にBase_Container及び各実装型の諸メソッド内において、「有効実装型」の設定と、そのチェックを行うための文脈を定義しています。

	すべてのコンテナオブジェクトは、「有効コンテナ型」"ごと"に、それぞれ、
	「被コンテナオブジェクト（あるいはそのリスト)」と、「(子コンテナの格納に関する)有効適合型-のリスト」を内部に格納していて、
	つまり、ある(コンテナ多様性を有する)同一オブジェクト内においての、testメソッド(-とそのテスト内容)、あるいはset/add/getなどのその「子要素」に関するメソッド
	のふるまいは、そのときの、「有効コンテナ型」の如何によって、多様である。ということです。

	ただし、ユーザーは、この内部的な(-"多様性"に関する-)複雑性について何ら気にする必要はありません。
	その「コンテナ多様性」を利用するときには、「有効コンテナ型の設定」だけを明示的に定義すれば、統一されたインターフェイスによって内部のデータにアクセスできますし
	また、内部では、その定義された「有効コンテナ型」についての情報に基づいて、"自動"で要素テストの内容などを(変更、)実施、します。


	*なお、被コンテナオブジェクトのコンテナオブジェクトへの「追加」に関してだけは、あえて名前を統一せず、大変な冗長性を持たせています。
	これは、単純に、コンテナ実装型ごとに「被コンテナーあるいはそのリスト」を内部に格納するため、多重継承による
	addメソッドのオーバーライドによってその("コンテナ多様性"の-)枠組みが破たんしてしまうという事情と、
	他方は、"実装"コンテナ型を無視した統一された名前(-例えばaddなど-)だと、ユーザー実装コードの表面からは、内部の「有効コンテナ型」に関する情報が完全に隠蔽されて-
	上記の"多様性"の副作用として、「実はユーザーが意図した処理とは全く別の処理がー内部の実際の有効コンテナ型の情報に基づいてー"自動で"ー実施された」という
	典型的なバグの混入が予想されるためです。

	-ただし、Base_Containerには、そのショートカットとして、単一の名前で現在有効なコンテナ型としてコンテナ内部に被コンテナを格納するメソッドadd()が定義されています
	これは内部で自動で「現在有効なコンテナ型」の隠蔽された統一メソッド_add()を呼び出します。
	ハードコードされたそれぞれの実装型独自の要素追加メソッド名を使うか、自動で有効コンテナ型の要素追加メソッドを間接に呼び出す
	(-内部の有効コンテナ型に関する情報を表面的には完全に隠蔽する-)Base_Containerのショートカット名(add)を用いるかは、ユーザーの判断に任されます。


	#クラス階層
	*Contained	=被コンテイン共通インターフェイス	=_container
		->Base_Container	=多様性および共通ロジックのサポート
			->Single_Container = _child
			->Plural_Container = _children
			->Container_Of_Container = _child_containers

	#Usage
	#コンテナクラスの継承と格納、あるいはその多様性に関する設定
	1, 任意の1つ以上の「コンテナ実装型」(Base_Container以外のコンテナクラス)を継承したクラスを生成する。
	2, 2つ以上のコンテナ実装型を継承した場合は、set_valid_container_type()によって「有効コンテナ型」を定義する。これは任意のコンテナ実装型でなければならない。
	   なお、ただ１つの実装型のみ継承した場合は、この「多様性の為の冗長システム」はスキップされ、内部で細かい変数群は自動設定される。
	3, コンテナオブジェクトのadd_valid_type()によって「格納可能型」を明示的に定義できる。
	   このメソッドで登録した「型-クラスオブジェクト」はその被格納オブジェクトの登録:add時の型チェックに用いられる。
	   なお、「コンテナ適合な型」が明示的に(このメソッドによって)定義されるまでは、デフォルトで、任意の型のオブジェクトを格納できる。

	#被コンテナクラスの継承
	4, Containedクラスを継承した「被コンテイン(=被格納)オブジェクト」を生成する。
	   このオブジェクトは親コンテナにアクセスする手段だけを有し、ほかの内部プロパティの設定などは、親コンテナを通して、行われるためユーザーが触る部分はない。

	#コンテナへの被コンテナオブジェクトの登録
	5, コンテナオブジェクトのset_.../又はadd_...メソッドによってContainedオブジェクトをコンテナオブジェクトに登録する。

	   *この子オブジェクトの登録に関するメソッド名は、その「コンテナ多様性」を用いた際、
	   分離されたメソッド名によって意味的な可読性とバグ検出の容易さをきわめて増幅させるであろうことからつけられた、冗長なものである。
	   ただし、Base_Containerにはそのショートカットとしてaddメソッドが定義されており、これは内部で適切(とはいえそれが必ずしもユーザーが意図しているとは限らない)な
	   被コンテナ登録メソッドを呼び出す。
	
	#利用
	6, コンテナ型はget_children()を有し、現在アクティブな有効コンテナ型に対する内部に格納された被コンテナオブジェクト(あるいはそのリスト)を取り出せる。
	   なお、コンテナ型はイテラブルである。この列挙処理の際、結局内部ではget_children()が呼ばれている。
	7, 被コンテナ型は、get_parent()あるいはget_father()を有する。これによって親コンテナオブジェクトを取り出せる。
"""

class Contained(object):
	"""
	コンテナオブジェクトの子オブジェクト(=被コンテイン型)となる型のインターフェイス
	"""
	def __init__(self):
		self._container = None

	def _set_container(self,container):
		if self.get_parent() is not None :
			raise Exception("既に親コンテナを持っています。")
		elif not isinstance(container,Base_Container) :
			raise TypeError("引数がコンテナオブジェクトでありません")
		#Set
		self._container = container

	def get_parent(self):
		return self._container

	def get_father(self):
		"""
		親コンテナを持たない最上位のコンテナオブジェクトを得る
		最上位にたどり着く為に条件分岐の再帰呼び出しを用いる。
		"""
		parent = self.get_parent()
		#親がいないのならNoneを返す
		if parent is None :
			return None
		#親コンテナがさらに親を有するのならそれについて再帰呼び出しをし、親の親がいないのなら、単に親をそのまま返す。
		return parent if parent.get_father() is None else parent.get_father()


class Base_Container(Contained):
	"""
	コンテナオブジェクトの最小抽象基底クラス。
	すべてのコンテナオブジェクトは、被コンテナでもある。つまり、この最小基底クラスはContainedを継承する。
	"""
	def __init__(self):
		"""
		すべてのコンテナ実装型がこの初期化ルーチンを呼ばなくてはならない。
		この初期化ルーチンでは、コンテナの多様性に関する初期化処理を行う。
		"""
		Base_Container.implement_types = (
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

	def add(self,child):
		"""
		オーバーライド禁止。連鎖的に然るべきオブジェクトの隠蔽された_add()を呼ぶ。
		後の処理はすべて呼び出し先のメソッドに完全に移譲する。
		"""
		self.test_valid_container_type()
		return self.get_valid_container_type()._add(self,child)

	def _add(self):
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
		if implement_type is None :
			implement_type = self.get_valid_container_type()
			if implement_type is None :
				raise Exception(
				"格納する子オブジェクトの型指定について、それを設定するコンテナ型が引数に定義されておらず、かつ有効実装型も未定義です。")

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
		この基底オブジェクトの外部から呼ばれる
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
	_add = set_child	#隠蔽されたエイリアス。

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
	_add = add_child	#隠蔽されたエイリアス。

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
	_add = add_container	#エイリアス

	def _get_children(self):
		return self._child_containers


if __name__ == '__main__' :
	print "containers.py : コンテナオブジェクトのインターフェイス群を提供するモジュールです。"

