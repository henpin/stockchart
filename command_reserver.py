#! /usr/bin/python
# -*- coding: utf-8 -*-

import copy

"""
コマンドの予約とその管理、実行に関するインターフェイスを定義するモジュール。
このモジュールでは、「予約されたコマンドを管理するオブジェクト」および
「実行可能コマンドと、実行可能タイミングを判断する関数、また、それに関する個別のプライベートな値、の３つを格納する予約可能コマンドオブジェクト」を規定する。

クラス :
	Command_Reserver:
		コマンド格納オブジェクト。
		self.reserve_command(command)で予約可能コマンドオブジェクトを格納し、
		self.resolve_command(command)で予約済みコマンドを「解決」する。
		また、予約済みコマンド取り消しのための機能も提供されており、self.cancel_command(command)を用いる。

	Reserved_Command:
		予約可能オブジェクト
		予約するコマンドcommandおよび実行可能タイミングを判定するcircumstanceを、呼び出し可能オブジェクトとして少なくとも格納する。
		また、オプショナルで、その条件判定に用いることのできる規定値valをオブジェクト生成時に定義できる。
		この値はその実行可能タイミングの判断関数self.circumstance()の唯一の引数として「常に」定義される。

		コマンドの「解決」はself.resolve_command()の呼び出しによって行われ、このメソッドはself.circumstance(self.val)を呼び出す。
		この条件判定関数が真を返せば定義されたコマンド関数self.command()を引数なしで呼び出す。

コマンドの「解決」:
	コマンドの解決は、まず、Command_Reserverのself.resolve_command()の呼び出しから始まる。
	このメソッドは、このオブジェクトに格納されたすべての予約済みコマンドについて、command.resolve_command()を呼び出す。

	すべてのReserved_Commandオブジェクトはこのself.resolve_command()の呼び出しに基づいて
	self.circumstance()を呼び出す。この返り値が真なら、self.command()を実行し、さもなくば実行しない。
	このself.resolve_command()の返り値はself.circumstance()の返り値である。つまり、コマンドを実際に実行したか否かに完全に対応する。

	Command_Reserverはこの返り値を見て、コマンドが実行されたか否かを判定する。
	もし、コマンドが実行されたなら、その予約済みオブジェクトの予約を消去する。つまり、self.reserved_commands.remove(command)を単純に行う。

クロージャーの利用:
	Reserved_Commandオブジェクトは、オプショナルな融通の利く隔たれた変数をなんら持たない。
	この制約は、多くの実際的なロジックの設計に、直接的な大きな制約を及ぼすように思われる。
	しかし、一方実際には、この「制約」は、多く、このオブジェクトのまとまりの利用範囲を著しく制限するものでは「ない」。
	なぜならば、Reserved_Commandオブジェクトは、「実行タイミング判断値」および「実行コマンド値」を、それぞれ、「関数」として有するからである。

	つまり、Reserved_Commandは直接的には、高々、上述の2つの「値」しか内部に格納しないが、
	しかし、「クロージャー」を利用することで、その関数スコープ固有の任意の個数の任意の「値」を、少なくとも疑似的に内部に「格納ー保有」することができるのである。
	つまり、このモジュールを利用する実装が、クロージャーを利用すれば、このモジュールの提供する枠組みは、特別な拡張なしに、きわめて広い範囲のロジックを実装でき得る

usage :
	1,Command_Reserverオブジェクトの生成
		book = Command_Reserver()
	2,Reserved_Commandの生成。
		able_to_execute = ( lambda val : True )
		command = ( lambda : do_nothing() )
		reserved_command = Reserved_Command(command,able_to_execute)
	3,コマンドの登録
		book.reserve_command(reserved_command)
	4,コマンド管理オブジェクトの「コマンド解決」メソッドの呼び出し
		book.resolve_command()
			-> reserved_commands.resolve_command()
				-> if reserved_commands.able_to_execute():
					reserved_commands.command()
			-> if forward :
				book.cancel_command(reserved_commands)
	
"""

class Command_Reserver(object):
	"""
	コマンド予約可能オブジェクト
	"""
	def __init__(self):
		self.reserved_commands = []	#予約済みコマンドのリスト

	def check_command(self,command):
		"""コマンドオブジェクトが十分妥当か判断するユーティリティ"""
		if not isinstance(command,Reserved_Command) :
			raise TypeError("引数がCommandオブジェクトでありません")

	def has_command(self,command):
		"""定義された引数commandが自身に登録されているか否か"""
		return ( command in self.reserve_commands )

	def reserve_command(self,command):
		"""
		コマンドの予約メソッド。
		引数にコマンドオブジェクトをとる。
		"""
		self.check_command(command)
		if self.has_command(command) :
			raise Exception("このコマンドオブジェクトは既に登録されています。同じ内容を登録するには、コマンドオブジェクトを複製してください。")

		self.reserved_commands.append(command)

	def cancel_command(self,command):
		"""
		コマンドをキャンセルします。
		このメソッドは冗長なエラー送出を行います。
		"""
		self.check_command(command)
		#取り消し
		if self.has_command(command) :
			self.reserved_commands.remove(command)
		else :
			raise Exception("指定されたコマンドオブジェクトが予約済みコマンドリストに存在していません")

	def resolve_command(self):
		"""
		予約済みコマンドの解決を行う
		"""
		for command in copy.copy(self.reserved_commands) :
			if command.resolve_command() :
				self.cancel_command(command)


class Reserved_Command(object):
	"""
	予約可能コマンドオブジェクト。

	内部に少なくとも
	1,予約するコマンド(callable-object)
	2,どの条件で予約を解決するかについての条件関数(callable)
	の両方をを有する。
	"""
	def __init__(self,command,circumstance):
		"""
		必須の値command,circumstanceの設定
		"""
		if not ( callable(command) and callable(circumstance) ) :
			raise TypeError("コマンドcommandおよび条件判断関数circumstanceは少なくとも呼び出し可能でなければなりません。")
		#属性
		self.command = command
		self.circumstance = circumstance

	def resolve_command(self):
		"""
		コマンドの解決を行う。
		もし、self.circumstance(self.val)が真を返せば、このオブジェクトのコマンドを解決する。
		"""
		condition = self.circumstance()
		#条件判定が真ならコマンドを実行
		if condition :
			self.command()
		return condition


