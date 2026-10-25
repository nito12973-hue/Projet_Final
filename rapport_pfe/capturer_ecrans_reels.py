from playwright.sync_api import sync_playwright
import os
import time

out_dir = r"c:\Users\nito1\Desktop\Projet_Final\rapport_pfe\illustrations_isep"
os.makedirs(out_dir, exist_ok=True)

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
base_url = "https://projet-final-bice.vercel.app"

print("Démarrage de la capture d'écrans réels sur SantéSN...")

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=chrome_path, headless=True)
    
    # 1. Landing Page / Accueil Public
    context = browser.new_context(viewport={'width': 1280, 'height': 820})
    page = context.new_page()
    page.goto(base_url, timeout=40000)
    page.wait_for_timeout(2000)
    p34 = os.path.join(out_dir, "fig_34_capture_accueil_login.png")
    page.screenshot(path=p34)
    print("Capture 1 réussie : Accueil public ->", p34)
    
    # 2. Espace Assuré (avec carte ISO 7810 et jauge de plafond)
    page.goto(f"{base_url}/connexion/", timeout=40000)
    page.wait_for_timeout(1000)
    page.fill("input[name='email']", "assure@santesn.sn")
    page.fill("input[name='password']", "Passer123!")
    page.click("button[type='submit']")
    page.wait_for_timeout(4000)
    print("URL après login Assuré:", page.url)
    
    p35 = os.path.join(out_dir, "fig_35_capture_espace_assure.png")
    page.screenshot(path=p35)
    print("Capture 2 réussie : Espace Assuré ->", p35)
    context.close()

    # 3. Espace Médecin
    context_med = browser.new_context(viewport={'width': 1280, 'height': 820})
    page_med = context_med.new_page()
    page_med.goto(f"{base_url}/connexion/", timeout=40000)
    page_med.wait_for_timeout(1000)
    page_med.fill("input[name='email']", "lama@gmail.com")
    page_med.fill("input[name='password']", "Passer123!")
    page_med.click("button[type='submit']")
    page_med.wait_for_timeout(4000)
    print("URL après login Médecin:", page_med.url)
    
    p36 = os.path.join(out_dir, "fig_36_capture_espace_medecin.png")
    page_med.screenshot(path=p36)
    print("Capture 3 réussie : Espace Médecin ->", p36)
    context_med.close()

    # 4. Espace Gestionnaire (Cartographie Leaflet & Conventions)
    context_gest = browser.new_context(viewport={'width': 1280, 'height': 820})
    page_gest = context_gest.new_page()
    page_gest.goto(f"{base_url}/connexion/", timeout=40000)
    page_gest.wait_for_timeout(1000)
    page_gest.fill("input[name='email']", "nito12973@gmail.com")
    page_gest.fill("input[name='password']", "Passer123!")
    page_gest.click("button[type='submit']")
    page_gest.wait_for_timeout(4000)
    print("URL après login Gestionnaire:", page_gest.url)
    
    p38 = os.path.join(out_dir, "fig_38_capture_espace_gestionnaire.png")
    page_gest.screenshot(path=p38)
    print("Capture 4 réussie : Espace Gestionnaire ->", p38)
    
    # Navigation vers prestataires cartographie
    try:
        page_gest.goto(f"{base_url}/prestataires/", timeout=25000)
        page_gest.wait_for_timeout(3000)
        p_map = os.path.join(out_dir, "fig_38b_cartographie_leaflet_reelle.png")
        page_gest.screenshot(path=p_map)
        print("Capture cartographie Leaflet réussie ->", p_map)
    except Exception as e:
        print("Erreur prestataires map:", e)
        
    context_gest.close()

    browser.close()
    print("Toutes les captures d'écran réelles ont été saisies avec succès !")
