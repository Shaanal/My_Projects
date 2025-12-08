# MyCGCalc — CGPA & SGPA Calculator with Login + Saved History  
A full-stack academic calculator web application built using **Supabase**, **TailwindCSS**, and **Netlify**.

MyCGCalc allows students to compute **SGPA**, **CGPA**, **Required SGPA**, and **Course Grade totals**, while offering **user authentication** and **persistent history storage**. Users can log in via **email/password** or **Google**, save all calculations, view them in a sleek sliding history drawer, reload saved data, and delete history.

---

## Features

### Academic Calculators  
- **SGPA Calculator**
  - Add/remove subjects dynamically  
  - Grade → Grade-point mapping  
  - Computes weighted SGPA  
  - Saves complete subject list to history  

- **CGPA Calculator**
  - Uses previous CGPA + credits + current SGPA  
  - Computes updated cumulative CGPA  
  - Stores input + computed CGPA  

- **Required SGPA Calculator**
  - Computes SGPA needed to reach a target CGPA  
  - Saves all relevant values  

- **Course Grade Estimator**
  - Calculates weighted score using quizzes, midsem, endsem, project, assignments  
  - Stores full detailed breakdown  

---

## Authentication (Supabase Auth)

- Email + Password login  
- Google OAuth login  
- Auto-redirect protection:
  - If not logged in → redirect to `login.html`
  - If logged in → access `home.html`  
- Supabase session handling  
- Logout instantly clears session  

---

## Database (Supabase Postgres)

### Table: `history`

| Column        | Type      | Description |
|---------------|-----------|-------------|
| `id`          | UUID (PK) | Auto-generated unique ID |
| `user_id`     | UUID      | Linked to authenticated user |
| `type`        | TEXT      | SGPA / CGPA / Required_SGPA / Course_Grade |
| `data`        | JSONB     | Full calculation details |
| `created_at`  | TIMESTAMP | Auto timestamp |

### Row-Level Security Policies  
Allows users to only read/delete their own data:

```sql
-- SELECT
(user_id = auth.uid())

-- INSERT
(user_id = auth.uid())

-- DELETE
(user_id = auth.uid())
```

## History Drawer (Right-Side Panel)

A smooth sliding UI that allows users to view and manage their saved history.

### Includes:
- **Open History** button  
- **Close Drawer** button  
- **Delete Single Entry**  
- **Clear All History**  
- **Load Data Back Into Calculator**  
- **Timestamp formatting**  
- **Pretty JSON formatting**  

When a user loads an entry, the stored values automatically populate into the correct calculator fields.

---

## Tech Stack

### **Frontend**
- HTML5  
- TailwindCSS  
- Vanilla JavaScript  
- Dynamic DOM manipulation  
- Drawer-style history UI  
- Toast notifications for user feedback  

### **Backend**
- Supabase Auth (Email + Google OAuth)  
- Supabase Database (Postgres + JSONB)  
- RLS (Row-Level Security) policies for secure, user-specific data  

### **Deployment**
- Hosted using **Netlify**  
- Connected to **GitHub repo** for auto-deployment  
- Supabase fully handles backend hosting  

---

## Project Structure

```
mycgcalc/
│
├── login.html
├── signup.html
└── home.html
```

---

## Important Configuration

### **Supabase Auth Redirect URLs**
https://mycgcalcmeshaa.netlify.app/home.html


### **Google OAuth Callback**
https://jswfahpezxgkcezfczio.supabase.co/auth/v1/callback


---

## Deployment Notes

- Netlify automatically rebuilds from GitHub whenever you push changes  
- No backend server is required  
- Supabase handles authentication + database  
- Only frontend HTML/JS needs to be updated  

---


## Final Summary

**MyCGCalc** is a fully functional, production-style academic calculator web application featuring:

✔ Multiple academic calculators (SGPA, CGPA, Required SGPA, Course Grade)  
✔ Email + Google authentication  
✔ Persistent user history stored in Supabase  
✔ Ability to load past results into calculators  
✔ Clean UI with TailwindCSS  
✔ Cloud-hosted backend  
✔ Live deployment on Netlify  


---

