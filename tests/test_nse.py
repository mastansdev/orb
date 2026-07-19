import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collectors.nse_corporate_collector import NSECorporateCollector

collector = NSECorporateCollector()

collector.connect()