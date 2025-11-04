import tkinter as tk
from tkinter import messagebox
import time
import random
import json
import os
import requests

# === CONFIGURATION ===
GOOGLE_DRIVE_FILE_ID = "1LDEy5ERl0jmGywHrArtUVnBrv4aSvSPw"
LEADERBOARD_URL = f"https://drive.google.com/uc?export=download&id={GOOGLE_DRIVE_FILE_ID}"
LOCAL_LEADERBOARD_FILE = "leaderboard.json"

def preload_leaderboard(progress_label):
    progress_label.config(text="Checking for local leaderboard...")
    if os.path.exists(LOCAL_LEADERBOARD_FILE):
        progress_label.config(text="Local leaderboard found. Skipping download.")
        return
    try:
        progress_label.config(text="Downloading leaderboard from Google Drive...")
        response = requests.get(LEADERBOARD_URL, timeout=5)
        if response.status_code == 200:
            leaderboard = json.loads(response.content.decode("utf-8"))
            with open(LOCAL_LEADERBOARD_FILE, "w") as f:
                json.dump(leaderboard, f)
            progress_label.config(text="Leaderboard downloaded and saved.")
        else:
            progress_label.config(text=f"Failed to fetch leaderboard: {response.status_code}")
    except Exception as e:
        progress_label.config(text=f"Error downloading leaderboard: {e}")

def show_splash():
    splash = tk.Tk()
    splash.title("Loading...")
    splash.geometry("350x200")
    splash.configure(bg="#1e272e")

    label = tk.Label(splash, text="⚡ Reaction Time Game", font=("Verdana", 16), fg="white", bg="#1e272e")
    label.pack(pady=20)

    progress_label = tk.Label(splash, text="", font=("Verdana", 10), fg="#fbc531", bg="#1e272e")
    progress_label.pack()

    splash.after(100, lambda: preload_leaderboard(progress_label))
    splash.after(2500, splash.destroy)
    splash.mainloop()

class ReactionGame:
    def __init__(self, root):
        self.root = root
        self.root.title("⚡ Reaction Time Game")
        self.root.geometry("500x400")
        self.root.configure(bg="#1e272e")

        self.label = tk.Label(root, text="Click 'Start' to begin!", font=("Verdana", 18), fg="white", bg="#1e272e")
        self.label.pack(pady=30)

        self.feedback_label = tk.Label(root, text="", font=("Verdana", 12), fg="white", bg="#1e272e")
        self.feedback_label.pack()

        self.start_button = tk.Button(root, text="Start", font=("Verdana", 14), command=self.start_game, bg="#0be881", fg="black", width=15)
        self.start_button.pack(pady=10)

        #TODO: (This is for the "Retry" button in the main window)
        # self.retry_button = tk.Button(root, text="Retry", font=("Verdana", 12), command=self.start_game, bg="#fbc531", fg="black", width=15)
        # self.retry_button.pack(pady=5)
        # self.retry_button.pack_forget()

        self.leaderboard_button = tk.Button(root, text="Leaderboard", font=("Verdana", 12), command=self.show_leaderboard, bg="#00a8ff", fg="white", width=15)
        self.leaderboard_button.pack(pady=5)

        #TODO: (This is for the "Reset" button in the main window)
        # self.reset_button = tk.Button(root, text="Reset Leaderboard", font=("Verdana", 10), command=self.reset_leaderboard, bg="#ff3f34", fg="white", width=15)
        # self.reset_button.pack(pady=5)

        self.root.bind("<Return>", self.react)
        self.waiting = False
        self.start_time = None

    def start_game(self):
        self.label.config(text="Wait for it...", fg="white")
        self.feedback_label.config(text="")
        self.start_button.config(state="disabled")
        #TODO: (Part of the main window "Retry" button)
        # self.retry_button.pack_forget()
        delay = random.randint(2000, 5000)
        self.root.after(delay, self.trigger_reaction)

    def trigger_reaction(self):
        self.label.config(text="NOW! Press Enter!", fg="#ff3f34")
        self.start_time = time.time()
        self.waiting = True

    def react(self, event):
        if self.waiting:
            reaction_time = round((time.time() - self.start_time) * 1000, 2)
            avg = self.get_average_score()
            self.waiting = False
            self.start_button.config(state="normal")
            #TODO: (Part of the main window "Retry" button)
            # self.retry_button.pack()

            # Color-coded feedback
            if avg:
                if reaction_time < avg:
                    color = "#0be881"
                    feedback = f"🔥 Above average! ({avg} ms)"
                elif reaction_time <= avg + 50:
                    color = "#fbc531"
                    feedback = f"⚖️ Near average ({avg} ms)"
                else:
                    color = "#ff3f34"
                    feedback = f"⏱️ Below average ({avg} ms)"
            else:
                color = "#ffffff"
                feedback = ""

            self.label.config(text=f"Your time: {reaction_time} ms", fg=color)
            self.feedback_label.config(text=feedback, fg=color)
            self.save_score(reaction_time)
        else:
            self.label.config(text="Too soon! Wait for the signal.", fg="#f1c40f")

    def get_average_score(self):
        leaderboard = self.load_leaderboard()
        if not leaderboard:
            return None
        scores = [entry["score"] for entry in leaderboard]
        return round(sum(scores) / len(scores), 2)

    def load_leaderboard(self):
        if os.path.exists(LOCAL_LEADERBOARD_FILE):
            with open(LOCAL_LEADERBOARD_FILE, "r") as f:
                return json.load(f)
        return []
    
    def reset_leaderboard(self):
        if os.path.exists(LOCAL_LEADERBOARD_FILE):
            os.remove(LOCAL_LEADERBOARD_FILE)
            messagebox.showinfo("Reset", "Leaderboard has been cleared.")
        else:
            messagebox.showinfo("Reset", "No leaderboard file found.")
        self.show_leaderboard()  # Reopen leaderboard to reflect changes



    def save_score(self, score):
        name = self.ask_name()
        if name == "__RETRY__":
            self.start_game()
            return
        if not name:
            return
        leaderboard = self.load_leaderboard()
        leaderboard.append({"name": name, "score": score})
        leaderboard.sort(key=lambda x: x["score"])
        leaderboard = leaderboard[:10]
        with open(LOCAL_LEADERBOARD_FILE, "w") as f:
            json.dump(leaderboard, f)
        self.show_leaderboard()



    def ask_name(self):
        popup = tk.Toplevel(self.root)
        popup.title("Enter Name or Retry")
        popup.geometry("300x200")
        popup.configure(bg="#1e272e")

        label = tk.Label(popup, text="Enter your name:", font=("Verdana", 12), bg="#1e272e", fg="white")
        label.pack(pady=10)

        entry = tk.Entry(popup, font=("Verdana", 12))
        entry.pack(pady=5)

        result = []

        def submit():
            result.append(entry.get())
            popup.destroy()

        def retry():
            result.append("__RETRY__")
            popup.destroy()

        submit_btn = tk.Button(popup, text="Submit", command=submit, font=("Verdana", 10), bg="#0be881", fg="black")
        submit_btn.pack(pady=5)

        retry_btn = tk.Button(popup, text="Retry", command=retry, font=("Verdana", 10), bg="#fbc531", fg="black")
        retry_btn.pack(pady=5)

        popup.grab_set()
        popup.wait_window()
        return result[0] if result else None
    
    def refresh_leaderboard(self):
        try:
            response = requests.get(LEADERBOARD_URL, timeout=5)
            if response.status_code == 200:
                leaderboard = json.loads(response.content.decode("utf-8"))
                with open(LOCAL_LEADERBOARD_FILE, "w") as f:
                    json.dump(leaderboard, f)
                self.show_leaderboard()
            else:
                messagebox.showerror("Error", f"Failed to fetch leaderboard: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Error", f"Error downloading leaderboard: {e}")




    def show_leaderboard(self):
        leaderboard = self.load_leaderboard()
        if not leaderboard:
            messagebox.showinfo("Leaderboard", "No scores yet!")
            return

        top = tk.Toplevel(self.root)
        top.title("🏆 Leaderboard")
        top.geometry("320x500")
        top.configure(bg="#2f3640")

        title = tk.Label(top, text="Top Reaction Times", font=("Verdana", 16), bg="#2f3640", fg="white")
        title.pack(pady=10)

        # Container for scrollable leaderboard
        container = tk.Frame(top, bg="#2f3640")
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg="#2f3640", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#2f3640")

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Stats for color coding
        scores = [entry["score"] for entry in leaderboard]
        avg_score = round(sum(scores) / len(scores), 2)
        best_score = min(scores)

        for i, entry in enumerate(leaderboard):
            score = entry["score"]
            name = entry["name"]

            if score == best_score:
                fg = "#ffd700"  # gold
                font = ("Verdana", 12, "bold")
            elif score < avg_score:
                fg = "#0be881"  # green
                font = ("Verdana", 12)
            elif score <= avg_score + 50:
                fg = "#f39c12"  # orange
                font = ("Verdana", 12)
            else:
                fg = "#ff3f34"  # red
                font = ("Verdana", 12)

            rank = f"{i+1}. {name} - {score} ms"
            label = tk.Label(scroll_frame, text=rank, font=font, bg="#2f3640", fg=fg, anchor="w")
            label.pack(fill="x", padx=10, pady=5)

        # Reset button below leaderboard
        reset_btn = tk.Button(top, text="Reset Leaderboard", font=("Verdana", 10), command=self.reset_leaderboard, bg="#ff3f34", fg="white")
        reset_btn.pack(pady=10)
        
        refresh_btn = tk.Button(top, text="Refresh Leaderboard (Download new version)", font=("Verdana", 10), command=self.refresh_leaderboard, bg="#00a8ff", fg="white")
        refresh_btn.pack(pady=5)




if __name__ == "__main__":
    show_splash()
    root = tk.Tk()
    app = ReactionGame(root)
    root.mainloop()

