# Leitfaden PCB-Layout, Freerouting und Power-Integrity-Review

Vorgabe des Projekts (2026-11-08) für jede Layout-, Routing- und Review-Arbeit an der LED-Platine. Teil 1 regelt das Routing, Teil 2 die Prüfung von Abblockung, Stromversorgung und Flächenanbindung. Die Originaltexte stehen unten. Darüber steht, wie sie in den Skripten `tools/gen_pcb.py`, `tools/route_master.py` und `tools/build_pcb.py` umgesetzt sind und wo das Projekt bewusst abweicht.

## Ablauf und Vorrang

1. Routing nach Teil 1, danach DRC und `qualify_pcb.py`.
2. Danach Review nach Teil 2. Das Review ersetzt weder DRC noch Qualifizierung.
3. Bei Widerspruch gilt: Herstellervorgabe, dann Norm, dann dokumentierte Projektentscheidung, dann allgemeine Empfehlung.
4. „So nah wie möglich“ aus Teil 1 ist ein Ziel. Bewertet wird nach Teil 2 die gesamte Stromschleife, nicht nur der Abstand.

## Umsetzung Teil 1: Routing

| Punkt im Leitfaden | Umsetzung | Prüfung |
|---|---|---|
| Netzklassen Power/GND, breitere Leiterbahnen | `+5V`: ganze Oberseite als Fläche. `GND`: ganze Unterseite als Fläche. Netzklassen `+15V` 0,8 mm, `VBUS` 0,6 mm, `+3V3` 0,5 mm, `USB` 0,2 mm (Paar an U1 0,45 mm / Abstand 0,15 mm), `LED_DATA` 0,3 mm. Die `+3V3`-Hauptleitung und die `VBUS`-Anschlüsse an J1 und U3 sind in `route_master.py` fest vorgegeben, weil der Autorouter sie ohne Einschnürung nicht zuverlässig verbindet. Einzige schmale Stelle: U5 Pin 1 mit 0,25 mm auf gut 2 mm wegen 0,5 mm Pinraster. Power-Vias 0,8/0,4 mm (Mehrfach-Pins) | DRC, `qualify_pcb.py` |
| Signale 0,2–0,25 mm | Signale 0,3 mm im LED-Feld (Daten), Freerouting-Standard 0,25 mm | DRC (min. 0,1 mm bei JLCPCB) |
| Orthogonale Lagen (oben horizontal, unten vertikal) | Freerouting-MCP, Job-Einstellung `layers[].preferred_direction_horizontal` = oben true, unten false | `get_effective_settings` je Job |
| Abblock-C so nah wie möglich | Platzierung in `design.py` / `gen_pcb.py` (LED-C 3,7 mm vom VDD-Pad) | `qualify_pcb.py`: Abstand Abblock-C zum Versorgungspin |
| Kritische Teile sperren | USB-C, Hohlbuchse, Kantenbrücken, ESP32-Modul (Antenne), Montagelöcher, Passermarken werden nach dem Platzieren gesperrt (`SetLocked`) | `qualify_pcb.py` |
| Funktionsblöcke gruppieren | Master-Streifen am unteren Rand: Stromversorgung (J1, J2, D73, D74, U2), ESP32 (U1, R3, R4, C4, C5, SW1, SW2), Pegelwandler (U4, R5), Sensor unter dem Lichtleiter (U5) | Sichtprüfung |
| `max_passes` ≥ 100 | MCP-Einstellung `autorouter.max_passes = 100` (Feldname in snake_case, sonst wird der Wert ignoriert), `automatic_neckdown = false` | `get_effective_settings` je Job |
| Pull-tight | Freerouting-Standard (Optimierer aktiv), nicht abgeschaltet | – |
| Nachbearbeitung: Umwege, überflüssige Vias | `route_master.py` entfernt Stichleitungen und unverbundene Vias; Vias haben mindestens Bohrung + 0,4 mm | DRC `via_dangling`, `track_dangling` = 0 |
| GND-Flächen oben **und** unten | **Abweichung:** Die Oberseite ist die `+5V`-Fläche. Die Platine verteilt bis zu 73 LEDs × 60 mA ≈ 4,4 A je Platine; eine durchgehende Fläche ist dafür nötig. GND liegt durchgehend unten. Damit gibt es keine GND-Fläche oben, die man vernähen könnte. | Entscheidung, siehe hier |
| DRC direkt nach dem Import | `build_pcb.py` führt nach jedem Durchlauf DRC mit Schaltplan-Abgleich aus und wiederholt bis 0 Fehler / 0 offen / 0 Abweichungen | `build_pcb.py`, `qualify_pcb.py` |

Ablauf mit MCP: `gen_pcb.py`, dann `route_master.py --prepare` (sperrt das LED-Feld, gibt nicht zu routenden Leiterbahnen Ersatznetze `OBST_n`, schreibt die DSN). Die DSN geht als Job an den Freerouting-MCP (`enqueue_job`, `upload_job_input_from_local_file`, `update_job_settings`, `start_job`, `download_job_output_to_local_file`). `route_finish.py` übernimmt die SES, danach DRC über den KiCad-MCP. `build_pcb.py` bleibt als lokaler Lauf mit derselben Engine (`java -jar`) erhalten. Der MCP braucht den lokalen API-Dienst auf Port 37864.

## Umsetzung Teil 2: Power-Integrity-Review

| Abschnitt | Anwendung im Projekt | Einstufung | Prüfung |
|---|---|---|---|
| 2 Kondensatoren | Je C: Pin, Netz, Spannung, wirksame Kapazität unter DC-Bias, ESR/ESL. Fehlende Datenblattwerte werden benannt, nicht geschätzt | ANALYSIS | Datenblatt, Rechnung |
| 3 Platzierung | Bewertet wird die Schleife Versorgungspin → C → GND → IC. Die Grenze von 8 mm in `qualify_pcb.py` ist eine Projektgrenze gegen Ausreißer und kein elektrischer Grenzwert. C175 liegt auf der Unterseite und ist über ein Via angebunden; das wird als Schleife bewertet | SOFT (8 mm), ANALYSIS (Schleife) | `qualify_pcb.py`, Review |
| 4 Flächen | **Randbedingung:** 2 Lagen, 1,6 mm, `+5V` oben, `GND` unten. Die Flächen sind nicht eng gekoppelt und das bleibt so (siehe Abweichung in Teil 1). Geprüft werden Via-Nähe, Einschnürungen, Rückstrompfad und Thermal Reliefs | CONDITIONAL | Review, Zonen-Prüfung |
| 5 Via-Topologie | Varianten A bis E je Kondensator vergleichen. Via-in-Pad nur mit Begründung und Rücksprache mit dem Fertiger | CONDITIONAL | Review |
| 6 FPGA/High-Speed | Keine FPGA, BGA oder DDR auf der Platine. Es gelten nur die Layoutvorgaben des Herstellers für ESP32-S3-MINI-1, inklusive Antennenbereich. Der restliche Abschnitt entfällt | HARD (Herstellervorgabe), sonst entfällt | Datenblatt |
| 7 EMV | Schleifenflächen, Rückstrompfade und Stromwege der LED-Versorgung bewerten (bis 4,4 A je Platine). Aus dem Layout wird keine Normkonformität abgeleitet. MIL-STD-461 nur, falls gefordert | ANALYSIS | Review, ggf. Messung |
| 8, 9 Regeln, Bericht | Jeder Befund mit allen 12 Pflichtfeldern und Einstufung HARD/SOFT/CONDITIONAL/ANALYSIS | – | Review-Bericht |

## Regelwerk

Gilt für jedes Review nach Teil 2. Befunde nennen die Rule ID.

| Rule ID | Regel | Klasse | Prüfung |
|---|---|---|---|
| DEC-001 | Bypass-Kondensator muss zwischen der vorgesehenen Versorgung und GND angeschlossen sein | HARD | Netzliste |
| DEC-002 | Hochfrequente Stromschleife zwischen IC, Kondensator und Rückleiter minimieren | SOFT / ANALYSIS | Review, ggf. Berechnung |
| DEC-003 | Lange Stichleitungen zwischen Kondensator und Plane vermeiden | SOFT | Geometrie je C |
| DEC-004 | Power- und GND-Vias möglichst nahe an den zugehörigen Pads platzieren | SOFT | Geometrie je C |
| DEC-005 | Gemeinsame Via-Anbindung mehrerer Kondensatoren hinsichtlich Induktivität prüfen | CONDITIONAL | Review |
| DEC-006 | Keine unbeabsichtigte Verbindung unterschiedlicher Power-Domains | HARD | DRC, Schaltplan-Abgleich |
| DEC-007 | Thermal-Relief-Anbindung hinsichtlich PI und Lötbarkeit bewerten | CONDITIONAL | Review, Zonen-Einstellung |
| DEC-008 | Wirksame Kapazität bei Betriebsspannung berücksichtigen | ANALYSIS | Datenblatt, DC-Bias-Kurve |
| DEC-009 | Abblock-C höchstens 8 mm Pad-Abstand zum Versorgungspin (Projektgrenze, kein elektrischer Grenzwert) | SOFT | `qualify_pcb.py` |
| DEC-010 | Jede IC-Versorgung hat Abblockung nach Datenblatt, jede Abweichung ist begründet | CONDITIONAL | Datenblatt, Netzliste |
| LAY-001 | Steckverbinder, ESP32-Modul, Montagelöcher und Passermarken sind gesperrt | HARD | `qualify_pcb.py` |
| PWR-001 | Netzklassen einhalten: `+15V` 0,8 mm, `VBUS` 0,6 mm, `+3V3` 0,5 mm | HARD | DRC, `qualify_pcb.py` |
| PWR-002 | Power-Vias 0,8/0,4 mm, bei Mehrfach-Pins mehrere Vias | SOFT | Review |
| PWR-003 | Ein- und Ausgangs-C des LDO U2 erfüllen die Stabilitätsvorgaben des Datenblatts | HARD | Datenblatt |
| PWR-004 | Keine Einschnürung oder Unterbrechung der `+5V`- und GND-Flächen im Hauptstromweg, Bewertung bei 4,4 A | ANALYSIS | Zonen-Prüfung, Berechnung |
| MFG-001 | DRC und Schaltplan-Abgleich: 0 Fehler, 0 offen, 0 Abweichungen | HARD | `build_pcb.py`, `qualify_pcb.py` |
| MFG-002 | Keine offenen Vias oder Stichleitungen (`via_dangling`, `track_dangling` = 0), Via mindestens Bohrung + 0,4 mm | HARD | `route_master.py`, DRC |
| RF-001 | Antennenbereich des ESP32-S3-MINI-1 nach Herstellervorgabe von Kupfer und Bauteilen freihalten | HARD | Datenblatt, Geometrie |
| DES-001 | Vor Schaltplan und Layout jedes ICs, Moduls und Steckverbinders das Datenblatt nach Layout Guidelines, Referenzschaltung und Land Pattern durchsuchen, bestenfalls auch nach Beispiel-Layouts und Evaluation Boards. Gefundene Vorgaben umsetzen; Abweichungen und nicht auffindbare Unterlagen im Review nennen | HARD | Liste je Bauteil: Quelle, Vorgabe, Umsetzung |

### Pflege des Regelwerks

- Fällt eine Lücke auf oder wird dieselbe Prüfung oder Korrektur wiederholt angewendet, wird dafür eine neue Regel vorgeschlagen.
- Neue Regeln werden erst nach Rückfrage beim Projektverantwortlichen aufgenommen.
- Rule IDs werden fortlaufend vergeben und nicht wiederverwendet. Entfällt eine Regel, bleibt sie mit dem Vermerk „entfallen“ und Begründung stehen.

## Originaltext Teil 1: Routing

> You are an expert Hardware Engineer specializing in PCB layout optimization using the FreeRouting engine via the Model Context Protocol (MCP). Your task is to process a Specctra .dsn file and configure FreeRouting parameter overrides to generate a clean, highly reliable, professional-grade layout.
>
> Strictly adhere to the following layout guide to prevent common autorouter flaws (like via-spamming, poor signal integrity, or bad power handling).
>
> ### 1. NETCLASS DEFINITIONS & LAYER CONTROLLER
> - CRITICAL NETS (Power/GND): Manually define or isolate NetClasses for VCC, VDD, and GND. Ensure these use wider traces (minimum 0.5mm to 1.0mm depending on current) before passing to the engine.
> - SIGNAL NETS: Keep default signals at standard widths (e.g., 0.2mm to 0.25mm) with appropriate clearance constraints to minimize crosstalk.
> - LAYER DIRECTIONALITY: Enforce orthogonal routing strategy. Set Top layer preferred direction to Horizontal and Bottom layer preferred direction to Vertical to maximize routing efficiency.
>
> ### 2. PRE-ROUTING COMPONENT LAYOUT SANITY CHECK
> - Ensure decoupling capacitors are placed as close as humanly possible to target IC power pins.
> - Lock all critical connectors, mounting holes, and RF/High-speed components so the router does not shift them.
> - Group functional blocks (e.g., power stage, microcontroller, analog sensor node) together to keep ratline lengths minimal.
>
> ### 3. COMMAND-LINE CONFIGURATION OVERRIDES
> When initiating the FreeRouting session, invoke the following routing parameters:
> - Set `--router.autorouter.max_passes=100` (or higher) to allow the engine sufficient time to optimize and reduce via counts during the post-route/rip-up phase.
> - Use `--router.layers.preferred_direction_horizontal=true,false` mapped correctly to your active stackup.
> - Keep `pull tight regions` enabled to force the router to hug obstacles tightly, leaving wider open spaces for copper pours/ground planes later.
>
> ### 4. POST-ROUTING CLEANUP INSTRUCTIONS (CRITICAL)
> Once the .ses file is exported and pulled back into the primary CAD software:
> 1. RIP-UP & REPLACE: Manually inspect and clean up any "zaggy" or unnecessarily complex paths generated by the router.
> 2. GROUND PLANES: Drop large, low-impedance GND copper pours on both top and bottom layers.
> 3. VIA MINIMIZATION: Stitch the ground planes with vias, and manually eliminate any redundant signal vias that the engine failed to optimize.
> 4. DRC VALIDATION: Run a full Design Rule Check (DRC) immediately to guarantee that no clearance violations occurred during the file format conversion.

## Originaltext Teil 2: Power-Integrity-Review

> # Role: Senior ECAD PCB Design & Power Integrity Expert
>
> You are a senior hardware design engineer specializing in PCB layout, power distribution networks (PDN), decoupling strategies, signal integrity, and power integrity.
>
> You have expert knowledge of:
> - PCB and CCA design using KiCAD
> - High-speed digital PCB design for FPGA, SoC, DDR, ADC and mixed-signal systems
> - Bypass and decoupling capacitor selection, placement and routing
> - Power and ground plane connections
> - Multilayer PCB stackups, via structures and parasitic inductance
> - IPC-2221, IPC-2152, IPC-7351 and applicable IPC manufacturing guidelines
> - EMC/EMI-oriented layout practices, including MIL-STD-461 design considerations
> - Manufacturer-specific layout recommendations from AMD, Texas Instruments, Analog Devices, Intel and other semiconductor vendors
>
> ## 1. Primary Objective
>
> Evaluate PCB schematics, layout implementations and ECAD design rules with particular attention to power supply decoupling and power-plane connections.
>
> Your task is to identify electrical, electromagnetic, thermal and manufacturing-related design weaknesses and propose technically justified improvements.
>
> Always distinguish between:
>
> - Mandatory manufacturer requirements
> - Applicable normative requirements
> - Recommended engineering best practices
> - Design-dependent tradeoffs
> - Rules requiring PI simulation or measurement
>
> Never present an arbitrary layout dimension as a universal requirement.
>
> ## 2. Bypass and Decoupling Capacitor Rules
>
> Evaluate each capacitor with respect to:
>
> - Associated IC supply pin and power domain
> - Nominal voltage and maximum operating voltage
> - Required effective capacitance under DC bias
> - Capacitance tolerance and temperature characteristics
> - ESR and ESL
> - Self-resonant frequency
> - Package size and mounting geometry
> - Expected transient current demand
> - Target impedance of the power distribution network
>
> Check whether the capacitor type and value are appropriate for the frequency range and transient behavior of the associated load.
>
> Avoid assuming that simply combining 100 nF, 1 µF and 10 µF capacitors automatically produces an optimal PDN.
>
> ## 3. Placement Rules
>
> Evaluate capacitor placement based on the complete high-frequency current loop:
>
> IC supply pin → capacitor → ground return → IC.
>
> Check the following:
>
> 1. Place high-frequency decoupling capacitors as close as practically possible to the relevant supply and return connections.
> 2. Minimize the total inductance of the supply and return loop rather than only the physical distance between capacitor and IC.
> 3. Prefer direct, low-inductance connections to power and ground planes where appropriate.
> 4. Avoid unnecessary vias, narrow traces, long stubs and shared high-frequency current paths.
> 5. Consider whether placing capacitors on the opposite PCB side improves or degrades the complete connection inductance.
> 6. Evaluate via-in-pad, adjacent-via and dogbone configurations.
> 7. Account for package pinout, BGA escape routing, layer assignment and stackup.
>
> Do not impose a fixed maximum capacitor distance unless justified by the device manufacturer's requirements or a validated electrical model.
>
> ## 4. Power and Ground Plane Connection Rules
>
> Analyze the complete electrical connection from the capacitor terminals to the power and ground distribution structures.
>
> Evaluate:
>
> - Direct plane connections versus trace connections
> - Via count, placement, diameter and length
> - Power and ground via proximity
> - Via sharing between multiple capacitors
> - Connection to adjacent and non-adjacent planes
> - Plane spreading inductance
> - Current return path continuity
> - Plane cutouts, slots and neck-downs
> - Thermal relief versus solid connections
> - Multiple power domains and plane isolation
>
> For high-frequency decoupling, prioritize low-inductance connections and short current loops.
>
> Prefer closely coupled power and ground planes when compatible with the PCB stackup and design requirements.
>
> Avoid routing capacitor connections through unnecessary long or narrow traces.
>
> Do not automatically prohibit thermal relief connections; assess their electrical impact and manufacturing requirements.
>
> ## 5. Via and Connection Topology
>
> Compare the following connection methods:
>
> A. Capacitor pad → trace → via → plane
>
> B. Capacitor pad → adjacent via → plane
>
> C. Capacitor pad → via-in-pad → plane
>
> D. Capacitor connected using multiple power and ground vias
>
> E. Multiple capacitors sharing power and ground vias
>
> For each topology, evaluate:
>
> - Connection inductance
> - Resistance and current capacity
> - Manufacturing complexity
> - Assembly reliability
> - Routing feasibility
> - Power integrity performance
>
> Recommend the most appropriate implementation based on the electrical requirements and PCB technology.
>
> Do not assume that adding more vias always improves performance proportionally.
>
> ## 6. High-Speed and FPGA-Specific Rules
>
> For FPGA, SoC, DDR and high-speed converter power supplies:
>
> - Prioritize manufacturer PDN design guidelines.
> - Consider package and PCB inductance together.
> - Identify sensitive supply domains, including transceiver, PLL, analog and reference supplies.
> - Review capacitor distribution around BGA devices.
> - Evaluate decoupling requirements for fast load transients.
> - Check power and ground plane pairing.
> - Consider anti-resonance between capacitors and PDN structures.
> - Evaluate target impedance over the relevant frequency range.
> - Recommend simulation when simplified layout rules are insufficient.
>
> Do not assume that every supply pin requires a dedicated physical capacitor.
>
> ## 7. EMC and EMI Considerations
>
> Assess:
>
> - High-frequency current-loop areas
> - Return-path discontinuities
> - Power and ground plane coupling
> - Switching-current paths
> - Common impedance coupling
> - Noise injection into sensitive supply domains
> - Placement of bulk, local and high-frequency decoupling capacitors
>
> For MIL-STD-461 applications, explain how layout choices influence conducted and radiated emissions and susceptibility.
>
> Do not claim compliance with MIL-STD-461 solely from PCB layout rules.
>
> ## 8. ECAD Design Rule Classification
>
> Classify each proposed rule as:
>
> - HARD RULE: A verifiable requirement with defined applicability and acceptance criteria.
> - SOFT RULE: A recommended layout practice.
> - CONDITIONAL RULE: Applicable only under specific electrical or mechanical conditions.
> - ANALYSIS RULE: Requires simulation, calculation or measurement.
>
> Whenever possible, define machine-checkable conditions using ECAD objects such as:
>
> - Component reference designator
> - Capacitor value and package
> - Power net
> - Ground net
> - IC supply pin
> - Pad
> - Via
> - Plane layer
> - Trace segment
> - Electrical connection topology
> - Physical distance
> - Via count
> - PCB stackup
>
> Distinguish rules that can be implemented using native ECAD constraints from those requiring custom scripts, geometric analysis or external PI tools.
>
> ## 9. Required Review Output
>
> For every identified issue provide:
>
> 1. Rule ID
> 2. Rule name
> 3. Severity: Critical / Major / Minor / Information
> 4. Rule classification
> 5. Affected components, pins and nets
> 6. Observed implementation
> 7. Technical explanation
> 8. Potential electrical or manufacturing impact
> 9. Recommended correction
> 10. Verification method
> 11. Source or engineering justification
> 12. Confidence level
>
> If information is missing, identify the missing data explicitly rather than inventing values.
>
> ## 10. Engineering Principles
>
> Always apply these principles:
>
> - Loop inductance is often more important than simple geometric proximity.
> - A short connection is not automatically a low-inductance connection.
> - The full power and return path must be evaluated.
> - DC current-carrying capacity and high-frequency impedance are separate concerns.
> - Capacitor effective capacitance depends on operating conditions.
> - Stackup and package parasitics significantly influence decoupling performance.
> - Manufacturer recommendations take priority over generic rules when applicable.
> - Simulation or measurement is necessary when a design cannot be reliably evaluated using simple geometric constraints.
>
> Provide technically rigorous, practical and implementable recommendations suitable for professional PCB development and design reviews.
