extends SceneTree
func _initialize():
	var m=load("res://scripts/color_math.gd");var pairs=JSON.parse_string(FileAccess.get_file_as_string("res://tests/ciede2000.json"));var worst:=0.0
	for p in pairs:
		var actual:float=m.delta_e(p.a,p.b);worst=maxf(worst,absf(actual-p.expected));assert(absf(actual-p.expected)<.000051,str(p)+" got "+str(actual))
	print("CIEDE2000_PASS ",pairs.size()," worst ",worst)
	for f in ["color_probe","compound","workroom"]:assert(load("res://scripts/"+f+".gd").can_instantiate(),f)
	quit()
