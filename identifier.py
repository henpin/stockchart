#! /usr/bin/python
#-*- coding: utf-8 -*-

"""
オブジェクトにユーザーフレンドリーな静的Id値を設定、利用するためのインターフェイスを提供するモジュール
"""

class Identifier(object):
	"""
	Id値の設定と利用のための単純なインターフェイスです
	Id値は文字列か、あるいはint値でなければなりません。なお、文字列は小文字列に正規化されます。
	"""
	def __init__(self,id_val,id_holder):
		self._id = check_id(id_val)
		self.id_holder = id_holder or GLOBAL_ID_HOLDER	#モジュールとしてimportされた時も、暗黙の名前解決処理でこのモジュール内のグローバル変数が参照される
		self.id_holder.add(self)

	def get_id(self):
		return self._id

	def identify(self,id_val):
		return id_val is self._id

	def check_id(self,id_val):
		"""
		id値が健全な利用において不正でないかどうかを確認する
		例えば、クラスオブジェクトなどはIDに向かない
		また、文字列のID値は子文字列に正規化する。大文字小文字の混ざった文字列はコードを複雑にするだけである
		"""
		if not isinstance(id_val,(str,int)):
			raise TypeError("Id値はint値か文字列です")

		return id_val	#未定義


class Id_Holder(object):
	"""
	Identifierインスタンスへの参照リストを格納し、そのid情報を走査するための枠組みを提供するクラス
	"""
	def __init__(self):
		self.id_dict = {}

	def add(self,identifier):
		"""
		identifierインスタンスを引数にとり、このIDホルダーに追加します
		"""
		if not isinstance(identifier,Identifier) :
			raise TypeError("引数がId格納型でありません")

		new_id = identifier.get_id()
		if new_id in self.id_dict :
			raise Exception("既にid値 %s はこのIdHolderに存在しています" % (new_id) )
		else :
			self.id_dict[new_id] = identifier

	def find(self,id_val):
		"""格納するidentifiersから引数値id_valを持ったIdentifierオブジェクトを探し、返す"""
		if id_val in self.id_dict :
			return self.id_dict[id_val]
		else :
			raise Exception("id値 %s はこのIDホルダーに存在しません" % id_val)

	def has_id(self,id_val):
		return self.id_dict.has_key(id_val)

		
#グローバルIdホルダー:デフォルトではすべてのIDインスタンスはここに格納される
GLOBAL_ID_HOLDER = Id_Holder()


