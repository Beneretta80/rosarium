#!/bin/bash

# Percorso della cartella (lo prende in automatico da dove sei ora)
APP_DIR="/home/benerettafamily/Rosario"
SCRIPT_PATH="$APP_DIR/rosario.py"
DESKTOP_FILE="$APP_DIR/rosarium.desktop"

echo "=== Inizio Installazione Rosarium ==="

# 1. Controllo se il file python esiste
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "ERRORE: Non trovo il file $SCRIPT_PATH"
    echo "Controlla che il file si chiami esattamente 'rosario.py'"
    exit 1
fi

# 2. Rendo eseguibile lo script Python
chmod +x "$SCRIPT_PATH"
echo "✔ Permessi esecuzione concessi a rosario.py"

# 3. Rigenero il file .desktop per essere sicuro che sia perfetto
echo "✔ Rigenerazione file icona..."
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Rosarium
Comment=Recita il Santo Rosario
Exec=/usr/bin/python3 $SCRIPT_PATH
Path=$APP_DIR/
Icon=$APP_DIR/images/madonna_pompei.jpg
Terminal=false
Categories=Utility;Education;
StartupNotify=true
EOF

# 4. Rendo eseguibile l'icona stessa
chmod +x "$DESKTOP_FILE"

# 5. Copio l'icona nel menu delle applicazioni di Ubuntu
# (Questo è il passaggio chiave per non far aprire l'editor di testo)
USER_APPS_DIR="$HOME/.local/share/applications"
mkdir -p "$USER_APPS_DIR"
cp "$DESKTOP_FILE" "$USER_APPS_DIR/"
echo "✔ Icona copiata nel menu applicazioni"

# 6. Provo a marcare il file come "fidato" (funziona su alcune versioni di GNOME)
gio set "$DESKTOP_FILE" metadata::trusted true 2>/dev/null
gio set "$USER_APPS_DIR/rosarium.desktop" metadata::trusted true 2>/dev/null

echo ""
echo "=== INSTALLAZIONE COMPLETATA! ==="
echo "Ora fai questa prova:"
echo "1. Premi il tasto Windows (Super) sulla tastiera."
echo "2. Scrivi 'Rosarium' nella barra di ricerca."
echo "3. Clicca sull'icona che appare."
