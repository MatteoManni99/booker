from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
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

def prenota(orario):
    success_flag = False
    tipo_conferma = "ok"
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
        for i in range(5):
            # Il > è un'icona fa-chevron-right, cerchiamo il pulsante/elemento che la contiene
            next_button = driver.find_element(By.XPATH, "//i[@class='fa fa-chevron-right']/..")
            next_button.click()
            time.sleep(0.1)
            print(f"  ✓ Click {i+1}/5 su '>'")
        print("✓ Completati i 5 click su '>'")
        time.sleep(5)  # Attendi il caricamento degli orari disponibili
        
        print(f"12. Click su '{orario} - 60 min SALA ATTREZZI'...")
        # Cerchiamo tutti gli slot disponibili
        slots = driver.find_elements(By.XPATH, "//div[@class='event-slot slot-available']")
        print(f"  ℹ Trovati {len(slots)} slot disponibili")
        # Proviamo a trovare lo slot con l'orario specifico
        for slot in slots:
            try:
                time_start = slot.find_element(By.XPATH, ".//span[@class='time-start']").text
                
                if orario in time_start:
                    print(f"  ✓ Trovato slot: {time_start}")
                    driver.execute_script("arguments[0].scrollIntoView(true);", slot)
                    time.sleep(0.5)
                    slot.click()
                    break
            except:
                pass
        
        time.sleep(2)
        print("✓ Orario selezionato")
        
        print("13. Click su Conferma Prenotazione...")
        try:
            conferma_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Conferma Prenotazione')]")
            if conferma_button.is_displayed():
                conferma_button.click()
            else:
                raise Exception("Bottone 'Conferma Prenotazione' non visibile")
        except NoSuchElementException:
            print("'Conferma Prenotazione' non trovato, provo con 'Lista'...")
            tipo_conferma = "lista"
            try:
                lista_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Lista')]")
                if lista_button.is_displayed():
                    lista_button.click()
                else:
                    raise Exception("Bottone 'Lista' non visibile")
            except NoSuchElementException:
                raise Exception("Né 'Conferma Prenotazione' né 'Lista' sono disponibili")

        time.sleep(1)
        print("✓ Prenotazione confermata")
        
        print("14. Click su No...")
        try:
            no_button = driver.find_element(By.XPATH, "//button[contains(text(), 'No')]")
            if no_button.is_displayed():
                no_button.click()
        except NoSuchElementException:
            print("'No' non trovato, provo con 'Ok'...")
            tipo_conferma = "lista"
            try:
                ok_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Ok')]")
                if ok_button.is_displayed():
                    ok_button.click()
                else:
                    raise Exception("Bottone 'Ok' non visibile")
            except NoSuchElementException:
                raise Exception("Né 'No' né 'Ok' sono disponibili")
        time.sleep(0.5)
        print("✓ Prenotazione completata!")
        success_flag = True
        
    except Exception as e:
        print(f"✗ ERRORE: {type(e).__name__}: {e}")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, f"ERRORE_{timestamp}.png"))
            print(f"Screenshot salvato in '{SCREENSHOT_DIR}/ERRORE_{timestamp}.png'")
            return success_flag, tipo_conferma
        except:
            return success_flag, tipo_conferma
    finally:
        try:
            driver.quit()
            return success_flag, tipo_conferma
        except:
            return success_flag, tipo_conferma

async def invia_messaggio(orario, success_flag = False, tipo_conferma = "ok"):
    data_futura = datetime.now() + timedelta(days=7)
    giorno = str(data_futura.day)
    giorni_settimana = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
    giorno_settimana = giorni_settimana[data_futura.weekday()]

    if not success_flag:
        await bot.send_message(
            chat_id=chat_id, 
            text=f"❌ Prenotazione per {giorno_settimana} {giorno} alle {orario} fallita. Controlla i log per dettagli."
        )
    else:
        if tipo_conferma == "lista":
            await bot.send_message(
                chat_id=chat_id, 
                text=f"⚠️ Slot per {giorno_settimana} {giorno} alle {orario} ora non disponibile! Prenotazione effettuata con successo per la lista d'attesa!"
            )
        elif tipo_conferma == "ok":
            await bot.send_message(
                chat_id=chat_id, 
                text=f"✅ Prenotazione completata per {giorno_settimana} {giorno} alle {orario} con successo!"
            )
        

if __name__ == "__main__":
    success_flag, tipo_conferma = prenota("18:15")
    asyncio.run(invia_messaggio("18:15", success_flag, tipo_conferma))

    if tipo_conferma == "lista" and success_flag:
        print("⚠️ Slot non disponibile, prenotazione effettuata per la lista d'attesa!, prova a prenotare alle 19:15")
        success_flag2, tipo_conferma2 = prenota("19:15")
        asyncio.run(invia_messaggio("19:15", success_flag2, tipo_conferma2))
    
