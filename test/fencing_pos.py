str = '0c0m'
window_pos = (500, 400)
monitor_size = (1920, 1080)
sprite_size = (200, 200)
point_pos = [0,0]
# point_pos[1] = [0,0]
alignment = {
    'l': 0,  # horizontal
    'c': monitor_size[0] // 2,
    'r': monitor_size[0],
    't': 0,  # vertical
    'm': monitor_size[1] // 2,
    'b': monitor_size[1]}
spr_alignment = {
    'l': 0,  # horizontal
    'c': sprite_size[0] // 2,
    'r': sprite_size[0],
    't': 0,  # vertical
    'm': sprite_size[1] // 2,
    'b': sprite_size[1]}
for i in range(0, len(str), 2):  # INCOMPLETE
    print(str[i])
    if (str[i] == '1'):
        point_pos[i//2] = window_pos[i//2]
        point_pos[i//2] -= spr_alignment[str[i+1]]
    else:
        point_pos[i//2] = alignment[str[i+1]]
print(point_pos)
