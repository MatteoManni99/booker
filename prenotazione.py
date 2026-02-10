from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException

import time
import os
from datetime import datetime
from config import ANACLETO_KEY, MY_TELEGRAM_ID, USERNAME, PASSWORD
from telegram import Bot
import asyncio
from datetime import datetime, timedelta
import platform
import logging
from logging.handlers import RotatingFileHandler

# ==================== CONFIGURAZIONE LOGGING ====================
def setup_logging():
    """Configura il sistema di logging con file e console"""
    
    # Crea cartella per i log
    LOG_DIR = "logs"
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        print(f"✓ Cartella '{LOG_DIR}' creata")
    
    # Crea cartella per gli screenshot
    SCREENSHOT_DIR = "screenshots_debug"
    if not os.path.exists(SCREENSHOT_DIR):
        os.makedirs(SCREENSHOT_DIR)
        print(f"✓ Cartella '{SCREENSHOT_DIR}' creata")
    
    # Ottieni il logger
    logger = logging.getLogger("PRENOTA")
    logger.setLevel(logging.DEBUG)
    
    # Formato per i log
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)-8s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler per file con rotazione (max 5MB, max 5 file)
    log_file = os.path.join(LOG_DIR, "prenota.log")
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=5  # Mantiene i 5 file precedenti
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler per errori in file separato
    error_log_file = os.path.join(LOG_DIR, "prenota_errors.log")
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=5*1024*1024,
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    # Handler per console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger, SCREENSHOT_DIR

# Usa il token che ti ha dato BotFather
token = ANACLETO_KEY
chat_id = MY_TELEGRAM_ID
bot = Bot(token=token)

# Setup logging
logger, SCREENSHOT_DIR = setup_logging()

logger.info("=" * 60)
logger.info("AVVIO SCRIPT DI PRENOTAZIONE")
logger.info("=" * 60)

def prenota(orario):
    """
    Effettua la prenotazione per l'orario specificato
    
    Args:
        orario: Stringa dell'orario (es: "18:15")
    
    Returns:
        tuple: (success_flag, tipo_conferma, step)
    """
    success_flag = False
    tipo_conferma = "ok"
    driver = None
    step = "preparazione"
    
    try:
        logger.info(f"Inizio prenotazione per orario: {orario}")
        logger.debug("Configurazione browser...")
        
        # Opzioni Chrome/Chromium
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_argument("--disable-mobile-emulation")
        chrome_options.add_argument("--window-size=1920,1080")

        # Disabilita User-Agent Client Hints che potrebbero forzare mobile
        prefs = {"profile.managed_default_content_settings.images": 1}
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Su Raspberry Pi, usa Chromium
        if "arm" in platform.machine() or "aarch64" in platform.machine():
            logger.info("Rilevato Raspberry Pi - Usando Chromium")
            chrome_options.binary_location = "/usr/bin/chromium-browser"

            # ===== OPZIONI ESSENZIALI PER RASPBERRY PI SENZA SCHERMO =====
            logger.info("Configurazione Chromium in modalità HEADLESS (senza schermo)...")
            
            # Modalità headless - essenziale per RPi senza display
            chrome_options.add_argument("--headless=new")
            
            # Disabilita GPU (RPi non ha GPU dedicated)
            chrome_options.add_argument("--disable-gpu")
            
            # Riduce consumo memoria
            chrome_options.add_argument("--single-process")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-extensions")
            
            # Sandbox disabilitato (spesso causa problemi su RPi)
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-setuid-sandbox")
            
            # Altre opzioni di stabilità
            chrome_options.add_argument("--disable-browser-side-navigation")
            chrome_options.add_argument("--disable-client-side-phishing-detection")
            chrome_options.add_argument("--disable-sync")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")  # Non carica le immagini (risparmia banda)
            chrome_options.add_argument("--disable-mobile-emulation")
            
            logger.info("Opzioni headless configurate")
            
            # Cerca il chromedriver di chromium
            chromedriver_paths = [
                "/usr/bin/chromedriver",
                "/usr/lib/chromium-browser/chromedriver",
                "/snap/bin/chromium"
            ]
            
            chromedriver_path = None
            for path in chromedriver_paths:
                if os.path.exists(path):
                    chromedriver_path = path
                    logger.info(f"Trovato chromedriver: {path}")
                    break
            
            if not chromedriver_path:
                logger.error("Chromedriver non trovato!")
                logger.error("Installa con: sudo apt-get install chromium-chromedriver")
                raise Exception("Chromedriver non trovato su Raspberry Pi")
            
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)

        else:
            logger.debug("Ricerca e download chromedriver...")
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        
        logger.info("Browser pronto")
        step = "browser_pronto"
        
        logger.debug("Step 1: Apertura sito...")
        driver.get("https://ecomm.sportrick.com/REPLYwellnessTO")
        time.sleep(1)
        logger.debug(f"URL attuale: {driver.current_url}")
        
        step = "sito_aperto"
        # Chiudi eventuali popup di cookie o notifiche
        logger.debug("Step 2: Chiusura popup e cookie...")
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
            
            popup_found = False
            for selector in close_selectors:
                try:
                    buttons = driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed():
                            button_text = button.text[:30]
                            button.click()
                            logger.debug(f"Chiuso popup: {button_text}")
                            popup_found = True
                            time.sleep(0.5)
                except:
                    pass
            
            if not popup_found:
                logger.debug("Nessun popup trovato")
        except Exception as e:
            logger.warning(f"Errore durante chiusura popup: {e}")
        
        logger.info("Sito aperto")
        step = "popup_chiuso"

        logger.debug("Step 3: Ricerca campo username...")
        username_field = driver.find_element(By.NAME, "UserName")
        logger.debug("Username field trovato")
        
        logger.debug("Step 4: Ricerca campo password...")
        password_field = driver.find_element(By.NAME, "Password")
        logger.debug("Password field trovato")
        
        logger.debug("Step 5: Inserimento credenziali...")
        username_field.send_keys(USERNAME)
        password_field.send_keys(PASSWORD)
        logger.debug("Credenziali inserite")
        
        logger.debug("Step 6: Ricerca bottone login...")
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        logger.debug("Login button trovato")
        
        logger.debug("Step 7: Click su login...")
        login_button.click()
        time.sleep(1)
        logger.info("Login completato")

        step = "login_completato"
        
        logger.debug("Step 8: Click su Booking...")
        booking_element = driver.find_element(By.ID, "mainmenu-booking")
        booking_element.click()
        time.sleep(0.5)
        logger.debug("Booking cliccato")
        
        logger.debug("Step 9: Click su Nuova Prenotazione...")
        nuova_prenotazione = driver.find_element(By.XPATH, "//span[@class='title' and contains(text(), 'Nuova Prenotazione')]")
        parent = nuova_prenotazione.find_element(By.XPATH, "..")
        parent.click()
        time.sleep(0.5)
        logger.debug("Nuova Prenotazione cliccato")
        
        logger.debug("Step 10: Click su Sala Attrezzi...")
        sala_attrezzi = driver.find_element(By.XPATH, "//h3[@class='list-group-item-heading col-md-10 font-blue-madison' and contains(text(), 'SALA ATTREZZI')]")
        parent = sala_attrezzi.find_element(By.XPATH, "..")
        parent.click()
        time.sleep(0.5)
        logger.debug("Sala Attrezzi cliccato")
        step = "sala_attrezzi_selezionata"
        
        logger.debug("Step 11: Navigazione verso l'orario desiderato...")
        for i in range(5):
            next_button = driver.find_element(By.XPATH, "//i[@class='fa fa-chevron-right']/..")
            next_button.click()
            time.sleep(0.1)
            logger.debug(f"Click {i+1}/5 su '>'")
        logger.debug("Completati i 5 click su '>'")
        
        logger.debug("Attesa caricamento orari disponibili (max 15 secondi)...")

        step = "pagine_giorni_navigate"

        try:
            wait = WebDriverWait(driver, 15)  # Massimo 15 secondi
            wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, "//div[@class='event-slot slot-available']")
            ))
            logger.debug("Orari disponibili caricati ✓")
            step = "orari_disponibili_caricati"
        except Exception as e:
            logger.warning(f"Timeout nell'attesa dei slot disponibili: {e}")
        
        logger.debug(f"Step 12: Ricerca orario '{orario}'...")
        slots = driver.find_elements(By.XPATH, "//div[@class='event-slot slot-available']")
        logger.info(f"Trovati {len(slots)} slot disponibili")
        
        slot_trovato = False
        for slot in reversed(slots):
            try:
                time_start = slot.find_element(By.XPATH, ".//span[@class='time-start']").text
                
                if orario in time_start:
                    logger.info(f"Trovato slot: {time_start}")
                    driver.execute_script("arguments[0].scrollIntoView(true);", slot)
                    time.sleep(0.5)
                    slot.click()
                    slot_trovato = True
                    step = "orario_trovato_e_selezionato"
                    break
            except:
                pass
        
        if not slot_trovato:
            logger.warning(f"Orario {orario} non trovato tra gli slot disponibili")
            step = "orario_non_trovato"
            raise Exception(f"Orario {orario} non trovato")
        
        time.sleep(2)
        logger.info("Orario selezionato")
        
        logger.debug("Step 13: Click su Conferma Prenotazione...")
        try:
            conferma_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Conferma Prenotazione')]")
            if conferma_button.is_displayed():
                conferma_button.click()
                logger.debug("Bottone 'Conferma Prenotazione' cliccato")
            else:
                raise Exception("Bottone 'Conferma Prenotazione' non visibile")
        except NoSuchElementException:
            logger.warning("'Conferma Prenotazione' non trovato, provo con 'Lista'...")
            tipo_conferma = "lista"
            try:
                lista_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Lista')]")
                if lista_button.is_displayed():
                    lista_button.click()
                    logger.debug("Bottone 'Lista' cliccato")
                else:
                    raise Exception("Bottone 'Lista' non visibile")
            except NoSuchElementException:
                logger.error("Ne 'Conferma Prenotazione' e 'Lista' sono disponibili")
                raise Exception("Ne 'Conferma Prenotazione' ne 'Lista' sono disponibili")

        logger.info("Prenotazione confermata")
        step = "prenotazione_confermata"

        time.sleep(1)
        logger.debug("Step 14: Click su No...")
        try:
            no_button = driver.find_element(By.XPATH, "//button[contains(text(), 'No')]")
            if no_button.is_displayed():
                no_button.click()
                logger.debug("Bottone 'No' cliccato")
        except NoSuchElementException:
            logger.warning("'No' non trovato, provo con 'Ok'...")
            tipo_conferma = "lista"
            try:
                ok_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Ok')]")
                if ok_button.is_displayed():
                    ok_button.click()
                    logger.debug("Bottone 'Ok' cliccato")
                else:
                    raise Exception("Bottone 'Ok' non visibile")
            except NoSuchElementException:
                logger.error("Ne 'No' ne 'Ok' sono disponibili")
                raise Exception("Ne 'No' ne 'Ok' sono disponibili")
        
        time.sleep(0.5)
        logger.info("✓ Prenotazione completata con successo!")
        success_flag = True
        step = "procedura_completata"
        
    except Exception as e:
        logger.error(f"ERRORE: {type(e).__name__}: {e}", exc_info=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if driver:
            try:
                screenshot_path = os.path.join(SCREENSHOT_DIR, f"ERRORE_{timestamp}.png")
                driver.save_screenshot(screenshot_path)
                logger.error(f"Screenshot salvato: {screenshot_path}")
            except Exception as screenshot_error:
                logger.error(f"Impossibile salvare screenshot: {screenshot_error}")
        
        success_flag = False
        
    finally:
        if driver:
            try:
                driver.quit()
                logger.debug("Driver chiuso")
            except Exception as e:
                logger.error(f"Errore durante chiusura driver: {e}")
        
        logger.info(f"Fine prenotazione - Successo: {success_flag}, Tipo: {tipo_conferma}", extra={"step": step})
        return success_flag, tipo_conferma, step

async def invia_messaggio(orario, success_flag=False, tipo_conferma="ok", step="sconosciuto"):
    """
    Invia messaggio Telegram con il risultato della prenotazione
    
    Args:
        orario: Orario della prenotazione
        success_flag: Se la prenotazione è andata a buon fine
        tipo_conferma: Tipo di conferma ('ok' o 'lista')
        step: Step corrente della procedura
    """
    logger.info(f"Invio messaggio Telegram per orario {orario}...", extra={"step": step})
    
    data_futura = datetime.now() + timedelta(days=7)
    giorno = str(data_futura.day)
    giorni_settimana = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
    giorno_settimana = giorni_settimana[data_futura.weekday()]

    try:
        if not success_flag:
            messaggio = f"❌ Prenotazione per {giorno_settimana} {giorno} alle {orario} fallita. Controlla i log per dettagli. Step: {step}"
            await bot.send_message(chat_id=chat_id, text=messaggio)
            logger.warning(f"Messaggio fallimento inviato: {messaggio}", extra={"step": step})
        else:
            if tipo_conferma == "lista":
                messaggio = f"⚠️ Slot per {giorno_settimana} {giorno} alle {orario} ora non disponibile! Prenotazione effettuata con successo per la lista d'attesa! Step: {step}"
                await bot.send_message(chat_id=chat_id, text=messaggio)
                logger.warning(f"Messaggio lista d'attesa inviato: {messaggio}", extra={"step": step})
            elif tipo_conferma == "ok":
                messaggio = f"✅ Prenotazione completata per {giorno_settimana} {giorno} alle {orario} con successo! Step: {step}"
                await bot.send_message(chat_id=chat_id, text=messaggio)
                logger.info(f"Messaggio successo inviato: {messaggio}", extra={"step": step})
    except Exception as e:
        logger.error(f"Errore nell'invio messaggio Telegram: {e}", exc_info=True)

async def main():
    """Funzione principale"""
    logger.info("INIZIO PROCEDURA PRENOTAZIONE")
    
    try:
        # Primo tentativo: 18:15
        logger.info("Tentativo 1: Prenotazione per le 18:15")
        success_flag, tipo_conferma, step = prenota("18:15")
        await invia_messaggio("18:15", success_flag, tipo_conferma, step)
        
        # Se non disponibile, prova 19:15
        if tipo_conferma == "lista" and success_flag:
            logger.warning("Slot 18:15 non disponibile, prenotazione in lista d'attesa. Tentativo per le 19:15...")
            success_flag2, tipo_conferma2, step = prenota("19:15")
            await invia_messaggio("19:15", success_flag2, tipo_conferma2, step)
        
        logger.info("=" * 60)
        logger.info("PROCEDURA COMPLETATA")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Errore critico nella procedura principale: {e}", exc_info=True)
        await invia_messaggio("SCONOSCIUTO", False, "errore", "errore_critico")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Script interrotto dall'utente")
    except Exception as e:
        logger.error(f"Errore nell'esecuzione dello script: {e}", exc_info=True)
    finally:
        logger.info("Script terminato")