from bse import BSE

print("Creating BSE...")
bse = BSE(download_folder="./")

print("Calling announcements...")
response = bse.announcements(page_no=1)

print(type(response))
print(response)