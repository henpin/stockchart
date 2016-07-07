#! /usr/bin/python
#-*- coding: utf-8 -*-

import os.path
import sys

"""
このスクリプトはモジュール検索パスの設定を行います。
"""
testdir = os.path.split(os.path.abspath(__file__))[0]
parent_dir = os.path.split(testdir)[0]
sys.path.insert(0,parent_dir)
