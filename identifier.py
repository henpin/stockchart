#! /usr/bin/python
#-*- coding: utf-8 -*-

"""
オブジェクトにユーザーフレンドリーな静的Id値を設定、利用するためのインターフェイスを提供するモジュール

Class構造:
	Identifier:
	オブジェクトに統一されたインターフェイスでID情報を保持、利用するための枠組みを与えるためのクラス。
	その初期化処理を呼ばなければーあるいは、引数としてID値を直接定義しなければー「IDを使用しない」こともできる。
	したがって、このクラスはすべてのほかのクラスが継承してかまわない。(それを利用するもしないも自由だからである。)

	このクラスは内部で定義されたIDホルダーオブジェクトのaddを呼び出し、ここで実際の紐づけが行われる。
	つまるところ、このインターフェイスは、そのオブジェクトにかかわるコンテキストとして「ID情報を定義する」だけで、
	その一意性の保証されたID-オブジェクトの紐づけ情報をID_Holderに格納する、という橋渡しと利用のための準備を内部で行うことができる。

	ID_Holder:
	実際のID-オブジェクトの紐づけ情報を保持するオブジェクト。単純に内部に辞書オブジェクトを持っており、これに関する機能を提供する。
	具体的には一意性を保証するためのエラーチェックと、登録されたID情報に対するオブジェクトを返す機能くらいである。
Usage:
	1,Identifierクラス(の初期化処理)を継承したユーザー実装クラスのインスタンスを作成する
	2,Identifierの初期化処理中で定義されたIDホルダーオブジェクトへの格納が行われ、ここで、実際のID値と、そのオブジェクトとの紐づけとその利用のための設定が行われる
	  なお、ID_ホルダーオブジェクトは明示的に定義しなければ、デフォルトでこのモジュールのグローバル名前空間に展開されるGLOBAL_ID_HOLDERが設定される。
"""

#グローバルIdホルダー:デフォルトではすべてのIDインスタンスはここに格納される
GLOBAL_ID_HOLDER = ID_Holder()

#Classes
class Identifier(object):
	"""
	Id値の設定と利用のための単純なインターフェイスです
	Id値は文字列か、あるいはint値でなければなりません。なお、文字列は小文字列に正規化されます。
	"""
	def __init__(self,id_val=None,id_holder=GLOBAL_ID_HOLDER):
		if id_val is not None :
			#Id機能有効
			self.set_id(id_val,id_holder)
		else :
			#Id機能無効
			self._set_no_available()	#IDに関する属性をNoneで初期化

	def set_id(self,id_val,id_holder=GLOBAL_ID_HOLDER):
		"""
		idの設定メソッド。
		このメソッドは、このオブジェクトがID機能を使用していないときに限り、実行される
		"""
		self._id = regulate_id(id_val)
		#IDホルダーが明示的に定義されなければ、グローバルIDホルダーがデフォルトで設定される.
		#モジュールとしてimportされた時も、暗黙の名前解決処理でこのモジュール内スコープのグローバル変数GLOBAL_ID_HOLDERが参照される
		self.id_holder = id_holder
		self.id_holder.add(self)

	def get_id(self):
		return self._id

	def identify(self,id_val):
		if not self.is_available() :
			raise Exception("このオブジェクトはID機能を利用していません")
		return id_val == self._id

	def regulate_id(self,id_val):
		"""
		IDイミュータブル値の、正規化とエラーチェックをおこなうユーティリティ。
		id値が健全な利用において不正でないかどうかを確認する
		例えば、クラスオブジェクトなどはIDに向かない
		また、文字列のID値は子文字列に正規化する。大文字小文字の混ざった文字列はコードを複雑にするだけである
		"""
		elif isinstance(id_val,int) :
			#int型の正規化
			if 0 < id_val <= 99999:
				return id_val
			else :
				raise Exception("int値としてのid値には1以上100000以下を指定してください")
		elif isinstance(id_val,str) :
			if id_val <= 2 :
				raise Exception("文字列としてのID値としては２文字以上を指定してください")
			#文字列型の正規化
			return id_val.lower()
		else :
			#型エラー
			raise TypeError("ID値にはint型かstr型を受け付けます")

	def is_available(self):
		return self._id

	def set_no_available(self):
		"""
		このオブジェクトのID機能を利用不能モードで「再」初期化する。
		このメソッドは、「現在ID機能を利用中」のオブジェクトの再初期化のためのメソッドである。
		つまり、ID_Holderに対しての紐づけ解除も内部で行う。
		その為、単純な非利用モードとしての初期化には、「隠蔽された」self._set_no_availableを用いなければならない。
		"""
		if not self.is_available() :
			raise Exception("このオブジェクトはID利用中ではありません。")
		self.id_holder.delete(self)

	def _set_no_available(self):
		"""
		このオブジェクトのID機能を非利用モードで初期化する。
		コード内部で単純な初期化処理を行う場合には、この隠蔽されたメソッドを用いる。
		"""
		self._id = None
		self.id_holder = None


class ID_Holder(Identifier):
	"""
	Identifierインスタンスへの参照リストを格納し、そのid情報を走査するための枠組みを提供するクラス
	"""
	def __init__(self,id_val=None,id_holder=None):
		"""
		IdホルダーもIDインターフェイスをサポートする。
		ただし、自分自身をIDに紐づけされた要素として格納することはできない。
		"""
		if id_holder is self :
			raise Exception("IDホルダーは、自分自身をID値に対する内容オブジェクトとして保持できません。")

		self.id_dict = {}	#ID値に紐づけされたオブジェクトの辞書
		Identifier.__init__(self,id_val,id_holder)

	def add(self,identifier):
		"""
		identifierインスタンスを引数にとり、このIDホルダーに追加します
		もちろん、ID値に対する一意性を保証するチェックも行う
		"""
		if not isinstance(identifier,Identifier) :
			raise TypeError("引数がId格納型でありません")

		#新しいID値のエラーチェックと登録
		new_id = identifier.get_id()
		if new_id in self.id_dict :
			raise Exception("既にid値 %s はこのIdHolderに存在しています" % (new_id) )
		else :
			self.id_dict[new_id] = identifier

	def delete(self,identifier):
		"""
		identifierインスタンスを引数にとり、このIDホルダーから消去します
		また、消去されたidentifierの利用状況に関するフラグも再設定します。
		"""
		removal_id = identifier.get_id()
		if removal_id not in self.id_dict :
			raise Exception("id値 %s はこのIdHolderに存在していません" % (removal_id) )
		else :
			self.id_dict.pop(removal_id)
			identifier._set_no_available()

	def find(self,id_val):
		"""格納するidentifiersから引数値id_valを持ったIdentifierオブジェクトを探し、返す"""
		if id_val in self.id_dict :
			return self.id_dict[id_val]
		else :
			raise Exception("id値 %s はこのIDホルダーに存在しません" % id_val)

	def has_id(self,id_val):
		return self.id_dict.has_key(id_val)

		


