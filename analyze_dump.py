from bs4 import BeautifulSoup
import re

def analyze():
    with open("debug_notebooklm_structure.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    soup = BeautifulSoup(html, "html.parser")
    
    print("--- SEARCHING FOR CREATE YOUR OWN ---")
    create_own = soup.find_all(string=re.compile("Create Your Own", re.I))
    for res in create_own:
        parent = res.parent
        print(f"Found match: '{res}'")
        print(f"Parent tag: {parent.name}, classes: {parent.get('class')}")
        # Go up 3 levels
        curr = parent
        for i in range(3):
            if curr.parent:
                curr = curr.parent
                print(f"Level {i+1} parent: {curr.name}, classes: {curr.get('class')}, attrs: {curr.attrs}")

    print("\n--- SEARCHING FOR TEXTAREAS ---")
    textareas = soup.find_all("textarea")
    for t in textareas:
        print(f"Textarea: placeholder='{t.get('placeholder')}', class='{t.get('class')}'")

    print("\n--- SEARCHING FOR CONTENTEDITABLE ---")
    editables = soup.find_all(attrs={"contenteditable": True})
    for e in editables:
        print(f"Editable: role='{e.get('role')}', placeholder='{e.get('placeholder')}', class='{e.get('class')}'")

if __name__ == "__main__":
    analyze()
