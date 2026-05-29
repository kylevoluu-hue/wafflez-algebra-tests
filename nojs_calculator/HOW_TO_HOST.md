# How to use the No-JavaScript calculator

This calculator does all the math on a **server** and sends back a plain
HTML page. Your Chromebook only shows a form and the answer, so it works
even when JavaScript is blocked by your school.

There's one catch worth saying plainly: **the calculator has to be running
somewhere.** You can't just open `app.py` like a file — a server has to run
it. Below are your options, easiest first.

---

## Option 1 (recommended): Host it free on PythonAnywhere

You only have to set this up **once**, ideally from a normal computer or
phone at home (the setup pages use JavaScript). After that, you visit the
finished web address from your school Chromebook and it works with **no
JavaScript** needed.

1. Go to **https://www.pythonanywhere.com** and make a **free** account.
2. On the dashboard, open the **Web** tab → **Add a new web app** →
   **Flask** → **Python 3.10** (any 3.x is fine).
3. It creates a file like `/home/YOURNAME/mysite/flask_app.py`.
   Open it in the **Files** tab, delete everything, and paste in the entire
   contents of **`app.py`** from this folder.
4. Open a **Bash console** (Consoles tab) and install the libraries:
   ```
   pip install --user flask sympy
   ```
5. Back on the **Web** tab, press the big green **Reload** button.
6. Your calculator is now live at:
   ```
   https://YOURNAME.pythonanywhere.com
   ```
   Bookmark that on your Chromebook. Done — no JavaScript required.

---

## Option 2: Run it on your own computer (same Wi-Fi)

If you have a Windows/Mac computer on the same network as the Chromebook:

1. Install Python, then in a terminal:
   ```
   pip install flask sympy
   python3 app.py
   ```
2. Find that computer's local IP (e.g. `192.168.1.20`).
3. On the Chromebook, visit `http://192.168.1.20:5000`.
   (Both devices must be on the same Wi-Fi.)

---

## Option 3: Other free hosts

The same `app.py` also runs on Render.com, Railway.app, or Replit.
Each gives you a public `https://...` URL you can open from the Chromebook.
A `requirements.txt` is included in this folder for them.

---

## Why there is no "just open the file" version

A web page can only *calculate* using a programming language. In a browser
that language is JavaScript — there is no other option built in. Pure
HTML/CSS can show buttons but can't do algebra. So with JavaScript blocked,
the only way to get real answers is to compute them on a server and send
back plain HTML, which is exactly what this app does.
