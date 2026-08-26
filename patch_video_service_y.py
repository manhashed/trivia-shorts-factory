with open("backend/app/services/video_service.py", "r") as f:
    content = f.read()

# Fix Question Text Y coordinate to dynamically center inside the box (y=480 to 940, center = 710)
old_q = "x=(w-text_w)/2:y=535:line_spacing=20"
new_q = "x=(w-text_w)/2:y=710-(text_h/2):line_spacing=20"
content = content.replace(old_q, new_q)

# Fix Answer Text Y coordinate. Box is y=970 to 1450 (center = 1210).
# The header is at 1010. We can center the body between 1080 and 1450. Center = 1265.
old_a = "x=(w-text_w)/2:y=1115:line_spacing=20"
new_a = "x=(w-text_w)/2:y=1265-(text_h/2):line_spacing=20"
content = content.replace(old_a, new_a)

with open("backend/app/services/video_service.py", "w") as f:
    f.write(content)
