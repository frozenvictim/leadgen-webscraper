from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import base64
import time
import pandas as pd


def scrape_yellow_pages(base_url, max_results=None):
    """Scrape business data from a Yellow Pages-like website using Selenium for 'Mehr Anzeigen'"""
    all_data = []
    total_results = 0  # Variable, um die Anzahl der gescrapten Ergebnisse zu verfolgen

    # Chrome Options (optional, aber oft nützlich, um das Browserfenster zu verstecken)
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Optional: startet Chrome im Headless-Modus (kein GUI)

    # Verwende die Service-Klasse, um den WebDriver zu starten
    service = Service(r"C:\Users\Fabia\chromedriver.exe")  # Pfad zu deinem ChromeDriver
    driver = webdriver.Chrome(service=service, options=chrome_options)  # Chrome starten

    driver.get(base_url)  # Seite laden
    time.sleep(2)  # Warten, bis die Seite geladen ist

    while True:
        # Scrape die Seite
        soup = BeautifulSoup(driver.page_source, "html.parser")
        businesses = soup.find_all("article", class_="mod mod-Treffer")

        # Wenn weniger Ergebnisse gefunden werden als erwartet, stoppe das Scraping
        if not businesses:
            break

        print(f"Anzahl gefundener Elemente auf dieser Seite: {len(businesses)}")

        for business in businesses:
            if max_results and total_results >= max_results:  # Wenn max_results gesetzt ist und wir die Grenze erreicht haben
                print(f"Maximale Anzahl von {max_results} Ergebnissen erreicht.")
                driver.quit()
                return all_data

            name = business.find('h2', class_='mod-Treffer__name')
            branche = business.find('p', class_='d-inline-block mod-Treffer--besteBranche')
            phone = business.find('a', class_='mod-TelefonnummerKompakt__phoneNumber contains-icon-big-tel')
            address = business.find('div', class_='mod-AdresseKompakt__adress-text')
            website_tag = business.find('span', class_='mod-WebseiteKompakt__text')

            name = name.text.strip() if name else 'N/A'
            branche = branche.text.strip() if branche else 'N/A'
            phone = phone.text.strip() if phone else 'N/A'

            # Wenn keine Adresse vorhanden ist, verwende einen Platzhalter
            if address:
                address = address.text.strip()
                cleaned_address = address.replace("\n", "").replace("\t", "").strip()
            else:
                cleaned_address = 'Keine Adresse verfügbar'  # Platzhalter für fehlende Adresse

            if website_tag and "data-webseitelink" in website_tag.attrs:
                encoded_link = website_tag["data-webseitelink"]
                decoded_link = base64.b64decode(encoded_link).decode("utf-8")
                website = decoded_link.strip() if decoded_link else 'N/A'
            else:
                website = 'N/A'

            # Verhindern, dass doppelte Adressen hinzugefügt werden
            existing_entry = next((item for item in all_data if item['Addresse'] == cleaned_address), None)
            if existing_entry:
                print(f"Adresse {cleaned_address} bereits hinzugefügt, überspringe diese Firma.")
                continue  # Wenn die Adresse bereits existiert, überspringe dieses Element

            all_data.append({
                'Name': name,
                'Branche': branche,
                'Telefon': phone,
                'Addresse': cleaned_address,
                'Website': website,
            })

            total_results += 1  # Zähle die extrahierten Ergebnisse

        # Klicken auf den "Mehr Anzeigen"-Button, wenn mehr Ergebnisse geladen werden sollen
        try:
            load_more_button = driver.find_element(By.XPATH, "//*[@id='mod-LoadMore--button']")
            load_more_button.click()  # Klicke auf den Button, um mehr Ergebnisse zu laden
            time.sleep(3)  # Warte auf das Laden der nächsten Ergebnisse
        except Exception as e:
            print("Kein weiterer Button gefunden oder Fehler: ", e)
            break  # Stoppe, wenn der Button nicht mehr existiert oder ein Fehler auftritt

    # Schließe den Webdriver
    driver.quit()

    return all_data


def save_to_csv(data, filename):
    """Saves the scraped data to a CSV file"""
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding="utf-8", sep=';')
    print(f"Datei gespeichert: {filename}")

def extract_city_code(url):
    """Extrahiere den Stadtnamen oder die Stadtnummer hinter 'stadt/' in der URL"""
    # Finde den Teil der URL hinter 'stadt/'
    start_index = url.find('stadt/') + len('stadt/')
    if start_index != -1:
        return url[start_index:]
    return None

if __name__ == "__main__":
    base_url = f"https://www.gelbeseiten.de/suche/stadt/bundesweit"
    max_results = 200  # Anzahl der maximalen Ergebnisse
    data = scrape_yellow_pages(base_url)
    save_to_csv(data, f"business_leads_{extract_city_code(base_url)}.csv")
