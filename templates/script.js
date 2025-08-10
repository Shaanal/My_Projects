import { getFirestore, collection, addDoc } from "firebase/firestore"; 
import { getAuth } from "firebase/auth";

const db = getFirestore();
const auth = getAuth();

async function saveResult(semester, sgpa, cgpa, subjectData) {
  try {
    const user = auth.currentUser;
    if (!user) return alert("Not logged in");

    await addDoc(collection(db, "results"), {
      uid: user.uid,
      semester,
      sgpa,
      cgpa,
      subjectData, // could be array of subjects with credits and grades
      timestamp: new Date()
    });

    alert("Result saved!");
  } catch (e) {
    console.error("Error saving result", e);
    alert("Failed to save result");
  }
}
