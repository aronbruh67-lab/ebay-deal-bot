# eBay Deal Bot

Ein persönlicher eBay.de Deal-Finder Bot mit digitalem Warenkorb, Bildern aus den Anzeigen, kontinuierlichen Updates und bestätigten Aktionen (Ja bieten / Ja kaufen).

**Maximalpreis: 20€ + Versand.**

## Features
- Sucht kontinuierlich nach Deals auf eBay.de
- Zeigt Bilder direkt aus der Anzeige (keine generierten Bilder)
- Digitaler Warenkorb: Manuell speichern, Status anzeigen (gespeichert, geboten, gekauft)
- Intelligente Buttons:
  - Nur Auktion → nur "Ja bieten"
  - Nur Sofort-Kaufen → nur "Ja kaufen"
  - Beides → beide Buttons
- Bei Klick auf "Ja bieten" oder "Ja kaufen": Automatische Ausführung mit deinem eBay-Konto (nach einmaligem Login)
- Verbindung zu deinem eBay-Konto via Browser-Session (Cookies)
- Preisfilter: ≤ 20€ + Versand

## ⚠️ Wichtiger Hinweis
Die Nutzung von Bots auf eBay kann gegen die Nutzungsbedingungen verstoßen. Dieses Tool ist nur für den persönlichen Gebrauch mit menschlicher Bestätigung gedacht. Nutze es auf eigenes Risiko. eBay kann Accounts sperren bei erkanntem automatisiertem Zugriff.

## Installation
```bash
git clone https://github.com/aronbruh67-lab/ebay-deal-bot.git
cd ebay-deal-bot
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

## Setup eBay-Konto
1. Starte das Tool einmal.
2. Beim ersten Mal öffnet sich ein Browser-Fenster – logge dich manuell bei eBay.de ein.
3. Die Session wird gespeichert (cookies.json).

## Nutzung
```bash
streamlit run app.py
```
- Konfiguriere Suchbegriffe
- Deals werden angezeigt mit Bild, Preis, Versand
- Speichere in den Warenkorb
- Klicke "Ja bieten" oder "Ja kaufen" für automatische Aktion

## Konfiguration
In der App oder via .env:
- MAX_PRICE=20
- Suchkeywords

Viel Erfolg beim Schnappen!
