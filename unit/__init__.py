import sys

import amino.test
from amino import Path

amino.test.setup(__file__)
sys.path[:0] = [str(Path(__file__).parent / '_fixtures')]
