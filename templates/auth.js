import { initializeApp } from "https://www.gstatic.com/firebasejs/10.11.0/firebase-app.js";
import { getAuth, signInWithEmailAndPassword, createUserWithEmailAndPassword, signInWithPopup, GoogleAuthProvider } from "https://www.gstatic.com/firebasejs/10.11.0/firebase-auth.js";

const firebaseConfig = {
  apiKey: "AIzaSyDdTDr0QWem0XqGisJ2nXTYibFCsJd3Xxw",
  authDomain: "cgcalc-7af1d.firebaseapp.com",
  databaseURL: "https://cgcalc-7af1d-default-rtdb.asia-southeast1.firebasedatabase.app",
  projectId: "cgcalc-7af1d",
  storageBucket: "cgcalc-7af1d.firebasestorage.app",
  messagingSenderId: "875151617453",
  appId: "1:875151617453:web:eb10d21e52008840974524"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

window.emailLogin = () => {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  signInWithEmailAndPassword(auth, email, password)
    .then(() => {
        alert("Login successful");
        window.location.href = "home.html";
    })
    .catch(err => alert(err.message));
};

window.googleLogin = function () {
  signInWithPopup(auth, provider)
    .then((result) => {
        alert("Login with Google successful");
        window.location.href = "home.html";
    })
    .catch(err => alert(err.message));
};

window.signup = () => {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  createUserWithEmailAndPassword(auth, email, password)
    .then(() => window.location.href = "home.html")
    .catch(e => alert(e.message));
};
