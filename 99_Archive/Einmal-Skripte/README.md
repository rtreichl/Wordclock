# Erledigte Einmal-Skripte

Diese Skripte haben das FreeCAD-Modell oder die Platine einmalig geändert. Sie liegen hier, weil sie beschreiben, was geändert wurde und warum. Sie sind nicht dafür gedacht, erneut zu laufen: Die Pfade beziehen sich auf die alte Lage unter `01_Mechanic/tools` und `02_Electronics/KiCad/tools`, und die Rastermaße stehen als Zahlen darin.

| Skript | Eingriff |
|---|---|
| `add_l1_pocket.py` | Tasche für die Spule L1 im Rückrahmen Q4 |
| `add_minute_dots.py` | Lichtkammern und LED für die Minutenpunkte |
| `fix_dovetail_top.py` | Schwalbenschwanz-Verbindungen oben geschlossen |
| `fix_qual_round2.py` | Korrekturen aus der zweiten Qualifikationsrunde |
| `fix_usb_web.py` | Steg am USB-C-Ausschnitt entfernt |
| `rebuild_frontplate.py` | Frontplatte nach der NEUN-Korrektur neu aufgebaut |
| `update_pcb_holes.py` | Montagelöcher im Modell auf 4,3 mm |
| `swap_mount_holes.py` | Montagelöcher in der Platine auf 4,3 mm |

Die lebenden Skripte der Mechanik sind `01_Mechanic/tools/update_pcb_model.py` und `make_jlc3dp_variant.py`.
