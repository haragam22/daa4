"""Gate entry point: emit a distinct marker only after the suite passes."""
import sys
import unittest

suite = unittest.defaultTestLoader.discover("tests")
result = unittest.TextTestRunner(verbosity=2).run(suite)
if not result.wasSuccessful():
    sys.exit(1)
print("ALGORITHMS AND CLI VERIFIED")
