with open("backend/app/services/ass_maker.py", "r") as f:
    content = f.read()

# Original style line ends with ...40,40,1100,1
content = content.replace(
    "10,4,8,40,40,1100,1",
    "10,4,8,100,100,1100,1"
)

with open("backend/app/services/ass_maker.py", "w") as f:
    f.write(content)
