#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import unittest
import sys
import socket
import os
import json
import threading
import time
import dredd_hooks as hooks
if sys.version_info[0] > 2:
    import io
else:
    import StringIO as io

hooks_thr = None


class Connection(object):

    def __init__(self):
        self.connection = socket.create_connection((hooks.HOST, hooks.PORT))
        self.rfile = self.connection.makefile('rb', -1)  # buffered input
        self.wfile = self.connection.makefile('wb', 0)  # unbuffered output

    def writeline(self, msg):
        msg = msg + hooks.MESSAGE_DELIMITER
        print("%d" % (sys.version_info[0]))
        if sys.version_info[0] > 2:
            self.wfile.write(msg.encode('utf-8'))
        else:
            self.wfile.write(msg)

    def readline(self):
        if sys.version_info[0] > 2:
            return self.rfile.readline().decode('utf-8').strip()
        else:
            return self.rfile.readline().strip()

    def close(self):
        self.rfile.close()
        self.wfile.close()
        self.connection.close()


class TestDreddHooks(unittest.TestCase):
    """
    Tests all the hooks defined.
    """
    @classmethod
    def setUpClass(cls):
        cls.output = io.StringIO()
        cls.saved_stdout = sys.stdout
        sys.stdout = cls.output
        cls.hooks_thr = threading.Thread(target=hooks.main,
                                         args=([os.path.abspath(__file__)],))
        cls.hooks_thr.start()
        time.sleep(1)
        cls.conn = Connection()

    @classmethod
    def tearDownClass(cls):
        cls.output.close()
        sys.stdout = cls.saved_stdout
        cls.conn.close()
        hooks.shutdown()
        cls.hooks_thr.join()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_before_all(self):
        self.conn.writeline(json.dumps({"event": "beforeAll", "data": [{}]}))
        msg = json.loads(self.conn.readline())
        expect = {"event": "beforeAll",
                  "data": [{
                      "hooks_modifications": ["before all mod"]}]}
        self.assertDictEqual(msg, expect)

    def test_after_all(self):
        self.conn.writeline(json.dumps({"event": "afterAll", "data": [{}]}))
        msg = json.loads(self.conn.readline())
        expect = {"event": "afterAll",
                  "data": [{
                      "hooks_modifications": ["after all mod"]}]}
        self.assertDictEqual(msg, expect)

    def test_before_validation(self):
        self.conn.writeline(json.dumps(
            {"event": "beforeEachValidation",
             "data": {
                 "name": "Machines > Machines collection > Get Machines"}}))
        msg = json.loads(self.conn.readline())
        expect = \
            {
                "event": "beforeEachValidation",
                "data":
                {
                    "name": "Machines > Machines collection > Get Machines",
                    "hooks_modifications":
                    [
                        "before each validation mod",
                        "before validation mod"
                    ]
                }
            }
        self.assertDictEqual(msg, expect)

    def test_before(self):
        self.conn.writeline(json.dumps(
            {"event": "beforeEach",
             "data": {
                 "name": "Machines > Machines collection > Get Machines"}}))
        msg = json.loads(self.conn.readline())
        expect = \
            {
                "event": "beforeEach",
                "data":
                {
                    "name": "Machines > Machines collection > Get Machines",
                    "hooks_modifications":
                    [
                        "before each mod",
                        "before mod"
                    ]
                }
            }
        self.assertDictEqual(msg, expect)

    def test_after(self):
        self.conn.writeline(json.dumps(
            {"event": "afterEach",
             "data": {
                 "name": "Machines > Machines collection > Get Machines"}}))
        msg = json.loads(self.conn.readline())
        expect = \
            {
                "event": "afterEach",
                "data":
                {
                    "name": "Machines > Machines collection > Get Machines",
                    "hooks_modifications":
                    [
                        "after mod",
                        "after each mod",
                    ],
                    "fail": "Yay! Failed!",
                }
            }
        self.assertDictEqual(msg, expect)

    def test_output(self):
        out = self.output.getvalue()
        for s in ['before all hook',
                  'before each hook',
                  'before each validation hook',
                  'before validation hook',
                  'after all hook',
                  'after each hook',
                  'after hook']:
            self.assertNotEqual(out.find(s), -1)


# *_all hooks
@hooks.before_all
def before_all_test(transactions):
    if 'hooks_modifications' not in transactions[0]:
        transactions[0]['hooks_modifications'] = []
    transactions[0]['hooks_modifications'].append("before all mod")
    print('before all hook')


@hooks.after_all
def after_all_test(transactions):
    if 'hooks_modifications' not in transactions[0]:
        transactions[0]['hooks_modifications'] = []
    transactions[0]['hooks_modifications'].append("after all mod")
    print('after all hook')


# *_each hooks
@hooks.before_each
def before_each_test(transaction):
    if 'hooks_modifications' not in transaction:
        transaction['hooks_modifications'] = []
    transaction['hooks_modifications'].append("before each mod")
    print('before each hook')


@hooks.before_each_validation
def before_each_validation_test(transaction):
    if 'hooks_modifications' not in transaction:
        transaction['hooks_modifications'] = []
    transaction['hooks_modifications'].append("before each validation mod")
    print('before each validation hook')


@hooks.after_each
def after_each_test(transaction):
    if 'hooks_modifications' not in transaction:
        transaction['hooks_modifications'] = []
    transaction['hooks_modifications'].append("after each mod")
    print('after each hook')


# *_each hooks
@hooks.before_validation('Machines > Machines collection > Get Machines')
def before_validation_test(transaction):
    if 'hooks_modifications' not in transaction:
        transaction['hooks_modifications'] = []
    transaction['hooks_modifications'].append("before validation mod")
    print('before validation hook')


@hooks.before("Machines > Machines collection > Get Machines")
def before_test(transaction):
    if 'hooks_modifications' not in transaction:
        transaction['hooks_modifications'] = []
    transaction['hooks_modifications'].append("before mod")
    print('before hook')


@hooks.after('Machines > Machines collection > Get Machines')
def after_test(transaction):
    if 'hooks_modifications' not in transaction:
        transaction['hooks_modifications'] = []
    transaction['hooks_modifications'].append("after mod")
    transaction['fail'] = 'Yay! Failed!'
    print('after hook')


if __name__ == '__main__':
    try:
        unittest.main()
    except Exception as e:
        exit(-1)
