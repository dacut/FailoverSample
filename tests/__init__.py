from __future__ import absolute_import, print_function
from unittest import defaultTestLoader as loader, TestSuite

def suite():
    import tests.hysteresis_test, tests.tcp_test
    ts = TestSuite()
    for module in [tests.hysteresis_test, tests.tcp_test]:
        ts.addTest(loader.loadTestsFromModule(module))

    return ts
