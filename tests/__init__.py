from __future__ import absolute_import, print_function
from unittest import defaultTestLoader as loader, TestSuite

def suite():
    import tests.background_test
    import tests.hysteresis_test
    import tests.oneshot_test
    import tests.tcp_test

    ts = TestSuite()
    for module in [
            tests.background_test,
            tests.hysteresis_test,
            tests.oneshot_test,
            tests.tcp_test,
    ]:
        ts.addTest(loader.loadTestsFromModule(module))

    return ts
