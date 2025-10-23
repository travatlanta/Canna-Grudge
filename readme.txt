CannaGrudge • Firebase Auth (GitHub Pages friendly)
===================================================

FILES
-----
- firebase-config.js   : Initializes Firebase Auth with your real config.
- login.html           : Google/Facebook/Apple buttons using Firebase Auth.
- dashboard.html       : Protected page that only renders for signed-in users.

USAGE
-----
1) Commit these files to your GitHub repo (e.g. in the root).
2) In Firebase Console:
   - Build -> Authentication -> Sign-in method:
     Enable Google (start with this), optionally Facebook and Apple later.
   - Authentication -> Settings -> Authorized domains:
     Add: localhost, 127.0.0.1, yourusername.github.io, cannagrudge.com, www.cannagrudge.com
3) Local test:
   - Serve the folder with any static server (python -m http.server 8000) and open /login.html
   - Click "Continue with Google".
   - After login you'll land at /dashboard.html showing your name/email.
4) GitHub Pages:
   - Enable Pages for the repo and open https://yourusername.github.io/<repo>/login.html
   - If your repo is a PROJECT page, the path includes the repo name. The code uses relative paths so it works under a subfolder.

NOTES
-----
- Facebook/Apple buttons require provider setup in Firebase before they work.
- Do not mix the old localStorage "auth". Firebase Auth state is the source of truth.
