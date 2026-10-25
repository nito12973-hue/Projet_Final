from playwright.sync_api import sync_playwright
import os

out_dir = r"c:\Users\nito1\Desktop\Projet_Final\rapport_pfe\illustrations_isep"
chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
base_url = "https://projet-final-bice.vercel.app"

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=chrome_path, headless=True)
    
    # 1. Pharmacien
    ctx_pharma = browser.new_context(viewport={'width': 1280, 'height': 820})
    page_pharma = ctx_pharma.new_page()
    page_pharma.goto(f"{base_url}/connexion/", timeout=40000)
    page_pharma.fill("input[name='email']", "pharmacien@santesn.sn")
    page_pharma.fill("input[name='password']", "Passer123!")
    page_pharma.click("button[type='submit']")
    page_pharma.wait_for_timeout(4000)
    p37 = os.path.join(out_dir, "fig_37_capture_espace_pharmacien.png")
    page_pharma.screenshot(path=p37)
    print("Capture Pharmacien réussie :", p37)
    ctx_pharma.close()
    
    # 2. Admin
    ctx_admin = browser.new_context(viewport={'width': 1280, 'height': 820})
    page_admin = ctx_admin.new_page()
    page_admin.goto(f"{base_url}/connexion/", timeout=40000)
    page_admin.fill("input[name='email']", "lamaranamamadousdiallo@gmail.com")
    page_admin.fill("input[name='password']", "Passer123!")
    page_admin.click("button[type='submit']")
    page_admin.wait_for_timeout(4000)
    p39 = os.path.join(out_dir, "fig_39_capture_supervision_admin.png")
    page_admin.screenshot(path=p39)
    print("Capture Admin réussie :", p39)
    ctx_admin.close()

    browser.close()
    print("Toutes les captures complémentaires sont terminées !")
