import blendersynth as bsyn
bsyn.run_this_script(debug=False)

monkey = bsyn.Mesh.from_primitive('monkey')
# monkey.origin_to_centroid(method='bounds')
# monkey.origin_to_centroid(method='median')
# monkey.origin_to_centroid(method='com_volume')
# monkey.origin_to_centroid(method='com_area')

# monkey.location = (10, 0, 0)
#
print(monkey.centroid('bounds'))
print(monkey.centroid('median'))
print(monkey.origin)