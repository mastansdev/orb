import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bse import BSE

print("Creating BSE...")
bse = BSE(download_folder="./")

print("Calling announcements...")
response = bse.announcements(page_no=1)

print(type(response))
print(response)