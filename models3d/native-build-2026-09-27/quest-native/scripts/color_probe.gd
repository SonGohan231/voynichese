extends Node3D
const Math=preload("res://scripts/color_math.gd")
var app
var panel:MeshInstance3D
var body:StaticBody3D
var caption:Label3D
var swatches:Array=[]
var source:Dictionary={}
var pixels:Image
var samples:Array=[{},{}]
var target:=0
var patch:=1
var zoom:=1
var center:=Vector2(.5,.5)
var region:=Rect2i()
var worker:Thread
var busy:=false
var requested:Dictionary={}
var history:Array=[]
func setup(owner_app):
	app=owner_app;name="ProbnikRGB";visible=false
	panel=MeshInstance3D.new();var q:=QuadMesh.new();q.size=Vector2(1.7,1.15);panel.mesh=q;panel.position.y=.35;add_child(panel)
	body=StaticBody3D.new();body.collision_layer=0;body.collision_mask=0;body.set_meta("color_probe",true);panel.add_child(body)
	var c:=CollisionShape3D.new();var s:=BoxShape3D.new();s.size=Vector3(1.8,1.4,.025);c.shape=s;body.add_child(c)
	caption=app.label("",34);caption.width=710;caption.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;caption.pixel_size=.0027;caption.position=Vector3(0,-.60,.05);add_child(caption)
	var backing=app.box(self,Vector3(0,-.59,-.025),Vector3(2.03,1.01,.018),Color("142b36"));backing.material_override=app.material(Color("142b36"),true)
	for i in range(2):
		var sw=app.box(self,Vector3(-.66+i*1.32,1.04,0),Vector3(.34,.15,.012),Color.WHITE);sw.material_override=app.material(Color.WHITE,true);swatches.append(sw)
	if FileAccess.file_exists("user://color_samples.json"):
		var data=JSON.parse_string(FileAccess.get_file_as_string("user://color_samples.json"))
		if data is Array:history=data
func toggle():
	visible=not visible;body.collision_layer=2 if visible else 0
	if visible:
		var d:Vector3=-app.camera.global_basis.z;d.y=0;d=d.normalized();global_position=app.camera.global_position+d*2.25+app.camera.global_basis.x*.68;look_at(Vector3(app.camera.global_position.x,global_position.y,app.camera.global_position.z),Vector3.UP,true)
		load_source(app.pages[app.page_cursor])
func load_source(meta:Dictionary):
	requested=meta
	if busy:return
	if source.get("id")==meta.id and pixels:refresh();return
	busy=true;caption.text="Wczytuję pełny skan f"+str(meta.label)+"…";body.collision_layer=0
	worker=Thread.new();worker.start(_decode.bind(meta))
func _decode(meta:Dictionary)->Dictionary:
	var bytes:=FileAccess.get_file_as_bytes("res://assets/source_pixels/"+str(meta.id)+".jpgbin")
	var hash:=HashingContext.new();hash.start(HashingContext.HASH_SHA256);hash.update(bytes);var sha:=hash.finish().hex_encode()
	if sha!=meta.sha256:return {"error":"Niezgodny skrót źródła"}
	var im:=Image.new();var error:=im.load_jpg_from_buffer(bytes)
	if error!=OK:return {"error":"Nie można odczytać skanu"}
	return {"meta":meta,"image":im}
func _process(_dt):
	if busy and worker and not worker.is_alive():
		var result=worker.wait_to_finish();worker=null;busy=false
		if result.has("error"):caption.text=result.error;return
		source=result.meta;pixels=result.image;zoom=1;center=Vector2(.5,.5)
		if requested.id!=source.id:load_source(requested);return
		refresh();body.collision_layer=2 if visible else 0
func _exit_tree():
	if worker:worker.wait_to_finish()
func refresh():
	if not pixels:return
	var w:=maxi(1,pixels.get_width()/zoom);var h:=maxi(1,pixels.get_height()/zoom)
	region=Rect2i(clampi(roundi(center.x*pixels.get_width())-w/2,0,pixels.get_width()-w),clampi(roundi(center.y*pixels.get_height())-h/2,0,pixels.get_height()-h),w,h)
	var view:=pixels.get_region(region);var maxsize:=1536
	if maxi(w,h)>maxsize:view.resize(roundi(float(w)*maxsize/maxi(w,h)),roundi(float(h)*maxsize/maxi(w,h)),Image.INTERPOLATE_LANCZOS)
	var m=app.material(Color.WHITE,true);m.albedo_texture=ImageTexture.create_from_image(view);m.texture_filter=BaseMaterial3D.TEXTURE_FILTER_NEAREST;panel.material_override=m
	var aspect:=float(w)/h;panel.mesh.size=Vector2(minf(1.7,1.15*aspect),minf(1.15,1.7/aspect));body.get_child(0).shape.size=Vector3(panel.mesh.size.x,panel.mesh.size.y,.025)
	update_text()
func sample_at(world:Vector3):
	if busy or not pixels:return
	var p:=panel.to_local(world);var size:Vector2=panel.mesh.size
	var uv:=Vector2(p.x/size.x+.5,.5-p.y/size.y)
	if uv.x<0 or uv.y<0 or uv.x>1 or uv.y>1:return
	var x:=clampi(region.position.x+floori(uv.x*region.size.x),0,pixels.get_width()-1);var y:=clampi(region.position.y+floori(uv.y*region.size.y),0,pixels.get_height()-1)
	set_sample(x,y)
func set_sample(x:int,y:int):
	if not pixels:return
	x=clampi(x,0,pixels.get_width()-1);y=clampi(y,0,pixels.get_height()-1)
	var sum:=Vector3.ZERO;var count:=0
	for yy in range(maxi(0,y-patch/2),mini(pixels.get_height(),y+patch/2+1)):
		for xx in range(maxi(0,x-patch/2),mini(pixels.get_width(),x+patch/2+1)):
			var c:=pixels.get_pixel(xx,yy);sum+=Vector3(c.r,c.g,c.b);count+=1
	var c:=Color(sum.x/count,sum.y/count,sum.z/count)
	samples[target]={"folio":source.label,"scan":source.id,"sha256":source.sha256,"x":x,"y":y,"patch":patch,"pixels_averaged":count,"rgb8":[roundi(c.r*255),roundi(c.g*255),roundi(c.b*255)],"rgb_mean":[c.r*255,c.g*255,c.b*255],"hex":"#"+c.to_html(false),"lab":Math.rgb_lab(c),"space":"Embedded sRGB profile; D65; decoded JPEG values","timestamp":Time.get_datetime_string_from_system(true)}
	swatches[target].material_override.albedo_color=c;center=Vector2((x+.5)/pixels.get_width(),(y+.5)/pixels.get_height());update_text()
func update_text():
	if not pixels:return
	var out:="Próbka %s · %d × %d px · zoom ×%d\n"%["A" if target==0 else "B",patch,patch,zoom]
	for i in range(2):
		if not samples[i].is_empty():
			var v:Dictionary=samples[i];out+="%s: %s  RGB %s\nf%s · x%d y%d\n"%["A" if i==0 else "B",v.hex,str(v.rgb8),str(v.folio).left(25),v.x,v.y]
	if not samples[0].is_empty() and not samples[1].is_empty():out+="ΔE00 = %.4f\n"%Math.delta_e(samples[0].lab,samples[1].lab)
	caption.text=out+"Kolor skanu sRGB; nie pomiar pigmentu."
func change_zoom(factor:int):
	if busy or not pixels:return
	zoom=clampi(zoom*factor if factor>0 else zoom/abs(factor),1,64);refresh()
func switch_target():target=1-target;update_text()
func change_patch():patch=3 if patch==1 else (11 if patch==3 else 1);update_text()
func save_comparison():
	if samples[0].is_empty() or samples[1].is_empty():app.say("Pobierz próbkę A i B");return
	var data={"A":samples[0].duplicate(true),"B":samples[1].duplicate(true),"delta_e00":Math.delta_e(samples[0].lab,samples[1].lab),"calibrated_pigments":false}
	history.append(data);var f:=FileAccess.open("user://color_samples.json.tmp",FileAccess.WRITE);f.store_string(JSON.stringify(history,"\t"));f.flush();f.close();DirAccess.rename_absolute("user://color_samples.json.tmp","user://color_samples.json");app.say("Zapisano porównanie kolorów wraz ze stronami i współrzędnymi")
func menu_actions()->Array:
	return [["Pokaż / schowaj",toggle],["Próbka A / B",switch_target],["Powiększ ×4",func():change_zoom(4)],["Oddal ÷4",func():change_zoom(-4)],["1 / 3 / 11 px",change_patch],["Cała strona",func():zoom=1;center=Vector2(.5,.5);refresh()],["◀ Strona",func():app._choose_page(-1);load_source(app.pages[app.page_cursor])],["Strona ▶",func():app._choose_page(1);load_source(app.pages[app.page_cursor])],["Zapisz kolory",save_comparison],["Wróć do modelu",func():visible=false;body.collision_layer=0;app.mode="Katalog";app._refresh_menu()]]
