# Flyeralarm
Repo that makes flyers searchable

# Requirements
1. Ziel & Scope

Automatisches Auslesen von Angebotsdaten aus Prospekt-Seiten (Bildern).

Nutzung des vorhandenen YOLO-Modells zur Erkennung von Angebots-Kacheln.

Extraktion der wichtigsten Informationen (Produktname, Preis, Aktionsinfos etc.) pro Kachel über ein Vision-LLM (z. B. GPT-5.1 / GPT-5-mini).

Speicherung der extrahierten Daten in einer Typesense-Collection zur späteren Suche/Filterung.

Nicht im Scope:

Kein Matching zu Einkaufslisten.

Keine komplexe Business-Logik wie „beste Angebote pro Nutzer“ – rein Extraktion + Indexierung.

2. Systemübersicht (High-Level)

Input: Prospekt als Bild (PNG/JPG) oder PDF.

Preprocessing: PDF → einzelne Seitenbilder (falls nötig), Normalisierung.

YOLO-Inference: Erkennung der Angebots-Kacheln, Ausgabe der Bounding Boxes.

Cropper: Zuschneiden der Bildausschnitte je Bounding Box.

Vision-Extractor: Call an OpenAI-Vision (Responses API) pro Crop, Rückgabe als strukturiertes JSON.

Validator & Normalizer: Bereinigung und Normalisierung der JSON-Daten.

Typesense-Writer: Schreiben der Daten in eine Typesense-Collection.

3. Detaillierte Anforderungen pro Schritt
3.1 Input & Preprocessing

Funktionale Anforderungen

System muss Prospekte in folgenden Formaten akzeptieren:

Einzelbild: .png, .jpg, .jpeg

PDF mit mehreren Seiten: .pdf

Wenn PDF:

Jede Seite muss in ein Bild (z. B. PNG) gerendert werden.

Seiten-Reihenfolge muss erhalten bleiben (page_number).

Optional: Bilder normalisieren

Maximalbreite/-höhe konfigurierbar (z. B. 3000 px), Seitenverhältnis beibehalten.

Farbraum: RGB.

Output dieses Schritts

Liste von PageImage-Objekten:

{
  "flyer_id": "rewe_2025_kw48",
  "page_number": 1,
  "image_path": "/data/flyers/rewe_2025_kw48_page_01.png"
}

3.2 YOLO-Inference (Bounding Boxes)

Voraussetzungen

Bereits trainiertes YOLO-Modell (z. B. best.pt) ist vorhanden.

Ein Service/Script, der folgende Inputs annimmt:

image_path

Und ausgibt:

Liste von Bounding Boxes mit Konfidenz & Klasse.

Funktionale Anforderungen

Für jede Prospektseite:

YOLO aufrufen und alle Objekte der relevanten Klassen (z. B. offer_tile, product_box etc.) zurückgeben.

Konfiguration:

Minimaler Confidence-Threshold (z. B. 0.5) muss konfigurierbar sein.

Optionale Filterung nach Klassen.

Output

Für jede Seite z. B.:

{
  "flyer_id": "rewe_2025_kw48",
  "page_number": 1,
  "detections": [
    {
      "bbox_id": "rewe_2025_kw48_01_0001",
      "x1": 120,
      "y1": 640,
      "x2": 520,
      "y2": 1040,
      "confidence": 0.91,
      "class_name": "offer_tile"
    }
  ]
}


Koordinaten können in Pixeln (bezogen auf das Originalbild) gespeichert werden.

3.3 Cropper (Bild-Ausschnitte erzeugen)

Funktionale Anforderungen

Für jede erkannte Bounding Box:

Bildausschnitt aus der entsprechenden Seiten-Grafik ausschneiden.

Optional einen konfigurierbaren Rand (Padding) in Pixel hinzufügen (z. B. 10–20 px), damit Preisbeschriftungen sicher enthalten sind.

Speicherung:

Crops werden unter reproduzierbarem Pfad gespeichert, z. B.
/data/crops/{flyer_id}/{page_number}/{bbox_id}.png.

Alternativ (performance-optimiert):

Crops können auch im Speicher gehalten und direkt an die Vision-API gesendet werden.

Output

Für jeden bbox_id ein CropImage-Objekt:

{
  "flyer_id": "rewe_2025_kw48",
  "page_number": 1,
  "bbox_id": "rewe_2025_kw48_01_0001",
  "crop_path": "/data/crops/rewe_2025_kw48/01/rewe_2025_kw48_01_0001.png"
}

3.4 Vision-Extractor (OpenAI)

Funktionale Anforderungen

Für jeden Crop einen Aufruf an das Vision-Modell (z. B. gpt-5.1-mini oder gpt-5.1) absetzen.

Prompting:

Der Prompt muss klar definieren, welche Informationen extrahiert werden sollen.

Rückgabeformat MUSS strikt JSON sein, damit es maschinenlesbar ist.

Beispiel-Schema für die Rückgabe:

{
  "product_name": "Danone YoPro Drink",
  "brand": "Danone",
  "description": "Protein-Drink, Erdbeer-Himbeer",
  "price_eur": 1.11,
  "old_price_eur": 1.79,
  "unit": "270 g",
  "unit_price_eur": 4.11,
  "currency": "EUR",
  "discount_text": "Aktion",
  "valid_from": null,
  "valid_to": "2025-12-07",
  "extra_bonus_text": "Beim Kauf von 1 Packung 1 Knete-Päckchen gratis"
}


Der Vision-Call muss zusätzlich die Metadaten des Crops kennen:

flyer_id, page_number, bbox_id.

Nichtfunktionale Anforderungen

Konfigurierbares Modell (z. B. gpt-5.1-mini als Default).

Rate-Limit Handling:

Max Requests pro Sekunde konfigurierbar.

Optional Queue/Batching (z. B. mit einfachem Worker-System).

Logging:

Für jeden Request: Erfolg/Misserfolg, Latenz, Tokenverbrauch.

3.5 Validator & Normalizer

Funktionale Anforderungen

Alle JSON-Antworten der Vision-API werden gegen ein fixes Schema geprüft:

Pflichtfelder: product_name, price_eur (kann null sein, aber Feld muss existieren).

Datentypen prüfen:

Preisfelder: float.

Datumfelder: ISO-8601 (YYYY-MM-DD) oder null.

Normalisierungen:

Tausendertrennzeichen und Komma/Punkt in Preisen vereinheitlichen.

Währung standardisieren ("EUR").

Einheiten-Strings bereinigen (z. B. "270 g" vs. "270g").

Fehlerhandling:

Wenn die Antwort nicht parsebar ist:

Einen Re-Try mit einem einfacheren Prompt (z. B. „gib nur Produktname und Preis“).

Wenn immer noch fehlgeschlagen → Datensatz mit Status parse_error = true markieren.

Output

Ein „sauberer“ OfferRecord, der direkt in Typesense gespeichert werden kann:

{
  "id": "rewe_2025_kw48_01_0001",     // = bbox_id
  "flyer_id": "rewe_2025_kw48",
  "retailer": "Rewe",
  "page_number": 1,
  "product_name": "Danone YoPro Drink",
  "brand": "Danone",
  "description": "Protein-Drink, Erdbeer-Himbeer",
  "price_eur": 1.11,
  "old_price_eur": 1.79,
  "unit": "270 g",
  "unit_price_eur": 4.11,
  "discount_text": "Aktion",
  "valid_from": null,
  "valid_to": "2025-12-07",
  "currency": "EUR",
  "bonus_text": "Beim Kauf von 1 Packung 1 Knete-Päckchen gratis",
  "image_path": "/data/crops/rewe_2025_kw48/01/rewe_2025_kw48_01_0001.png",
  "bbox_x1": 120,
  "bbox_y1": 640,
  "bbox_x2": 520,
  "bbox_y2": 1040,
  "confidence": 0.91,
  "parse_error": false,
  "created_at": 1732550400   // Unix Timestamp
}

4. Typesense-Integration
4.1 Typesense-Schema

Anforderung

Es soll mindestens eine Collection geben, z. B. offers.

Vorschlag für das Collection-Schema:

{
  "name": "offers",
  "fields": [
    { "name": "id",            "type": "string" },
    { "name": "flyer_id",      "type": "string",  "facet": true },
    { "name": "retailer",      "type": "string",  "facet": true },
    { "name": "page_number",   "type": "int32",   "facet": true },
    { "name": "product_name",  "type": "string" },
    { "name": "brand",         "type": "string",  "facet": true },
    { "name": "description",   "type": "string" },
    { "name": "price_eur",     "type": "float",   "facet": true },
    { "name": "old_price_eur", "type": "float",   "facet": true },
    { "name": "unit",          "type": "string" },
    { "name": "unit_price_eur","type": "float",   "facet": true },
    { "name": "discount_text", "type": "string",  "facet": true },
    { "name": "valid_from",    "type": "int64",   "facet": true },
    { "name": "valid_to",      "type": "int64",   "facet": true },
    { "name": "currency",      "type": "string",  "facet": true },
    { "name": "bonus_text",    "type": "string" },
    { "name": "image_path",    "type": "string" },
    { "name": "bbox_x1",       "type": "int32" },
    { "name": "bbox_y1",       "type": "int32" },
    { "name": "bbox_x2",       "type": "int32" },
    { "name": "bbox_y2",       "type": "int32" },
    { "name": "confidence",    "type": "float" },
    { "name": "parse_error",   "type": "bool",    "facet": true },
    { "name": "created_at",    "type": "int64",   "facet": true }
  ],
  "default_sorting_field": "created_at"
}


Hinweis: valid_from / valid_to kannst du als Unix-Zeitstempel speichern (oder string, dann type: "string" + Facet).

4.2 Typesense-Writer

Funktionale Anforderungen

Für jeden validierten OfferRecord:

Upsert in die offers-Collection:

Wenn id bereits existiert → aktualisieren.

Sonst → neuen Datensatz anlegen.

Bulk-Operation:

Möglichkeit, mehrere Offers in einem Batch zu senden (Performance).

Fehlerhandling:

Wenn der Typesense-Call fehlschlägt:

Logging des Records + Fehlers.

Optional Retry-Mechanismus.

5. Konfiguration & Infrastruktur

Konfigurierbare Parameter

Pfade:

Input-Verzeichnis für Prospekte.

Output-Verzeichnis für gerenderte Seiten.

Output-Verzeichnis für Crops.

YOLO:

Modellpfad (best.pt).

Confidence-Threshold.

Liste der relevanten Klassen.

OpenAI:

API-Key.

Modellname (z. B. gpt-5.1-mini).

Max Tokens pro Request.

Typesense:

Host, Port, Protokoll (http/https).

API-Key.

Collection-Name.

Nichtfunktionale Anforderungen

Logging:

Mindestens INFO-Level für Pipeline-Schritte und WARN/ERROR für Fehler.

Monitoring:

Anzahl verarbeiteter Seiten, Anzahl erkannter Kacheln, Anzahl parse_errors.

Reproduzierbarkeit:

Flyer-ID und Dateipfade müssen so definiert sein, dass derselbe Prospekt nochmal verarbeitet werden kann, ohne Chaos in der DB zu erzeugen (z. B. über Hash aus Dateiname + Datum).
