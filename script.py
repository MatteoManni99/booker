from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
import os
from datetime import datetime
from config import ANACLETO_KEY, MY_TELEGRAM_ID, USERNAME, PASSWORD
from telegram import Bot
import asyncio
from datetime import datetime, timedelta

# Usa il token che ti ha dato BotFather
token = ANACLETO_KEY
chat_id = MY_TELEGRAM_ID
bot = Bot(token=token)

#Crea cartella per gli screenshot
SCREENSHOT_DIR = "screenshots_debug"
if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR)
    print(f"✓ Cartella '{SCREENSHOT_DIR}' creata")

def prenota():
    success_flag = False
    try:
        # webdriver_manager scarica automaticamente il driver corretto
        print("🔍 Ricerca e download chromedriver...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        print("✓ Chromedriver pronto")
        
        print("1. Apertura sito...")
        driver.get("https://ecomm.sportrick.com/REPLYwellnessTO")
        time.sleep(1)
        
        # Chiudi eventuali popup di cookie o notifiche
        print("2. Chiusura popup e cookie...")
        try:
            # Prova diversi selettori comuni per chiudere i popup
            close_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accetta')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'chiudi')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'close')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ok')]",
                "//div[@class='cookie-consent']//button",
                "//div[@id='cookieConsent']//button",
                "//button[@class='close']",
                "//button[@aria-label='Close']"
            ]
            
            for selector in close_selectors:
                try:
                    buttons = driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed():
                            button.click()
                            print(f"  ✓ Chiuso popup: {button.text[:30]}")
                            time.sleep(0.5)
                except:
                    pass
        except Exception as e:
            print(f"  ℹ Nessun popup trovato: {e}")
        
        print("✓ Sito aperto")
        
        print("3. Ricerca campo username...")
        username_field = driver.find_element(By.NAME, "UserName")
        print(f"✓ Username field trovato")
        
        print("4. Ricerca campo password...")
        password_field = driver.find_element(By.NAME, "Password")
        print(f"✓ Password field trovato")
        
        print("5. Inserimento credenziali...")
        username_field.send_keys(USERNAME)
        password_field.send_keys(PASSWORD)
        print("✓ Credenziali inserite")
        
        print("6. Ricerca bottone login...")
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        print(f"✓ Login button trovato")
        
        print("7. Click su login...")
        login_button.click()
        time.sleep(1)
        print("✓ Login completato")
        
        print("8. Click su Booking...")
        booking_element = driver.find_element(By.ID, "mainmenu-booking")
        booking_element.click()
        time.sleep(0.5)
        print("✓ Booking cliccato")
        
        print("9. Click su Nuova Prenotazione...")
        nuova_prenotazione = driver.find_element(By.XPATH, "//span[@class='title' and contains(text(), 'Nuova Prenotazione')]")
        # Clicca sul genitore (li o a) perché il click deve essere su un elemento clickable
        parent = nuova_prenotazione.find_element(By.XPATH, "..")
        parent.click()
        time.sleep(0.5)
        print("✓ Nuova Prenotazione cliccato")
        
        print("10. Click su Sala Attrezzi...")
        sala_attrezzi = driver.find_element(By.XPATH, "//h3[@class='list-group-item-heading col-md-10 font-blue-madison' and contains(text(), 'SALA ATTREZZI')]")
        # Clicca sul genitore che contiene l'elemento clickable
        parent = sala_attrezzi.find_element(By.XPATH, "..")
        parent.click()
        time.sleep(0.5)
        print("✓ Sala Attrezzi cliccato")
        
        print("11. Click su '>' cinque volte...")
        for i in range(4):
            # Il > è un'icona fa-chevron-right, cerchiamo il pulsante/elemento che la contiene
            next_button = driver.find_element(By.XPATH, "//i[@class='fa fa-chevron-right']/..")
            next_button.click()
            time.sleep(0.1)
            print(f"  ✓ Click {i+1}/5 su '>'")
        print("✓ Completati i 5 click su '>'")
        time.sleep(4)  # Attendi il caricamento degli orari disponibili
        
        print("12. Click su '18:15 - 60 min SALA ATTREZZI'...")
        # Cerchiamo tutti gli slot disponibili
        slots = driver.find_elements(By.XPATH, "//div[@class='event-slot slot-available']")
        print(f"  ℹ Trovati {len(slots)} slot disponibili")
        
        found = False
        # Scorriamo gli slot in ordine inverso per trovare l'ultimo disponibile, per non confondersi con lo stesso orario di un altro giorno
        for slot in reversed(slots):
            try:
                time_start = slot.find_element(By.XPATH, ".//span[@class='time-start']").text
                description = slot.find_element(By.XPATH, ".//div[@class='slot-description']").text
                
                print(f"  - Slot: {time_start} {description}")
                
                # Cerchiamo lo slot con orario 18:15
                if "18:15" in time_start and "SALA ATTREZZI" in description:
                    print(f"  ✓ Trovato slot target: {time_start}")
                    # Scrolla in vista
                    driver.execute_script("arguments[0].scrollIntoView(true);", slot)
                    time.sleep(0.2)
                    # Clicca sul bottone "Prenota" dentro questo slot
                    prenota_buttons = slot.find_elements(By.XPATH, ".//div[@class='slot-notes']")
                    if prenota_buttons:
                        prenota_buttons[0].click()
                    else:
                        slot.click()
                    found = True
                    break
            except Exception as e:
                pass
        
        if not found:
            print("  ℹ Slot 18:15 non trovato, provo con il primo disponibile...")
            # Se 18:15 non esiste, usa il primo slot
            if slots:
                driver.execute_script("arguments[0].scrollIntoView(true);", slots[0])
                time.sleep(1)
                prenota_buttons = slots[0].find_elements(By.XPATH, ".//div[@class='slot-notes']")
                if prenota_buttons:
                    prenota_buttons[0].click()
                else:
                    slots[0].click()
        
        time.sleep(2)
        print("✓ Orario selezionato")
        
        print("13. Click su Conferma Prenotazione...")
        conferma_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Conferma Prenotazione')]")
        #conferma_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Lista')]")
        conferma_button.click()
        time.sleep(1)
        print("✓ Prenotazione confermata")
        
        print("14. Click su No...")
        no_button = driver.find_element(By.XPATH, "//button[contains(text(), 'No')]")
        #no_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Ok')]")
        no_button.click()
        time.sleep(0.5)
        print("✓ Prenotazione completata!")
        success_flag = True
        
    except Exception as e:
        print(f"✗ ERRORE: {type(e).__name__}: {e}")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, f"ERRORE_{timestamp}.png"))
            print(f"Screenshot salvato in '{SCREENSHOT_DIR}/ERRORE_{timestamp}.png'")
            return success_flag
        except:
            return success_flag
    finally:
        try:
            driver.quit()
            return success_flag
        except:
            return success_flag

async def invia_messaggio(success_flag = False):
    data_futura = datetime.now() + timedelta(days=7)
    giorno = str(data_futura.day)
    giorni_settimana = ['lunedì', 'martedì', 'mercoledì', 'giovedì', 'venerdì', 'sabato', 'domenica']
    giorno_settimana = giorni_settimana[data_futura.weekday()]

    if success_flag:
        await bot.send_message(
            chat_id=chat_id, 
            text=f"✅ Prenotazione completata per {giorno_settimana} {giorno} alle 18:15 con successo!"
        )
    else:
        await bot.send_message(
            chat_id=chat_id, 
            text=f"❌ Prenotazione per {giorno_settimana} {giorno} alle 18:15 fallita. Controlla i log per dettagli."
        )

if __name__ == "__main__":
    success_flag = prenota()
    asyncio.run(invia_messaggio(success_flag))