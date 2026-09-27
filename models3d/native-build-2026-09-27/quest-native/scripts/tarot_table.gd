extends Node3D
## Physical 78-card deck. Read order is the explicit left-to-right slot order.
const CENTRE := Vector3(3.0, 0.90, -1.70)
var app
var cards: Array = []
var by_id: Dictionary = {}
var categories := ["Wszystkie", "Wielkie Arkana", "Buław", "Kielichów", "Mieczy", "Denarów"]
var category := 0
var cursor := 0
var filtered: Array = []
var deck: Array = []
var drawn: Dictionary = {}
var count := 3
var slots: Array = [null, null, null]
var frames: Node3D
var reading: Label3D
var reading_page := 0
var reading_pages: Array = []
var selected_card: Node3D
var rng := RandomNumberGenerator.new()

func setup(owner_app):
	app = owner_app; name = "Tarot"
	cards = JSON.parse_string(FileAccess.get_file_as_string("res://assets/tarot/cards.json"))
	for card in cards: by_id[card.id] = card
	filtered = cards.duplicate()
	for c in cards: deck.append(c.id)
	rng.randomize(); _shuffle_remaining()
	frames = Node3D.new(); add_child(frames)
	reading = app.label("Tarot · interpretacja symboliczna\nUłóż karty na polach 1–3.\nChwyt: przenieś · A/X: odwróć 180°", 27)
	app.box(self, Vector3(3,1.87,-2.59), Vector3(2.25,1.32,.045), Color("142c29"))
	reading.position = Vector3(3, 2.46, -2.55); reading.pixel_size = 0.0028
	reading.font_size = 32; reading.outline_size = 3
	reading.width = 740; reading.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	reading.vertical_alignment = VERTICAL_ALIGNMENT_TOP; add_child(reading)
	_build_slots()

func _build_slots():
	for child in frames.get_children(): frames.remove_child(child); child.queue_free()
	for i in range(count):
		var p := slot_position(i)
		var b = app.box(frames, p - Vector3(0,0.009,0), Vector3(.205,.007,.32), Color("38574f"))
		b.name = "Pole_%d" % (i+1)
		var l = app.label(str(i+1), 26); l.position = p+Vector3(0,.015,.23); l.rotation.x = -PI/2; frames.add_child(l)

func slot_position(i: int) -> Vector3:
	return CENTRE + Vector3((i-(count-1)*.5)*.38,.012,0)

func _shuffle_remaining():
	for i in range(deck.size()-1,0,-1):
		var j := rng.randi_range(0,i); var swap = deck[i]; deck[i]=deck[j]; deck[j]=swap

func menu_actions() -> Array:
	return [["Podejdź do tarota", goto_table], ["Losuj kartę", draw_next], ["◀ Karta", func(): choose(-1)], ["Karta ▶", func(): choose(1)], ["Kolor / Arkana", cycle_category], ["Dodaj wybraną", draw_chosen], ["Pola: %d" % count, change_layout], ["Odwróć 180°", reverse_selected], ["Interpretuj układ", interpret], ["Tekst ▶", next_reading], ["Tasuj pozostałe", shuffle], ["Zbierz karty", clear_cards]]

func goto_table():
	await app.switch_room(0)
	app.origin.position = Vector3(3,0,.0); app.origin.rotation.y = 0
	app.mode = "Tarot"; app.place_menu(); app._refresh_menu()

func choose(delta: int):
	cursor = posmod(cursor+delta,filtered.size())
	app.say(filtered[cursor].name + " · " + filtered[cursor].category)

func cycle_category():
	category = (category+1)%categories.size()
	filtered = cards.filter(func(c):return category==0 or c.category==categories[category]); cursor=0; choose(0)

func draw_next():
	if deck.is_empty(): app.say("Talia jest na stole. Zbierz karty, aby zacząć ponownie."); return
	_draw(deck.back())

func draw_chosen():
	_draw(filtered[cursor].id)

func _draw(id: String):
	if drawn.has(id): selected_card = drawn[id]; app.selected = selected_card; app.say("Ta karta jest już na stole"); return
	if drawn.size() >= 12: app.say("Na stole mieści się 12 kart. Zbierz układ przed nowym rozdaniem."); return
	app.checkpoint(); var card := spawn_card(id)
	if not card: return
	var slot := slots.find(null)
	if slot >= 0: _place(card,slot,false)
	else: card.position = CENTRE+Vector3(-.85+float(drawn.size()%6)*.28,.02,.47)
	selected_card=card; app.selected=card; invalidate()
	if complete():interpret()
	app.save_workspace(); app.say(by_id[id].name + " · możesz przenieść na dowolne pole")

func spawn_card(id: String) -> Node3D:
	if not by_id.has(id) or drawn.has(id): return null
	var path: String = by_id[id].model
	if not ResourceLoader.exists(path): return null
	var card := Node3D.new(); card.name="Karta_"+id; card.set_meta("tarot_card",id); card.set_meta("slot",-1); card.set_meta("reversed",false); add_child(card)
	var model = load(path).instantiate(); card.add_child(model)
	var body := StaticBody3D.new(); body.collision_layer=1; body.collision_mask=0; body.set_meta("tarot",card); card.add_child(body)
	var collision := CollisionShape3D.new(); var shape := BoxShape3D.new(); shape.size=Vector3(.165,.018,.28); collision.shape=shape; body.add_child(collision)
	drawn[id]=card; deck.erase(id); return card

func _place(card: Node3D, index: int, reversed: bool):
	_remove_from_slots(card)
	card.position=slot_position(index); card.rotation=Vector3(0,PI if reversed else 0,0); card.scale=Vector3.ONE
	card.set_meta("slot",index); card.set_meta("reversed",reversed); slots[index]=card

func _remove_from_slots(card: Node3D):
	for i in range(slots.size()):
		if slots[i]==card: slots[i]=null
	card.set_meta("slot",-1)

func begin_grab(card: Node3D):
	selected_card=card; _remove_from_slots(card); invalidate()

func finish_grab(card: Node3D):
	selected_card=card
	var index := -1; var nearest := .23
	for i in range(count):
		var d: float = card.global_position.distance_to(slot_position(i))
		if d<nearest: nearest=d;index=i
	var reversed: bool = card.global_basis.z.dot(Vector3.BACK)<0
	if index>=0:
		var other=slots[index]
		if is_instance_valid(other) and other!=card:
			_remove_from_slots(other); other.position=CENTRE+Vector3(.75,.025,.47)
		_place(card,index,reversed)
	else: card.set_meta("slot",-1)
	invalidate()
	if complete(): interpret()

func reverse_selected():
	if not is_instance_valid(selected_card): app.say("Najpierw wybierz kartę"); return
	app.checkpoint(); selected_card.rotate_y(PI)
	selected_card.set_meta("reversed",not selected_card.get_meta("reversed",false)); invalidate()
	if complete(): interpret()
	app.save_workspace()

func complete() -> bool:
	for c in slots:
		if not is_instance_valid(c):return false
	return true

func ordered_ids() -> Array:
	var order: Array=[]
	for c in slots: order.append(c.get_meta("tarot_card") if is_instance_valid(c) else null)
	return order

func interpret(persist := true):
	reading_pages=[];reading_page=0
	if not complete():
		reading.text="Układ jest niepełny.\nUzupełnij pola 1–%d.\nKarty poza polami pozostają poza odczytem."%count
		app.say("Brakuje karty w układzie");return
	var positions := ["Punkt wyjścia", "Napięcie / przeszkoda", "Kierunek do rozważenia"] if count==3 else ["Punkt wyjścia","Co wspiera","Co utrudnia","Inna perspektywa","Następny krok do rozważenia"]
	var chain: Array=[]
	for i in range(count):
		var card: Node3D=slots[i];var d: Dictionary=by_id[card.get_meta("tarot_card")];var rev: bool=card.get_meta("reversed",false)
		var meaning: String=d.reversed if rev else d.upright
		chain.append(d.theme)
		reading_pages.append("%d. %s\n%s%s\n\n%s"%[i+1,positions[i],d.name," · odwrócona" if rev else "",meaning])
	var summary := "Kolejność Twojego układu\n"+" → ".join(chain)+"\n\nZobacz, jak „%s” prowadzi przez „%s” do „%s”. Co w tym przejściu jest dla Ciebie ważne?"%[chain[0],chain[1],chain[-1]]
	reading_pages.append(summary);_show_reading()
	if persist:app.save_workspace()

func _show_reading():
	if reading_pages.is_empty(): return
	reading.text="INTERPRETACJA SYMBOLICZNA · %d/%d\n\n%s"%[reading_page+1,reading_pages.size(),reading_pages[reading_page]]

func next_reading():
	if reading_pages.is_empty(): interpret(); return
	reading_page=(reading_page+1)%reading_pages.size();_show_reading()

func invalidate():
	reading_pages=[];reading_page=0
	reading.text="Układaj po swojemu · pola 1–%d\nKolejność: od lewej do prawej.\nInterpretacja uwzględni obrót o 180°."%count

func change_layout():
	app._release_all();app.checkpoint();count=5 if count==3 else 3;slots=[];slots.resize(count)
	var i:=0
	for id in drawn:
		var card: Node3D=drawn[id];card.set_meta("slot",-1)
		if i<count:_place(card,i,card.get_meta("reversed",false))
		else:card.position=CENTRE+Vector3(-.8+float((i-count)%6)*.28,.025,.48)
		i+=1
	_build_slots();invalidate();app._refresh_menu();app.save_workspace()

func shuffle():
	app.checkpoint();_shuffle_remaining();app.say("Pozostała talia przetasowana");app.save_workspace()

func clear_cards():
	app._release_all();app.checkpoint();_clear();_shuffle_remaining();invalidate();app.save_workspace()

func _clear():
	selected_card=null
	if is_instance_valid(app.selected) and app.selected.has_meta("tarot_card"):app.selected=null
	for card in drawn.values():
		if is_instance_valid(card):card.get_parent().remove_child(card);card.queue_free()
	drawn={};deck=[]
	for c in cards:deck.append(c.id)
	slots=[];slots.resize(count)

func data() -> Dictionary:
	var result: Array=[]
	for id in drawn:
		var card: Node3D=drawn[id]
		result.append({"id":id,"transform":app._encode_transform(card.global_transform),"slot":card.get_meta("slot",-1),"reversed":card.get_meta("reversed",false)})
	return {"count":count,"cards":result,"deck":deck.duplicate(),"reading_page":reading_page}

func restore(d: Dictionary):
	_clear();count=5 if d.get("count",3)==5 else 3;slots=[];slots.resize(count)
	for item in d.get("cards",[]).slice(0,12):
		var id: String=item.get("id","");var card:=spawn_card(id)
		if not card:continue
		card.global_transform=app._decode_transform(item.get("transform",[]));card.set_meta("reversed",bool(item.get("reversed",false)))
		var index: int=int(item.get("slot",-1))
		if index>=0 and index<count and slots[index]==null:card.set_meta("slot",index);slots[index]=card
	var saved: Array=d.get("deck",[])
	var allowed: Array=deck.duplicate();deck=[]
	for id in saved:
		if allowed.has(id) and not deck.has(id):deck.append(id)
	for id in allowed:
		if not deck.has(id):deck.append(id)
	_build_slots();invalidate()
	if complete():
		interpret(false);reading_page=clampi(int(d.get("reading_page",0)),0,reading_pages.size()-1);_show_reading()
