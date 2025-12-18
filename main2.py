from __future__ import annotations
from typing import Dict, Set
import tkinter as tk
from tkinter import ttk, messagebox
import re

# -------------------------------------------------
#  LOGJIKA E BASHKËSIVE
# -------------------------------------------------
def parse_set_input(raw: str) -> Set[str]:
    raw = raw.replace("{", "").replace("}", "")
    return set(x.strip() for x in raw.replace(",", " ").split() if x.strip())


def evaluate_expression(expr: str, sets: Dict[str, Set[str]]) -> Set[str]:
    """
    Shndërron shprehje si:
    A ∪ (B \ A)
    në operacione Python me set()
    """
    expr = expr.replace("∪", "|")
    expr = expr.replace("∩", "&")
    expr = expr.replace("\\", "-")
    expr = expr.replace("Δ", "^")

    for k in sets:
        expr = re.sub(rf"\b{k}\b", f"sets['{k}']", expr)

    try:
        return eval(expr)
    except Exception as e:
        raise ValueError(f"Gabim në shprehje: {e}")


# -------------------------------------------------
#  GUI APP
# -------------------------------------------------
class SetApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Projekt inteligjent për bashkësi – Expression Builder")
        self.root.geometry("1000x650")

        self.num_sets_var = tk.IntVar(value=2)
        self.expr_var = tk.StringVar()

        self.set_entries: Dict[str, tk.Entry] = {}
        self.current_sets: Dict[str, Set[str]] = {}

        self.build_ui()

    # -------------------------------------------------
    def build_ui(self):
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Numri i bashkësive:").pack(side=tk.LEFT)
        cb = ttk.Combobox(
            top, values=[2, 3, 4],
            textvariable=self.num_sets_var,
            state="readonly", width=5
        )
        cb.pack(side=tk.LEFT, padx=5)
        cb.bind("<<ComboboxSelected>>", lambda e: self.build_sets())

        self.sets_frame = ttk.LabelFrame(self.root, text="Bashkësitë", padding=10)
        self.sets_frame.pack(fill=tk.X, padx=10)

        self.ops_frame = ttk.LabelFrame(self.root, text="Ndërtimi i shprehjes", padding=10)
        self.ops_frame.pack(fill=tk.X, padx=10, pady=5)

        self.output = tk.Text(self.root, height=18)
        self.output.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.build_sets()
        self.build_expression_builder()

        ttk.Button(self.root, text="Llogarit", command=self.compute).pack(pady=5)

    # -------------------------------------------------
    def build_sets(self):
        for w in self.sets_frame.winfo_children():
            w.destroy()

        self.set_entries.clear()
        labels = ["A", "B", "C", "D"][:self.num_sets_var.get()]

        for lab in labels:
            row = ttk.Frame(self.sets_frame)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=f"{lab} =").pack(side=tk.LEFT)
            e = ttk.Entry(row)
            e.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            self.set_entries[lab] = e

        self.build_expression_builder()

    # -------------------------------------------------
    def build_expression_builder(self):
        for w in self.ops_frame.winfo_children():
            w.destroy()

        labels = list(self.set_entries.keys())

        # --- Buttons A B C D
        btns = ttk.Frame(self.ops_frame)
        btns.pack(anchor=tk.W)

        for lab in labels:
            ttk.Button(btns, text=lab,
                       command=lambda l=lab: self.add_expr(l)
                       ).pack(side=tk.LEFT, padx=4)

        # --- Operator checkboxes (si foto)
        ops = ttk.Frame(self.ops_frame)
        ops.pack(anchor=tk.W, pady=5)

        self.op_buttons = {
            "∪": " ∪ ",
            "∩": " ∩ ",
            "\\": " \\ ",
            "Δ": " Δ "
        }

        for sym, val in self.op_buttons.items():
            ttk.Button(
                ops, text=sym,
                command=lambda v=val: self.add_expr(v)
            ).pack(side=tk.LEFT, padx=6)

        # --- Parentheses
        ttk.Button(ops, text="(", command=lambda: self.add_expr("(")).pack(side=tk.LEFT)
        ttk.Button(ops, text=")", command=lambda: self.add_expr(")")).pack(side=tk.LEFT)

        # --- Expression field
        row = ttk.Frame(self.ops_frame)
        row.pack(fill=tk.X, pady=5)

        ttk.Label(row, text="Shprehja:").pack(side=tk.LEFT)
        ttk.Entry(row, textvariable=self.expr_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=5
        )

    # -------------------------------------------------
    def add_expr(self, token: str):
        self.expr_var.set(self.expr_var.get() + token)

    # -------------------------------------------------
    def read_sets(self):
        self.current_sets = {
            k: parse_set_input(e.get())
            for k, e in self.set_entries.items()
        }

    # -------------------------------------------------
    def compute(self):
        self.output.delete("1.0", tk.END)
        self.read_sets()

        expr = self.expr_var.get().strip()
        if not expr:
            messagebox.showwarning("Gabim", "Shprehja është bosh")
            return

        try:
            result = evaluate_expression(expr, self.current_sets)
        except ValueError as e:
            messagebox.showerror("Gabim", str(e))
            return

        self.output.insert(tk.END, f"Shprehja:\n{expr}\n\n")
        self.output.insert(tk.END, "Bashkësitë:\n")
        for k, v in self.current_sets.items():
            self.output.insert(tk.END, f"{k} = {sorted(v)}\n")

        self.output.insert(tk.END, f"\nRezultati:\nR = {sorted(result)}\n")


# -------------------------------------------------
def main():
    root = tk.Tk()
    SetApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
