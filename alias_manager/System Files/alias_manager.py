#!/usr/bin/env python3
"""Lookout Alias Manager - name your units from the PC.

Connects to a Lookout router/box over the LAN, loads the current unit-ID -> name table,
lets you edit it in a simple grid, and saves it back. The box picks up the new names
within a few seconds - no restart, no SSH. Standard library only.

Run:  double-click  Start Alias Manager.bat
"""
import json, http.client
import tkinter as tk

PORT          = 8080
DEFAULT_IP    = "192.168.8.1"
DEFAULT_TOKEN = "lookout"

class App:
    def __init__(self, root):
        self.root = root
        root.title("Lookout Alias Manager")
        root.geometry("580x560")

        top = tk.Frame(root, padx=10, pady=10); top.pack(fill="x")
        tk.Label(top, text="Router IP").grid(row=0, column=0, sticky="w")
        self.ip = tk.Entry(top, width=16); self.ip.insert(0, DEFAULT_IP); self.ip.grid(row=0, column=1, padx=6)
        tk.Label(top, text="Token").grid(row=0, column=2, sticky="w")
        self.token = tk.Entry(top, width=12); self.token.insert(0, DEFAULT_TOKEN); self.token.grid(row=0, column=3, padx=6)
        tk.Button(top, text="Load from router", command=self.load).grid(row=0, column=4, padx=4)

        hdr = tk.Frame(root, padx=12); hdr.pack(fill="x")
        tk.Label(hdr, text="Unit ID", width=20, anchor="w", font=("Segoe UI", 9, "bold")).grid(row=0, column=0)
        tk.Label(hdr, text="Name",    width=28, anchor="w", font=("Segoe UI", 9, "bold")).grid(row=0, column=1)

        mid = tk.Frame(root); mid.pack(fill="both", expand=True, padx=12)
        self.canvas = tk.Canvas(mid, highlightthickness=0)
        sb = tk.Scrollbar(mid, orient="vertical", command=self.canvas.yview)
        self.rows_frame = tk.Frame(self.canvas)
        self.rows_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.rows_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side="left", fill="both", expand=True); sb.pack(side="right", fill="y")
        self.rows = []

        bot = tk.Frame(root, padx=10, pady=10); bot.pack(fill="x")
        tk.Button(bot, text="+ Add unit", command=lambda: self.add_row("", "")).pack(side="left")
        tk.Button(bot, text="Save to router", command=self.save, bg="#228B55", fg="white",
                  font=("Segoe UI", 9, "bold")).pack(side="right")
        self.status = tk.Label(root, text="Enter the router IP and click \"Load from router\".",
                               anchor="w", fg="#555", padx=12, pady=4)
        self.status.pack(fill="x")
        self.add_row("", "")

    def add_row(self, uid, name):
        fr = tk.Frame(self.rows_frame)
        e1 = tk.Entry(fr, width=20); e1.insert(0, uid); e1.grid(row=0, column=0, padx=2, pady=2)
        e2 = tk.Entry(fr, width=28); e2.insert(0, name); e2.grid(row=0, column=1, padx=2, pady=2)
        tk.Button(fr, text="–", width=2, command=lambda: self.del_row(fr)).grid(row=0, column=2, padx=4)
        fr.pack(anchor="w")
        self.rows.append((fr, e1, e2))

    def del_row(self, fr):
        self.rows = [r for r in self.rows if r[0] is not fr]
        fr.destroy()

    def clear(self):
        for fr, _, _ in self.rows:
            fr.destroy()
        self.rows = []

    def _conn(self):
        return http.client.HTTPConnection(self.ip.get().strip(), PORT, timeout=6)

    def load(self):
        try:
            c = self._conn()
            c.request("GET", "/admin/aliases?token=" + self.token.get().strip())
            r = c.getresponse(); data = json.loads(r.read() or b"{}")
            if r.status != 200 or not data.get("ok"):
                return self.set_status("Load failed: " + str(data.get("error", r.status)), True)
            al = data.get("aliases", {})
            self.clear()
            for uid, name in sorted(al.items()):
                self.add_row(uid, name)
            if not al:
                self.add_row("", "")
            self.set_status("Loaded %d name(s) from %s." % (len(al), self.ip.get().strip()))
        except Exception as e:
            self.set_status("Could not reach the router: %s" % e, True)

    def save(self):
        out = {}
        for _, e1, e2 in self.rows:
            uid = e1.get().strip()
            if uid:
                out[uid] = e2.get().strip()
        try:
            c = self._conn()
            body = json.dumps(out).encode()
            c.request("POST", "/admin/aliases?token=" + self.token.get().strip(),
                      body=body, headers={"Content-Type": "application/json"})
            r = c.getresponse(); data = json.loads(r.read() or b"{}")
            if r.status != 200 or not data.get("ok"):
                return self.set_status("Save failed: " + str(data.get("error", r.status)), True)
            self.set_status("Saved %s name(s). The map updates within a few seconds." % data.get("count"))
        except Exception as e:
            self.set_status("Could not reach the router: %s" % e, True)

    def set_status(self, msg, err=False):
        self.status.config(text=msg, fg="#c00" if err else "#282")

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
