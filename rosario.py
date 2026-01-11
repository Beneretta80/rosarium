import gi
import os
import glob
from datetime import datetime

# Verifica e richiedi la versione corretta di GTK
try:
    gi.require_version('Gtk', '4.0')
except ValueError:
    print("Errore: GTK 4.0 non trovato. Assicurati di aver installato le librerie necessarie.")
    print("Su Ubuntu: sudo apt install libgtk-4-dev python3-gi gir1.2-gtk-4.0")
    exit(1)

from gi.repository import Gtk, Gdk, GLib

# Tenta di importare i dati. Se fallisce, avvisa l'utente.
try:
    from rosario_data import TRADUZIONI, MISTERI_DATA, NODI_TEXTS, MISERICORDIA_TEXTS, ANGELICA_TEXTS, ANGELICA_IMMAGINI
except ImportError:
    print("Errore: File 'rosario_data.py' non trovato nella stessa cartella.")
    exit(1)

# --- CONFIGURAZIONE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "images")

# Funzione helper per trovare immagini in modo flessibile
def trova_immagine(pattern):
    if not os.path.exists(IMG_DIR):
        return None
    files = glob.glob(os.path.join(IMG_DIR, pattern))
    files.sort()
    return files[0] if files else None

# Caricamento percorsi immagini
# Icona dell'app (per riferimento interno)
ICONA_APP = os.path.join(IMG_DIR, "icona.svg")

# Immagini per i contenuti
MADONNA_POMPEI = trova_immagine("madonna_pompei.*")
CORONA_CLASSICO = trova_immagine("*corona*rosario*4*") or trova_immagine("*Corona*rosario*1*")
MADONNA_NODI = trova_immagine("*madonna*scioglie*nodi*") or trova_immagine("*madonna*nodi*")
CORONA_MISERICORDIA = trova_immagine("*corona*divina*misericordia*") or trova_immagine("*divina*misericordia*") or trova_immagine("*misericordia*")
CORONA_ANGELICA = trova_immagine("*corona*angelica*") or trova_immagine("*san*michele*") or CORONA_CLASSICO

class RosarioApp(Gtk.Application):
    def __init__(self):
        # L'ID 'rosarium' deve corrispondere al nome del file .desktop e alla StartupWMClass
        super().__init__(application_id="rosarium")
        # Impostiamo il nome del programma per il sistema operativo
        GLib.set_prgname("rosarium")
        
        self.pagina = "benvenuto"
        self.tipo_rosario = None
        self.grano = 0
        self.lingua_corrente = "IT"
        self.dots = []
        self.main_container = None
        self.immagine_mistero_widget = None

    def do_activate(self):
        self.win = Gtk.ApplicationWindow(application=self, title="Rosarium")
        self.win.set_default_size(900, 650)
        
        # In GTK4 l'icona della finestra è gestita dal file .desktop tramite l'application_id.
        # Avendo impostato application_id="rosarium" e StartupWMClass=rosarium nel file .desktop,
        # Ubuntu userà automaticamente l'icona definita lì (icona.svg).

        # CSS per lo stile
        css_data = b"""
        window { background: #faf0e6; font-family: Ubuntu, Sans, serif; }
        .dot-off { color: #d3d3d3; font-size: 20px; margin: 0 3px; }
        .dot-on { color: #ffcc00; font-size: 20px; margin: 0 3px; text-shadow: 0 0 5px orange; }
        .title { font-size: 24px; font-weight: bold; color: #8B4513; margin-top: 10px; margin-bottom: 10px; }
        .intro-title { font-size: 36px; font-weight: bold; color: #8B4513; margin: 20px; }
        .intro-subtitle { font-size: 20px; color: #5D2F00; margin: 10px; }
        .intro-text { font-size: 22px; color: #5D2F00; margin: 15px; }
        .prayer { font-size: 20px; color: #5D2F00; padding: 15px; line-height: 1.5; }
        .combo { font-size: 16px; margin-bottom: 5px; }
        .rosario-card { margin: 10px; padding: 15px; background: white; border-radius: 10px; transition: all 200ms; }
        .rosario-card:hover { background: #fff8dc; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
        """
        css = Gtk.CssProvider()
        css.load_from_data(css_data)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.aggiorna_ui()

        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self.on_key_press)
        self.win.add_controller(key_ctrl)

        self.win.set_child(self.main_container)
        self.win.present()

    # ========== CREAZIONE PAGINE ==========
    
    def crea_pagina_benvenuto(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_vexpand(True)
        main_box.set_margin_top(10)
        main_box.set_margin_start(15)
        main_box.set_margin_end(15)
        
        lingue_keys = list(TRADUZIONI.keys())
        lingue_nomi = [TRADUZIONI[k]["nome"] for k in lingue_keys]
        dropdown = Gtk.DropDown.new_from_strings(lingue_nomi)
        dropdown.set_halign(Gtk.Align.END)
        dropdown.add_css_class("combo")
        dropdown.set_selected(lingue_keys.index(self.lingua_corrente))
        dropdown.connect("notify::selected", self.cambia_lingua, lingue_keys)
        main_box.append(dropdown)
        
        center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        center_box.set_halign(Gtk.Align.CENTER)
        center_box.set_valign(Gtk.Align.CENTER)
        center_box.set_vexpand(True)
        
        title_text = "Benvenuti nell'App Rosarium" if self.lingua_corrente == "IT" else "Salve in Applicatione Rosarium"
        title_lbl = Gtk.Label(label=title_text)
        title_lbl.add_css_class("intro-title")
        center_box.append(title_lbl)
        
        # Qui usiamo la Madonna di Pompei come immagine di benvenuto (contenuto), non come icona
        if MADONNA_POMPEI and os.path.exists(MADONNA_POMPEI):
            img = Gtk.Picture.new_for_filename(MADONNA_POMPEI)
            img.set_content_fit(Gtk.ContentFit.CONTAIN)
            img.set_size_request(300, 350)
            center_box.append(img)
        
        subtitle_text = "\n(Clicca o premi Spazio per continuare)" if self.lingua_corrente == "IT" else "\n(Clicca vel preme Spatium)"
        subtitle_lbl = Gtk.Label(label=subtitle_text)
        subtitle_lbl.add_css_class("intro-subtitle")
        subtitle_lbl.set_opacity(0.7)
        center_box.append(subtitle_lbl)
        
        gesture = Gtk.GestureClick()
        gesture.connect("pressed", lambda *_: self.vai_a_selezione())
        center_box.add_controller(gesture)
        
        main_box.append(center_box)
        return main_box

    def crea_pagina_selezione(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_top(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        
        title_text = "Scegli il tipo di preghiera" if self.lingua_corrente == "IT" else "Elige genus orationis"
        title_lbl = Gtk.Label(label=title_text)
        title_lbl.add_css_class("intro-title")
        main_box.append(title_lbl)
        
        grid = Gtk.Grid()
        grid.set_row_spacing(20)
        grid.set_column_spacing(20)
        grid.set_halign(Gtk.Align.CENTER)
        grid.set_valign(Gtk.Align.CENTER)
        grid.set_vexpand(True)
        
        rosari = [
            ("classico", CORONA_CLASSICO, "Rosario Classico", "Rosarium Classicum"),
            ("nodi", MADONNA_NODI, "Maria che scioglie i nodi", "Maria quae nodos solvit"),
            ("misericordia", CORONA_MISERICORDIA, "Coroncina Divina Misericordia", "Corolla Divinae Misericordiae"),
            ("angelica", CORONA_ANGELICA, "Corona Angelica (San Michele)", "Corona Angelica")
        ]
        
        for idx, (tipo, img_path, nome_it, nome_la) in enumerate(rosari):
            row = idx // 2
            col = idx % 2
            
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            card.add_css_class("rosario-card")
            card.set_size_request(380, 300)
            
            if img_path and os.path.exists(img_path):
                img = Gtk.Picture.new_for_filename(img_path)
                img.set_content_fit(Gtk.ContentFit.CONTAIN)
                img.set_size_request(320, 200)
                card.append(img)
            
            nome = nome_it if self.lingua_corrente == "IT" else nome_la
            lbl = Gtk.Label(label=nome)
            lbl.set_wrap(True)
            lbl.set_justify(Gtk.Justification.CENTER)
            lbl.add_css_class("intro-text")
            card.append(lbl)
            
            gesture = Gtk.GestureClick()
            gesture.connect("pressed", lambda g, n, x, y, t=tipo: self.seleziona_rosario(t))
            card.add_controller(gesture)
            
            grid.attach(card, col, row, 1, 1)
        
        main_box.append(grid)
        return main_box

    def crea_intro_classico(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_top(10)
        main_box.set_margin_start(15)
        main_box.set_margin_end(15)
        
        btn_back = Gtk.Button(label="← Indietro")
        btn_back.set_halign(Gtk.Align.START)
        btn_back.connect("clicked", lambda *_: self.indietro())
        main_box.append(btn_back)
        
        h_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        h_box.set_vexpand(True)
        h_box.set_halign(Gtk.Align.CENTER)
        h_box.set_valign(Gtk.Align.CENTER)
        
        if CORONA_CLASSICO and os.path.exists(CORONA_CLASSICO):
            img = Gtk.Picture.new_for_filename(CORONA_CLASSICO)
            img.set_content_fit(Gtk.ContentFit.CONTAIN)
            img.set_size_request(350, 400)
            h_box.append(img)
        
        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        text_box.set_valign(Gtk.Align.CENTER)
        
        T = TRADUZIONI[self.lingua_corrente]
        oggi_idx = datetime.now().weekday()
        idx_mistero = {0:0, 1:1, 2:2, 3:3, 4:1, 5:0, 6:2}[oggi_idx]
        
        giorno_text = T["giorni"][oggi_idx]
        mistero_text = T["misteri"][idx_mistero]
        
        if self.lingua_corrente == "IT":
            info_text = f"Oggi è {giorno_text}\n\ne si recitano i\n\n{mistero_text}"
            btn_text = "Inizia il Rosario →"
        else:
            info_text = f"Hodie est {giorno_text}\n\net recitamus\n\n{mistero_text}"
            btn_text = "Incipe Rosarium →"
        
        info_lbl = Gtk.Label(label=info_text)
        info_lbl.add_css_class("intro-text")
        info_lbl.set_justify(Gtk.Justification.CENTER)
        text_box.append(info_lbl)
        
        btn_start = Gtk.Button(label=btn_text)
        btn_start.connect("clicked", lambda *_: self.avanza())
        text_box.append(btn_start)
        
        h_box.append(text_box)
        main_box.append(h_box)
        
        return main_box

    def crea_pagina_rosario(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # 1. TOP BAR
        top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        top_bar.set_margin_top(10)
        top_bar.set_margin_start(15)
        top_bar.set_margin_end(15)
        
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        btn_indietro = Gtk.Button(label="◀")
        btn_indietro.connect("clicked", lambda *_: self.indietro())
        nav_box.append(btn_indietro)
        btn_home = Gtk.Button(label="🏠")
        btn_home.connect("clicked", lambda *_: self.vai_inizio())
        nav_box.append(btn_home)
        top_bar.append(nav_box)
        
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        top_bar.append(spacer)
        
        lingue_keys = list(TRADUZIONI.keys())
        lingue_nomi = [TRADUZIONI[k]["nome"] for k in lingue_keys]
        dropdown = Gtk.DropDown.new_from_strings(lingue_nomi)
        dropdown.set_halign(Gtk.Align.END)
        dropdown.add_css_class("combo")
        dropdown.set_selected(lingue_keys.index(self.lingua_corrente))
        dropdown.connect("notify::selected", self.cambia_lingua, lingue_keys)
        top_bar.append(dropdown)
        main_box.append(top_bar)
        
        # 2. CONTENT AREA
        content_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content_area.set_vexpand(True)
        content_area.set_margin_start(15)
        content_area.set_margin_end(15)
        content_area.set_margin_bottom(10)
        
        main_gesture = Gtk.GestureClick()
        main_gesture.connect("pressed", lambda *_: self.avanza())
        content_area.add_controller(main_gesture)
        
        self.lbl_titolo = Gtk.Label()
        self.lbl_titolo.add_css_class("title")
        content_area.append(self.lbl_titolo)
        
        horizontal_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        horizontal_box.set_vexpand(True)
        
        # COLONNA SINISTRA
        left_column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        img_show = None
        if self.tipo_rosario == "classico":
            img_show = CORONA_CLASSICO
        elif self.tipo_rosario == "nodi":
            img_show = MADONNA_NODI if MADONNA_NODI else CORONA_CLASSICO
        elif self.tipo_rosario == "misericordia":
            img_show = CORONA_MISERICORDIA if CORONA_MISERICORDIA else CORONA_CLASSICO
        elif self.tipo_rosario == "angelica":
            if self.grano == 0:
                img_show = CORONA_ANGELICA
            else:
                img_show = None 

        if img_show and os.path.exists(img_show):
            self.immagine_mistero_widget = Gtk.Picture.new_for_filename(img_show)
            self.immagine_mistero_widget.set_content_fit(Gtk.ContentFit.CONTAIN)
            self.immagine_mistero_widget.set_size_request(350, 400)
            left_column.append(self.immagine_mistero_widget)
        elif self.tipo_rosario == "angelica" and hasattr(self, 'immagine_mistero_widget') and self.immagine_mistero_widget:
            left_column.append(self.immagine_mistero_widget)
        
        box_dots = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, halign=Gtk.Align.CENTER)
        self.dots = []
        for _ in range(10):
            lbl = Gtk.Label(label="●")
            lbl.add_css_class("dot-off")
            self.dots.append(lbl)
            box_dots.append(lbl)
        left_column.append(box_dots)
        horizontal_box.append(left_column)
        
        # COLONNA DESTRA
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_hexpand(True)
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.label = Gtk.Label(wrap=True, justify=Gtk.Justification.CENTER)
        self.label.add_css_class("prayer")
        self.label.set_margin_start(10)
        self.label.set_margin_end(10)
        scrolled_window.set_child(self.label)
        horizontal_box.append(scrolled_window)
        
        content_area.append(horizontal_box)
        main_box.append(content_area)
        
        if self.tipo_rosario == "classico":
            self.aggiorna_contenuto_classico()
        elif self.tipo_rosario == "nodi":
            self.aggiorna_contenuto_nodi()
        elif self.tipo_rosario == "misericordia":
            self.aggiorna_contenuto_misericordia()
        elif self.tipo_rosario == "angelica":
            self.aggiorna_contenuto_angelica()
        else:
            self.label.set_text("In sviluppo...")
            
        return main_box

    def aggiorna_contenuto_classico(self):
        g = self.grano
        T = TRADUZIONI[self.lingua_corrente]
        text = ""
        ave_count = 0
        
        oggi_idx = datetime.now().weekday()
        # Mappatura corretta in base alla lista in rosario_data.py
        map_giorno_to_idx_lista = {
            0: 0, # Lun -> Gioia
            1: 2, # Mar -> Dolore
            2: 3, # Mer -> Gloria
            3: 1, # Gio -> Luce
            4: 2, # Ven -> Dolore
            5: 0, # Sab -> Gioia
            6: 3  # Dom -> Gloria
        }
        
        idx_lista = map_giorno_to_idx_lista[oggi_idx]
        dati_misteri_correnti = MISTERI_DATA[idx_lista]
        
        nome_misteri = dati_misteri_correnti["nome_it" if self.lingua_corrente == "IT" else "nome_la"]
        self.lbl_titolo.set_text(nome_misteri)
        
        if g == 0: text = T["segno"]
        elif g == 1: text = T["odio"]
        elif g == 2: text = T["gloria"]
        elif g == 3: text = T["credo"]
        elif g == 4: text = T["pater"]
        elif g == 5: text = f"{T['ave']}\n\n{T['ave_fede']}"
        elif g == 6: text = f"{T['ave']}\n\n{T['ave_speranza']}"
        elif g == 7: text = f"{T['ave']}\n\n{T['ave_carita']}"
        elif g == 8: text = T["gloria"]
        elif 9 <= g <= 83:
            step_decina = (g - 9) % 15
            num_mistero = ((g - 9) // 15) + 1
            
            if step_decina == 14:
                self.grano += 1
                self.aggiorna_contenuto_classico()
                return

            mistero_singolo = dati_misteri_correnti["misteri"][num_mistero - 1]
            immagine_corrente = os.path.join(IMG_DIR, mistero_singolo["immagine"])
            self.aggiorna_immagine_mistero(immagine_corrente)
            
            titolo_key = "titolo_it" if self.lingua_corrente == "IT" else "titolo_la"
            
            if step_decina == 0:
                vangelo_key = "vangelo_it" if self.lingua_corrente == "IT" else "vangelo_la"
                testo_vangelo = mistero_singolo.get(vangelo_key, "")
                text = f"{mistero_singolo[titolo_key]}\n\n{testo_vangelo}\n\n{T['pater']}"
            elif 1 <= step_decina <= 10:
                text = f"{T['ave']}\n\n({step_decina}/10)"
                ave_count = step_decina
            elif step_decina == 11:
                text = T["gloria"]
                ave_count = 10
            elif step_decina == 12: text = T["fatima"]
            elif step_decina == 13: text = T["regina_pace"]
            
        elif g == 84: text = T["salve"]
        elif g == 85: text = T["litanie"]
        elif g == 86: text = T["sotto_litanie"]
        elif g == 87: text = T["finale"]
        elif g == 88: text = T["michele"]
        elif g == 89: text = f"{T['riposo']} (1/3)"
        elif g == 90: text = f"{T['riposo']} (2/3)"
        elif g == 91: text = f"{T['riposo']} (3/3)"
        elif g == 92: text = T["segno"]
        elif g == 93: text = "Rosario completato!"
        
        self.label.set_text(text)
        self.aggiorna_dots(ave_count, 10)

    def aggiorna_contenuto_nodi(self):
        g = self.grano
        T = TRADUZIONI[self.lingua_corrente]
        text = ""
        ave_count = 0
        
        oggi_idx = datetime.now().weekday()
        map_giorno_to_idx_lista = {
            0: 0, 1: 2, 2: 3, 3: 1, 4: 2, 5: 0, 6: 3
        }
        idx_lista = map_giorno_to_idx_lista[oggi_idx]
        dati_misteri_correnti = MISTERI_DATA[idx_lista]
        
        nome_misteri = dati_misteri_correnti["nome_it" if self.lingua_corrente == "IT" else "nome_la"]
        self.lbl_titolo.set_text("Maria che scioglie i nodi - " + nome_misteri)
        
        if g < 10 or g > 84:
            img_nodi = MADONNA_NODI if MADONNA_NODI else CORONA_CLASSICO
            self.aggiorna_immagine_mistero(img_nodi)

        if g == 0: text = T["segno"]
        elif g == 1: text = T["odio"]
        elif g == 2: text = T["gloria"]
        elif g == 3: text = NODI_TEXTS["intro"]
        elif g == 4: text = T["credo"]
        elif g == 5: text = T["pater"]
        elif g == 6: text = f"{T['ave']}\n\n{T['ave_fede']}"
        elif g == 7: text = f"{T['ave']}\n\n{T['ave_speranza']}"
        elif g == 8: text = f"{T['ave']}\n\n{T['ave_carita']}"
        elif g == 9: text = T["gloria"]
        elif 10 <= g <= 84:
            step_decina = (g - 10) % 15
            num_mistero = ((g - 10) // 15) + 1
            
            if step_decina == 14:
                self.grano += 1
                self.aggiorna_contenuto_nodi()
                return

            mistero_singolo = dati_misteri_correnti["misteri"][num_mistero - 1]
            immagine_corrente = os.path.join(IMG_DIR, mistero_singolo["immagine"])
            self.aggiorna_immagine_mistero(immagine_corrente)

            titolo_key = "titolo_it" if self.lingua_corrente == "IT" else "titolo_la"
            
            if step_decina == 0:
                vangelo_key = "vangelo_it" if self.lingua_corrente == "IT" else "vangelo_la"
                testo_vangelo = mistero_singolo.get(vangelo_key, "")
                text = f"{mistero_singolo[titolo_key]}\n\n{testo_vangelo}\n\n{T['pater']}"
            elif 1 <= step_decina <= 10:
                text = f"{T['ave']}\n\n({step_decina}/10)"
                ave_count = step_decina
            elif step_decina == 11:
                text = T["gloria"]
                ave_count = 10
            elif step_decina == 12: 
                text = NODI_TEXTS["giaculatoria"]
            elif step_decina == 13: 
                text = T["fatima"]
            
        elif g == 85: text = T["salve"]
        elif g == 86: text = NODI_TEXTS["finale"]
        elif g == 87: text = NODI_TEXTS["intenzioni"]
        elif g == 88: text = T["segno"]
        elif g == 89: text = "Preghiera completata!"

        self.label.set_text(text)
        self.aggiorna_dots(ave_count, 10)

    def aggiorna_contenuto_misericordia(self):
        g = self.grano
        T = TRADUZIONI[self.lingua_corrente]
        M = MISERICORDIA_TEXTS
        text = ""
        ave_count = 0
        
        self.lbl_titolo.set_text("Coroncina alla Divina Misericordia")
        
        if g == 0: text = T["segno"]
        elif g == 1: text = T["pater"]
        elif g == 2: text = T["ave"]
        elif g == 3: text = T["credo"]
        elif 4 <= g <= 58:
            pos = g - 4
            step = pos % 11 
            decina = (pos // 11) + 1
            if step == 0:
                text = f"Decina {decina}\n\n{M['eterno_padre']}"
                ave_count = 0
            else:
                text = f"{M['passione']}\n\n({step}/10)"
                ave_count = step
        elif g == 59: text = f"{M['santo_dio']} (1/3)"
        elif g == 60: text = f"{M['santo_dio']} (2/3)"
        elif g == 61: text = f"{M['santo_dio']} (3/3)"
        elif g == 62: text = M["conclusiva"]
        elif g == 63: text = T["segno"]
        elif g == 64: text = "Coroncina completata!"
        
        self.label.set_text(text)
        self.aggiorna_dots(ave_count, 10)

    def aggiorna_contenuto_angelica(self):
        g = self.grano
        T = TRADUZIONI[self.lingua_corrente]
        A = ANGELICA_TEXTS
        text = ""
        ave_count = 0
        
        self.lbl_titolo.set_text("Corona Angelica (San Michele)")
        
        if g == 0: 
            text = "O Dio, vieni a salvarmi.\nSignore, vieni presto in mio aiuto.\n\nGloria al Padre..."
            img_iniziale = CORONA_ANGELICA if CORONA_ANGELICA else CORONA_CLASSICO
            self.aggiorna_immagine_mistero(img_iniziale)
        
        elif 1 <= g <= 36:
            group_idx = (g - 1) // 4
            step_in_group = (g - 1) % 4
            
            if step_in_group == 0:
                if group_idx < len(ANGELICA_IMMAGINI):
                    img_coro = os.path.join(IMG_DIR, ANGELICA_IMMAGINI[group_idx])
                    self.aggiorna_immagine_mistero(img_coro)
                text = f"{A['salutazioni'][group_idx]}\n\n{T['pater']}"
                ave_count = 0
            else:
                text = f"{T['ave']}\n\n({step_in_group}/3)"
                ave_count = step_in_group
        
        elif 37 <= g <= 40:
            idx = g - 37
            text = f"{A['pater_finali'][idx]}\n\n{T['pater']}"
            ave_count = 0
            img_finale = CORONA_ANGELICA if CORONA_ANGELICA else CORONA_CLASSICO
            if idx == 0:
                self.aggiorna_immagine_mistero(img_finale)
        
        elif g == 41: text = A["preghiera"]
        elif g == 42: text = A["orazione"]
        elif g == 43: text = T["segno"]
        elif g == 44: text = "Corona Angelica completata!"
        
        self.label.set_text(text)
        self.aggiorna_dots(ave_count, 3)

    def aggiorna_immagine_mistero(self, percorso_immagine):
        if hasattr(self, 'immagine_mistero_widget') and self.immagine_mistero_widget:
            if percorso_immagine and os.path.exists(percorso_immagine):
                self.immagine_mistero_widget.set_filename(percorso_immagine)

    def aggiorna_dots(self, count, max_visible=10):
        for i, dot in enumerate(self.dots):
            if i < max_visible:
                dot.set_visible(True)
                dot.remove_css_class("dot-on")
                dot.remove_css_class("dot-off")
                dot.add_css_class("dot-on" if i < count else "dot-off")
            else:
                dot.set_visible(False)

    def vai_a_selezione(self):
        self.pagina = "selezione"
        self.aggiorna_ui()

    def seleziona_rosario(self, tipo):
        self.tipo_rosario = tipo
        if tipo == "classico":
            self.pagina = "intro_classico"
        else:
            self.pagina = "rosario"
            self.grano = 0
        self.aggiorna_ui()

    def avanza(self):
        if self.pagina == "intro_classico":
            self.pagina = "rosario"
            self.grano = 0
        elif self.pagina == "rosario":
            self.grano += 1
        self.aggiorna_ui()

    def indietro(self):
        if self.pagina == "rosario" and self.grano > 0:
            self.grano -= 1
        elif self.pagina == "rosario" and self.grano == 0:
            if self.tipo_rosario == "classico":
                self.pagina = "intro_classico"
            else:
                self.pagina = "selezione"
        elif self.pagina == "intro_classico":
            self.pagina = "selezione"
        self.aggiorna_ui()

    def vai_inizio(self):
        self.pagina = "benvenuto"
        self.tipo_rosario = None
        self.grano = 0
        self.aggiorna_ui()

    def cambia_lingua(self, dropdown, param, keys):
        idx = dropdown.get_selected()
        self.lingua_corrente = keys[idx]
        self.aggiorna_ui()

    def on_key_press(self, controller, keyval, keycode, state):
        if self.pagina == "benvenuto":
            if keyval == Gdk.KEY_space:
                self.vai_a_selezione()
                return True
        elif self.pagina == "selezione":
            if keyval == Gdk.KEY_Escape:
                self.vai_inizio()
                return True
        elif self.pagina in ["intro_classico", "rosario"]:
            if keyval == Gdk.KEY_space or keyval == Gdk.KEY_Right:
                self.avanza()
                return True
            elif keyval == Gdk.KEY_Left:
                self.indietro()
                return True
            elif keyval == Gdk.KEY_Home:
                self.vai_inizio()
                return True
        return False

    def aggiorna_ui(self):
        while (child := self.main_container.get_first_child()) is not None:
            self.main_container.remove(child)
        
        if self.pagina == "benvenuto":
            content = self.crea_pagina_benvenuto()
        elif self.pagina == "selezione":
            content = self.crea_pagina_selezione()
        elif self.pagina == "intro_classico":
            content = self.crea_intro_classico()
        elif self.pagina == "rosario":
            content = self.crea_pagina_rosario()
        
        self.main_container.append(content)
        self.win.grab_focus()

app = RosarioApp()
app.run(None)
