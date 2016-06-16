#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
一般的なイベント処理に関する枠組みを提供するモジュール
このモジュールで規定されるイベント処理の責任を担うオブジェクトに付されるインターフェイスとしての基底クラスは、自由に拡張可能である。


クラス構造:
	#クラス図
	Event_Listener
		-> Event_Processor	<- generate_event_processor
		-> Event_Distributer

	#概説
	Event_Listener:
		イベントを受け取る為の共通インターフェイス。
		receive_event()メソッドを備える。基底クラス。

	Event_Distributer <- Event_Listener :
		イベントを分配する上位インターフェイス。
		イベント処理インターフェイスEvent_Processorと同時に利用できる。
		この場合、そのオブジェクトは、「伝搬可能」な、イベント処理オブジェクトとなる。

	Event_Processor <- Event_Processor :
		イベント処理オブジェクト。
		イベント名に対するその処理メソッドprocess_EVENTTYPEを備えてなければならない。
		#拡張性に関する冗長部分
		拡張性、また再利用の為に静的なイベント名のセットに対する処理メソッドインターフェイス群を有した実装型は定義してない。
		常に利用側モジュールのほうで、generate_event_processor(event_names)を呼び出し、動的にイベントインターフェイスそのものを生成しなければならない。
	
Usage :
	# 実装クラスの生成と、イベントの枠組みの利用
	1,実装イベント処理型の定義、生成
		Event_Processor = generate_event_processor(event_names)

	2,実装イベント処理型のprocess_インターフェイスのオーバーライド。
		Event_Processor.process_EVENTTYPE = function

	3,イベント分配オブジェクトの生成と、イベント伝搬のためのget_next_targetのオーバーライド。
		root_distributer = Event_Distributer()
			root_distributer.set_default_target = Event_Listener_obj
		node_distributer = Event_Distributer()
			node_distributer.get_next_target = function (-> Event_Listener or None )

	# イベントの送出と受け取り。
	4,イベント分配オブジェクトのsend(event_type,event_obj,target)を呼び出し、イベントを送出する。
	  送出されたイベントは、すべからく、定義されたイベント送出対象オブジェクトEvent_Listenerのイベント受け取りインターフェイスreceive_event()を呼び出す。
		target = Event_Listener
		root_distributer.send(event_obj,event_obj,target)
			-> target.receive_event(event_type,event_obj)

	# イベントハンドラの呼び出し
	5,Event_Processorに再定義されているreceive_event()は定義されたイベントタイプに対応するprocess_メソッドを呼び出す
		Event_Processor.receive_event(event_type,event_obj)
			-> if Event_Processor.handlable(event_type) :
				Event_Processor.process_EVENTTYPE(event_obj)
		尚、Event_Processorがそのイベント名に対応するprocess_メソッドを持たない場合、例外を送出する。
		つまり、このとき、被イベント送出対象オブジェクトは、常にそのイベント名に対するprocessインターフェイスを持っていなければ、ならない。
			
	# イベントの伝搬
	6,Event_Distributerに再定義されているreceive_event()はself.bubbling()メソッドを内部で呼び出して、イベントの伝搬を行う
		Event_Distributer.receive_event(event_type,event_obj)
			-> Event_Distributer.bubbling(event_type,event_obj)
		尚、被イベント送出対象オブジェクトが、Event_Distributerであり且つEvent_Processorであったなら、
		「初めに」Event_Processorのreceive_event()を呼び出し、そのあとに、Event_Distributerのreceive_event()を呼び出す。

	7,イベントの伝搬に関する実装処理ルーチンbubblingは、その伝搬先を決定するself.get_next_target()を呼び出し、
	　もし、その返り値がEvent_Listenerならば、再帰的にそのイベントリスナーに対してイベントをsendする。
		Event_Distributer.bubbling(event_type,event_obj)
			-> self.get_next_target() ( -> Event_Listener or None )
				self.send(event_type,event_obj,next_target)

イベントの伝搬:
	イベント分配オブジェクトEvent_Distributerはイベントを伝搬させる。
	具体的にはEvent_Distributer.send()によって単純にイベントを送出した後、その送出先オブジェクトのbubbling()メソッドを呼び出す。

	このbubblingメソッドはそのオブジェクトのget_next_target()を呼び出し、次の伝搬先オブジェクトを決定する。
	もしこれが偽をとれば、そのイベントの伝搬ーバブリングは停止する。
	伝搬先がEvent_Listenerであれば、そのbubblingメソッドは、再帰的に、そのオブジェクトに対して再びイベントをsendする。

"""
#デフォルトのイベント名
DEFAULT_EVENT_NAMES = (
	"KEYDOWN",
	"MOUSEBUTTONDOWN",
	"MOUSEMOTION",
	"MOUSEDRAG",
	"VIDEORESIZE",
	)

#Classes
class Event_Listener(object):
	"""
	イベントを受け取るため待機するオブジェクト。
	イベントを受け取るためのインターフェイスを備える。
	"""
	def receive_event(self,event_type,event_obj):
		"""
		イベントを受け取るイベントリスナー共通インターフェイス
		要オーバーライド。
		"""
		raise Exception("オーバーライド必須です")
			

class Event_Processor(Event_Listener):
	"""
	イベントを処理する既定メソッドを定義するインターフェイス。
	Event_Distributerからイベントが分配、伝搬、されることが期待される。
	"""
	event_names = None	#大文字イベント名のタプル

	def handlable(self,event_type):
		"""
		定義されたイベント名に対する、そのイベント処理メソッドprocess_EVENTTYPEをインターフェイスとして有しているか否か。
		"""
		method_name = generate_method_name(event_type)
		return hasattr(self,method_name) 

	def receive_event(self,event_type,event_obj):
		"""
		Event分配オブジェクトから伝搬:sendされたイベントを受け取る。
		内部でコンテキストとして渡されたイベントタイプに対応するprocess_イベント処理メソッドを呼び出す
		"""
		#Processメソッドの呼び出し。
		if self.handlable(event_type) :
			method_name = generate_method_name(event_type)
			processing_method = getattr(self,method_name)
			processing_method(event_obj)
		else :
			raise Exception("このイベント処理オブジェクトには、イベントタイプ %s に対する\
				イベント処理メソッド %s が定義されていません。" % (event_type,method_name))


class Event_Distributer(Event_Listener):
	"""
	イベントの監視、分配オブジェクト。
	イベントが発生したら、定義された対象オブジェクトにイベントを送出する。
	"""
	def __init__(self):
		self.default_target = None	#デフォルトのイベント伝搬対象オブジェクト

	def set_default_target(self,default_target):
		"""
		デフォルトイベント送出対象オブジェクトの定義
		"""
		#イベントに関するインターフェイスを有していれば
		self.check_target(default_target)
		self.default_target = default_target

	def get_default_target(self):
		"""
		デフォルトのイベント送出先オブジェクトを得るインターフェイス。未定義ならエラーを吐く。
		"""
		if self.default_target :
			return self.default_target
		else :
			raise Exception("デフォルトのイベント送出先が未定義です。")

	def check_target(self,target,event_type=None):
		"""
		イベント送出対象オブジェクトが、然るべきインターフェイスを有しているかチェック
		"""
		if not isinstance(target,Event_Listener) :
			raise TypeError("イベント送出対象オブジェクトが、イベントリスナー型でありません。")

	def send(self,event_type,event_obj,target=None):
		"""
		対象オブジェクトtargetにイベントを送出します。
		"""
		#イベント送出対象のチェック
		if target is None :
			target = self.get_default_target()
		else :
			self.check_target(target)
		#イベント名のチェック
		check_event_name(event_type)

		#イベントの受け渡し
		if isinstance(target,Event_Processor) :
			Event_Processor.receive_event(target,event_type,event_obj)
		if isinstance(target,Event_Distributer) :
			Event_Distributer.receive_event(target,event_type,event_obj)

	def receive_event(self,event_type,event_obj):
		"""
		sendによって送られたイベントを受け取る。
		バブリング処理を行う点で、Event_Processorのそれより拡張されている。
		"""
		#イベントの伝搬
		self.bubbling(event_type,event_obj)

	def bubbling(self,event_type,event_obj):
		"""
		イベントの伝搬を行う。
		伝搬先はself.get_next_target()の返り値である。
		オーバーライド禁止。
		"""
		next_target = self.get_next_target()
		if next_target :
			self.check_target(next_target)
			self.send(event_type,event_obj,next_target)

	def get_next_target(self):
		"""
		バブリング定義時、要オーバーライド。
		次のイベント送出先オブジェクトEvent_Listener、または、バブリングを行わない意味でNone(やFalseなどの偽)を返す。
		デフォルトではNoneを返し、つまりイベントの伝搬は行わない。
		"""
		return


# General Fucntion
def check_event_name(event_name):
	"""イベント名が十分妥当かを判定する。"""
	if not isinstance(event_name,str) :
		raise TypeError("イベント名は文字列でなければなりません")
	if not all( (len(event_name) >= 3 , event_name.isalpha() , event_name.isupper()) ) :
		raise Exception("イベント名は、３文字以上の特殊文字を含まない、大文字列でなければなりません。")


def generate_event_processor(event_names=DEFAULT_EVENT_NAMES) :
	"""
	引数event_namesの格納するイベント名に対するprocess_イベント名のメソッドをそのインターフェイスとして有するクラスオブジェクトを返す
	"""
	#Event_Processorの継承型を動的に生成する一時関数
	def create_event_processor():
		#新たなEvent_Processor継承クラスを定義して、イベント名に対する属性を付加。
		event_processor = type("event_processor",(Event_Processor,),{})	#新たなクラスオブジェクト
		event_processor.event_names = event_names

		dummy_func = ( lambda self,event_obj : None )	#pass文
		for event_name in event_names :
			check_event_name(event_name)
			method_name = generate_method_name(event_name)
			set_attr(event_processor,method_name,dummy_func)

		return event_processor

	#Do generate
	#event_namesが文字列を有するタプルなら
	if event_names and isinstance(event_names,tuple) and all(isinstance(name,str) for name in event_names) :
		return create_event_processor()
	else :
		raise TypeError("イベント名リストは、空でない文字列のタプルに限ります。")


def generate_method_name(event_name):
	"""イベント名に対する、そのイベント処理メソッドの名前を一意に返す。"""
	return "process_%s" % (event_name)


if __name__ == "__main__" :
	print "This is General Module offering Event Interfaces"



