import {
  signInWithEmailAndPassword,
  signOut,
  type User as FirebaseUser,
} from "firebase/auth";
import { auth } from "../firebase";
import api from "../api";

export interface AppUser {
  username: string;
  role: string;
  team_id?: string;
  team_name?: string;
  email?: string;
}

export function saveSession(accessToken: string, user: AppUser) {
  localStorage.setItem("bingo_token", accessToken);
  localStorage.setItem("bingo_user", JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem("bingo_token");
  localStorage.removeItem("bingo_user");
}

export function getStoredUser(): AppUser | null {
  const raw = localStorage.getItem("bingo_user");
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AppUser;
  } catch {
    return null;
  }
}

async function syncFirebaseUser(idToken: string, teamName?: string) {
  const response = await api.post("/api/auth/firebase", {
    id_token: idToken,
    team_name: teamName,
  });
  return response.data as {
    access_token: string;
    role: string;
    team_id?: string;
    team_name?: string;
    username: string;
  };
}

export async function firebaseSignUp(
  email: string,
  password: string,
  teamName: string
) {
  const response = await api.post("/api/auth/register", {
    email: email.trim(),
    password,
    team_name: teamName.trim(),
  });
  const data = response.data as {
    access_token: string;
    role: string;
    team_id?: string;
    team_name?: string;
    username: string;
  };

  saveSession(data.access_token, {
    username: data.username,
    role: data.role,
    team_id: data.team_id,
    team_name: data.team_name,
    email,
  });

  return data;
}

export async function firebaseSignIn(email: string, password: string) {
  const credential = await signInWithEmailAndPassword(auth, email, password);
  const idToken = await credential.user.getIdToken(true);
  const data = await syncFirebaseUser(idToken);

  saveSession(data.access_token, {
    username: data.username,
    role: data.role,
    team_id: data.team_id,
    team_name: data.team_name,
    email,
  });

  return data;
}

export async function tournamentLogin(username: string, password: string) {
  const response = await api.post("/api/auth/login", {
    username: username.trim(),
    password: password.trim(),
  });

  const { access_token, role, team_id, team_name } = response.data;
  saveSession(access_token, { username, role, team_id, team_name });
  return response.data;
}

export async function logout() {
  try {
    await api.post("/api/auth/logout");
  } catch {
    // Session may already be invalid
  }

  clearSession();

  if (auth.currentUser) {
    await signOut(auth);
  }
}

export async function restoreFirebaseSession(firebaseUser: FirebaseUser) {
  if (localStorage.getItem("bingo_token")) return;

  const idToken = await firebaseUser.getIdToken(true);
  const data = await syncFirebaseUser(idToken);

  saveSession(data.access_token, {
    username: data.username,
    role: data.role,
    team_id: data.team_id,
    team_name: data.team_name,
    email: firebaseUser.email ?? undefined,
  });
}
