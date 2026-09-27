extends SceneTree
func _initialize():
 var map = OpenXRActionMap.new()
 map.create_default_action_sets()
 ResourceSaver.save(map, "res://actions.tres")
 quit()
