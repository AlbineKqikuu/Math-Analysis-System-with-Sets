from __future__ import annotations
from typing import Dict, Set, List, Optional
import json
import csv
import os

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# -------------------------------------------------
#  LIBRARITË OPSIONALE (Venn + PDF)
# -------------------------------------------------
HAS_VENN = True
HAS_REPORTLAB = True

try:
    import matplotlib.pyplot as plt
    from matplotlib_venn import venn2, venn3
except Exception:
    HAS_VENN = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
except Exception:
    HAS_REPORTLAB = False


# -------------------------------------------------
#  FUNKSIONE LOGJIKE
# -------------------------------------------------
def parse_set_input(raw: str) -> Set[str]:
    """
    Konverton input p.sh. "1,2,3 4" ose "a b c" në set strings.
    """
    raw = raw.replace("{", "").replace("}", "")
    parts: List[str] = []
    for chunk in raw.replace(",", " ").split():
        item = chunk.strip()
        if item:
            parts.append(item)
    return set(parts)


def compute_result(
    sets: Dict[str, Set[str]],
    op: str,
    first_label: Optional[str] = None,
    second_label: Optional[str] = None,
) -> Set[str]:
    if not sets:
        return set()

    if op == "union":
        result: Set[str] = set()
        for s in sets.values():
            result |= s
        return result

    if op == "intersection":
        it = iter(sets.values())
        try:
            result = next(it).copy()
        except StopIteration:
            return set()
        for s in it:
            result &= s
        return result

    if op in {"difference", "symdiff"}:
        if not first_label or not second_label:
            return set()
        if first_label == second_label:
            return set()
        A = sets[first_label]
        B = sets[second_label]
        if op == "difference":
            return A - B
        else:
            return A ^ B

    return set()


def build_membership_table(sets: Dict[str, Set[str]], result: Set[str]) -> str:
    all_elements: Set[str] = set()
    for s in sets.values():
        all_elements |= s
    all_elements |= result

    sorted_elements = sorted(all_elements, key=lambda x: (len(x), x))
    labels = list(sets.keys())

    header = "Element".ljust(10)
    for lab in labels:
        header += lab.center(6)
    header += "Rez.".center(6)

    lines = []
    lines.append("TABELA E ANËTARËSISË")
    lines.append(header)
    lines.append("-" * len(header))

    for el in sorted_elements:
        row = el.ljust(10)
        for lab in labels:
            row += ("✓" if el in sets[lab] else ".").center(6)
        row += ("✓" if el in result else ".").center(6)
        lines.append(row)

    return "\n".join(lines)


def build_membership_csv(sets: Dict[str, Set[str]], result: Set[str], csv_path: str):
    """
    Krijon CSV të tabelës së anëtarësisë për Excel.
    """
    all_elements: Set[str] = set()
    for s in sets.values():
        all_elements |= s
    all_elements |= result

    sorted_elements = sorted(all_elements, key=lambda x: (len(x), x))
    labels = list(sets.keys())

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        header = ["Element"] + labels + ["Rezultat"]
        writer.writerow(header)

        for el in sorted_elements:
            row = [el]
            for lab in labels:
                row.append("1" if el in sets[lab] else "0")
            row.append("1" if el in result else "0")
            writer.writerow(row)


def analyze_sets(sets: Dict[str, Set[str]]) -> str:
    labels = list(sets.keys())
    lines = []
    lines.append("ANALIZA LOGJIKE E BASHKËSIVE:")

    if len(labels) < 2:
        lines.append("Nuk ka mjaftueshëm bashkësi për analizë.")
        return "\n".join(lines)

    total_universe: Set[str] = set()
    for s in sets.values():
        total_universe |= s
    universe_size = len(total_universe) if total_universe else 1

    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            a, b = labels[i], labels[j]
            A, B = sets[a], sets[b]
            inter = A & B
            uni = A | B
            only_a = A - B
            only_b = B - A

            if A == B:
                rel = "janë të barabarta."
            elif A.issubset(B):
                rel = f"{a} është nënbashkësi e {b}."
            elif B.issubset(A):
                rel = f"{b} është nënbashkësi e {a}."
            elif A.isdisjoint(B):
                rel = "janë disjunkte (s'kanë elemente të përbashkëta)."
            else:
                rel = "kanë disa elemente të përbashkëta, por asnjëra s’është nënbashkësi e tjetrës."

            # koeficienti i ngjashmërisë Jaccard
            sim = len(inter) / len(uni) if len(uni) > 0 else 0.0
            perc_inter = len(inter) / universe_size * 100 if universe_size > 0 else 0

            lines.append(
                f"- {a} dhe {b}: {rel} "
                f"| |A|={len(A)}, |B|={len(B)}, |A∩B|={len(inter)}, |A∪B|={len(uni)}, "
                f"Jaccard={sim:.2f}, A∩B ≈ {perc_inter:.1f}% e universit lokal."
            )
            if only_a:
                lines.append(f"    Elementet vetëm në {a}: {sorted(only_a)}")
            if only_b:
                lines.append(f"    Elementet vetëm në {b}: {sorted(only_b)}")

    return "\n".join(lines)


def intelligent_summary(
    sets: Dict[str, Set[str]],
    result: Set[str],
    op: str,
    first_label: Optional[str],
    second_label: Optional[str],
) -> str:
    lines: List[str] = []
    labels = list(sets.keys())

    if op == "union":
        lines.append("KOMENT INTELIGJENT:")
        lines.append(
            f"- Union-i përfshin {len(result)} elemente nga gjithsej "
            f"{len(set().union(*sets.values())) if sets else 0} elemente të mundshme."
        )
        big = max(labels, key=lambda l: len(sets[l])) if labels else None
        if big:
            lines.append(f"- Bashkësia më e madhe është {big} me {len(sets[big])} elemente.")
    elif op == "intersection":
        lines.append("KOMENT INTELIGJENT:")
        if not result:
            lines.append("- Prerja është bosh → bashkësitë nuk kanë elemente të përbashkëta.")
        else:
            lines.append(f"- Prerja ka {len(result)} element(e): {sorted(result)}")
    elif op == "difference" and first_label and second_label:
        A = sets[first_label]
        B = sets[second_label]
        lines.append("KOMENT INTELIGJENT:")
        lines.append(
            f"- Nga {first_label} janë hequr elementët që gjenden në {second_label}."
        )
        lines.append(f"- {first_label} kishte {len(A)} elemente, pas diferencës mbeten {len(result)}.")
    elif op == "symdiff" and first_label and second_label:
        lines.append("KOMENT INTELIGJENT:")
        lines.append(
            f"- Diferenca simetrike {first_label} Δ {second_label} përfshin elementët "
            "që janë në njërën prej bashkësive, por jo në të dyjat."
        )
        lines.append(f"- Rezultati ka {len(result)} element(e): {sorted(result)}")

    return "\n".join(lines) if lines else ""


# -------------------------------------------------
#  VENN DIAGRAM PËR 2 / 3 / 4 BASHKËSI (FINAL)
# -------------------------------------------------
def draw_venn(sets: Dict[str, Set[str]], op: str,
              first_label: Optional[str], second_label: Optional[str]):
    if not HAS_VENN:
        messagebox.showinfo(
            "Diagram Venn",
            "matplotlib_venn nuk është i instaluar.\n"
            "Instalo me: pip install matplotlib matplotlib-venn venn",
        )
        return

    import matplotlib.pyplot as plt
    from matplotlib_venn import venn2, venn3
    try:
        from venn import venn as venn4
    except:
        venn4 = None

    n = len(sets)
    labels = list(sets.keys())

    if n < 2:
        messagebox.showwarning("Diagram Venn", "Duhet të paktën 2 bashkësi.")
        return

    # Titulli
    if op == "union":
        title = f"Union ({', '.join(labels)})"
    elif op == "intersection":
        title = f"Prerje ({', '.join(labels)})"
    elif op == "difference":
        title = f"Diferencë {first_label} \\ {second_label}"
    elif op == "symdiff":
        title = f"Diferencë Simetrike {first_label} Δ {second_label}"
    else:
        title = f"Diagram Venn ({', '.join(labels)})"

    # ---------------------------------------
    #  CASE: 2 BASHKËSI
    # ---------------------------------------
    if n == 2:
        A, B = sets[labels[0]], sets[labels[1]]
        plt.figure(figsize=(7, 7))
        v = venn2([A, B], set_labels=(labels[0], labels[1]))

        def txt(s):
            try:
                return "\n".join(sorted(s, key=lambda x: int(x)))
            except:
                return "\n".join(sorted(s))

        # Zona 10 → vetëm A
        if v.get_label_by_id("10"):
            v.get_label_by_id("10").set_text(txt(A - B))
        # Zona 01 → vetëm B
        if v.get_label_by_id("01"):
            v.get_label_by_id("01").set_text(txt(B - A))
        # Zona 11 → përbashkëta
        if v.get_label_by_id("11"):
            v.get_label_by_id("11").set_text(txt(A & B))

        # Ngjyra pastel
        if v.get_patch_by_id("10"):
            v.get_patch_by_id("10").set_color("#ffcccc")
        if v.get_patch_by_id("01"):
            v.get_patch_by_id("01").set_color("#cce5ff")
        if v.get_patch_by_id("11"):
            v.get_patch_by_id("11").set_color("#ffe6cc")

        plt.title(title, fontsize=14)
        plt.show()
        return

    # ---------------------------------------
    #  CASE: 3 BASHKËSI
    # ---------------------------------------
    if n == 3:
        A, B, C = sets[labels[0]], sets[labels[1]], sets[labels[2]]
        plt.figure(figsize=(7, 7))
        v = venn3([A, B, C], set_labels=(labels[0], labels[1], labels[2]))

        regions = {
            "100": A - B - C,
            "010": B - A - C,
            "001": C - A - B,
            "110": (A & B) - C,
            "101": (A & C) - B,
            "011": (B & C) - A,
            "111": A & B & C,
        }

        def txt(s):
            try:
                return "\n".join(sorted(s, key=lambda x: int(x)))
            except:
                return "\n".join(sorted(s))

        for area, elements in regions.items():
            if v.get_label_by_id(area):
                v.get_label_by_id(area).set_text(txt(elements))

        # Ngjyrat pastel
        colors = {
            "100": "#ffcccc",
            "010": "#cce5ff",
            "001": "#ccffcc",
            "110": "#ffe6cc",
            "101": "#e6ccff",
            "011": "#ccffe6",
            "111": "#ffffcc",
        }

        for area, col in colors.items():
            if v.get_patch_by_id(area):
                v.get_patch_by_id(area).set_color(col)

        plt.title(title, fontsize=14)
        plt.show()
        return

     # ---------------------------------------
    #  CASE: 4 BASHKËSI (VERSIONI I SAKTË)
    # ---------------------------------------
    if n == 4:
        A, B, C, D = sets[labels[0]], sets[labels[1]], sets[labels[2]], sets[labels[3]]

        # 15 zonat për 4 bashkësi
        Z = {}
        Z["A"]   = A - (B | C | D)
        Z["B"]   = B - (A | C | D)
        Z["C"]   = C - (A | B | D)
        Z["D"]   = D - (A | B | C)

        Z["AB"]  = (A & B) - (C | D)
        Z["AC"]  = (A & C) - (B | D)
        Z["AD"]  = (A & D) - (B | C)

        Z["BC"]  = (B & C) - (A | D)
        Z["BD"]  = (B & D) - (A | C)
        Z["CD"]  = (C & D) - (A | B)

        Z["ABC"] = (A & B & C) - D
        Z["ABD"] = (A & B & D) - C
        Z["ACD"] = (A & C & D) - B
        Z["BCD"] = (B & C & D) - A

        Z["ABCD"] = A & B & C & D

        # Vizatim Square Layout (më i saktë se çdo bibliotekë)
        plt.figure(figsize=(10, 10))
        ax = plt.gca()
        ax.set_title(title + " (4 bashkësi)", fontsize=16)
        ax.axis("off")

        # Pozicionet e zonave
        positions = {
            "A":   (0.12, 0.80),
            "B":   (0.82, 0.80),
            "C":   (0.12, 0.20),
            "D":   (0.82, 0.20),

            "AB":  (0.47, 0.83),
            "AC":  (0.12, 0.55),
            "AD":  (0.47, 0.55),

            "BC":  (0.53, 0.55),
            "BD":  (0.87, 0.55),
            "CD":  (0.53, 0.22),

            "ABC": (0.30, 0.70),
            "ABD": (0.63, 0.70),
            "ACD": (0.30, 0.40),
            "BCD": (0.63, 0.40),

            "ABCD": (0.47, 0.50),
        }

        pastel = "#e8f3ff"

        def sort_items(s):
            try: return sorted(s, key=lambda x: int(x))
            except: return sorted(s)

        # Shkruaj çdo zonë
        for zone, pos in positions.items():
            text = "\n".join(sort_items(Z[zone])) if Z[zone] else ""
            ax.text(
                pos[0], pos[1],
                text,
                fontsize=10,
                ha="center",
                va="center",
                bbox=dict(boxstyle="round,pad=0.3", fc=pastel, ec="#aaccee")
            )

        # Etiketa A B C D
        ax.text(0.12, 0.90, labels[0], fontsize=14, weight="bold")
        ax.text(0.82, 0.90, labels[1], fontsize=14, weight="bold")
        ax.text(0.12, 0.10, labels[2], fontsize=14, weight="bold")
        ax.text(0.82, 0.10, labels[3], fontsize=14, weight="bold")

        plt.show()
        return




# -------------------------------------------------
#  EXPORT NË PDF
# -------------------------------------------------
def export_to_pdf(
    pdf_path: str,
    sets: Dict[str, Set[str]],
    result: Set[str],
    op_desc: str,
    membership_table: str,
    analysis: str,
    intelligent_comment: str,
):
    if not HAS_REPORTLAB:
        messagebox.showinfo(
            "PDF",
            "reportlab nuk është i instaluar.\nInstalo me: pip install reportlab",
        )
        return

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    x_margin = 20 * mm
    y = height - 25 * mm

    def draw_text_block(title: str, text: str, y_start: float) -> float:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x_margin, y_start, title)
        y_current = y_start - 15
        c.setFont("Helvetica", 10)
        for line in text.splitlines():
            if y_current < 25 * mm:
                c.showPage()
                y_current = height - 25 * mm
                c.setFont("Helvetica-Bold", 12)
                c.drawString(x_margin, y_current, title + " (vijim)")
                y_current -= 15
                c.setFont("Helvetica", 10)
            c.drawString(x_margin, y_current, line)
            y_current -= 12
        return y_current - 10

    # Titulli kryesor
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x_margin, y, "Projekt inteligjent për bashkësi")
    y -= 25

    # Operacioni + bashkësitë
    sets_text_lines = ["Bashkësitë:"]
    for lab, s in sets.items():
        sets_text_lines.append(f"{lab} = {{ " + ", ".join(sorted(s)) + " }}")
    sets_text_lines.append("")
    sets_text_lines.append("Rezultati:")
    sets_text_lines.append("R = { " + ", ".join(sorted(result)) + " }")
    sets_text = "\n".join(sets_text_lines)

    y = draw_text_block("Operacioni", op_desc + "\n\n" + sets_text, y)
    y = draw_text_block("Tabela e anëtarësisë", membership_table, y)
    y = draw_text_block("Analiza logjike", analysis, y)
    if intelligent_comment.strip():
        y = draw_text_block("Koment inteligjent", intelligent_comment, y)

    c.showPage()
    c.save()


# -------------------------------------------------
#  GUI
# -------------------------------------------------
class SetApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Projekt inteligjent për bashkësi (Union, Prerje, Diferencë)")
        self.root.geometry("1000x650")

        # stil modern
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TButton", padding=6)
        style.configure("TLabel", padding=2)

        self.num_sets_var = tk.IntVar(value=2)

        self.set_entries: Dict[str, tk.Entry] = {}
        self.operation_var = tk.StringVar(value="union")
        self.first_set_var = tk.StringVar()
        self.second_set_var = tk.StringVar()

        # për të ruajtur rezultatet aktuale (për export)
        self.current_sets: Dict[str, Set[str]] = {}
        self.current_result: Set[str] = set()
        self.current_op_desc: str = ""
        self.current_membership: str = ""
        self.current_analysis: str = ""
        self.current_intelligent: str = ""

        self.create_widgets()
        self.create_menu()

    # ----------------- GUI Layout -----------------
    def create_widgets(self):
        # sipër: numri i bashkësive
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(top_frame, text="Numri i bashkësive:").pack(side=tk.LEFT)
        self.num_sets_combo = ttk.Combobox(
            top_frame,
            textvariable=self.num_sets_var,
            values=[2, 3, 4],
            state="readonly",
            width=5,
        )
        self.num_sets_combo.pack(side=tk.LEFT, padx=5)
        self.num_sets_combo.bind("<<ComboboxSelected>>", lambda e: self.build_set_inputs())

        # bashkësitë
        self.sets_frame = ttk.LabelFrame(self.root, text="Bashkësitë", padding=10)
        self.sets_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # operacionet
        self.op_frame = ttk.LabelFrame(self.root, text="Operacionet", padding=10)
        self.op_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # butonat
        button_frame = ttk.Frame(self.root, padding=10)
        button_frame.pack(side=tk.TOP, fill=tk.X)

        # output + scrollbar
        output_frame = ttk.Frame(self.root)
        output_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.output_text = tk.Text(output_frame, wrap=tk.NONE)
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        y_scroll = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=self.output_text.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_text.configure(yscrollcommand=y_scroll.set)

        self.build_set_inputs()
        self.build_operation_selector()

        ttk.Button(button_frame, text="Llogarit", command=self.on_compute).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Diagram Venn", command=self.on_venn).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export TXT", command=self.on_export_txt).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export CSV", command=self.on_export_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export PDF", command=self.on_export_pdf).pack(side=tk.LEFT, padx=5)

    def create_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Projekt i ri", command=self.on_new_project)
        file_menu.add_command(label="Hape projekt...", command=self.on_open_project)
        file_menu.add_command(label="Ruaj projekt...", command=self.on_save_project)
        file_menu.add_separator()
        file_menu.add_command(label="Dalje", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        self.root.config(menu=menubar)

    # ----------------- Inputs për bashkësi -----------------
    def build_set_inputs(self):
        for widget in self.sets_frame.winfo_children():
            widget.destroy()

        self.set_entries.clear()

        n = self.num_sets_var.get()
        labels = ["A", "B", "C", "D"][:n]

        for lab in labels:
            row = ttk.Frame(self.sets_frame)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=f"{lab} =").pack(side=tk.LEFT)
            entry = ttk.Entry(row)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            self.set_entries[lab] = entry

        self.update_set_choice_comboboxes()

    def build_operation_selector(self):
        for widget in self.op_frame.winfo_children():
            widget.destroy()

        ops_frame = ttk.Frame(self.op_frame)
        ops_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Radiobutton(
            ops_frame,
            text="Union (A ∪ B ∪ ...)",
            variable=self.operation_var,
            value="union",
            command=self.update_set_choice_visibility,
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            ops_frame,
            text="Prerje (A ∩ B ∩ ...)",
            variable=self.operation_var,
            value="intersection",
            command=self.update_set_choice_visibility,
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            ops_frame,
            text="Diferencë (X \\ Y)",
            variable=self.operation_var,
            value="difference",
            command=self.update_set_choice_visibility,
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            ops_frame,
            text="Diferencë simetrike (X Δ Y)",
            variable=self.operation_var,
            value="symdiff",
            command=self.update_set_choice_visibility,
        ).pack(anchor=tk.W)

        self.diff_frame = ttk.Frame(self.op_frame)
        self.diff_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        ttk.Label(self.diff_frame, text="Bashkësia e parë (X):").pack(side=tk.LEFT)
        self.first_set_combo = ttk.Combobox(
            self.diff_frame,
            textvariable=self.first_set_var,
            state="readonly",
            width=5,
        )
        self.first_set_combo.pack(side=tk.LEFT, padx=5)

        ttk.Label(self.diff_frame, text="Bashkësia e dytë (Y):").pack(side=tk.LEFT)
        self.second_set_combo = ttk.Combobox(
            self.diff_frame,
            textvariable=self.second_set_var,
            state="readonly",
            width=5,
        )
        self.second_set_combo.pack(side=tk.LEFT, padx=5)

        self.update_set_choice_comboboxes()
        self.update_set_choice_visibility()

    def update_set_choice_comboboxes(self):
        if not hasattr(self, "first_set_combo"):
            return
        n = self.num_sets_var.get()
        labels = ["A", "B", "C", "D"][:n]

        self.first_set_combo["values"] = labels
        self.second_set_combo["values"] = labels

        if labels:
            self.first_set_var.set(labels[0])
            self.second_set_var.set(labels[1] if len(labels) > 1 else labels[0])

    def update_set_choice_visibility(self):
        op = self.operation_var.get()
        if op in {"difference", "symdiff"}:
            self.diff_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        else:
            self.diff_frame.pack_forget()

    def read_sets(self) -> Dict[str, Set[str]]:
        sets: Dict[str, Set[str]] = {}
        for lab, entry in self.set_entries.items():
            raw = entry.get()
            s = parse_set_input(raw)
            sets[lab] = s
        return sets

    # ----------------- Aksionet kryesore -----------------
    def on_compute(self):
        sets = self.read_sets()
        op = self.operation_var.get()

        first_label = self.first_set_var.get() if op in {"difference", "symdiff"} else None
        second_label = self.second_set_var.get() if op in {"difference", "symdiff"} else None

        result = compute_result(sets, op, first_label, second_label)

        self.output_text.delete("1.0", tk.END)

        # Përshkrimi i operacionit
        desc = "Operacioni: "
        if op == "union":
            desc += "UNION i të gjitha bashkësive"
        elif op == "intersection":
            desc += "PRERJE e të gjitha bashkësive"
        elif op == "difference":
            desc += f"DIFERENCË {first_label} \\ {second_label}"
        elif op == "symdiff":
            desc += f"DIFERENCË SIMETRIKE {first_label} Δ {second_label}"

        self.output_text.insert(tk.END, desc + "\n\n")

        # Shfaq bashkësitë
        self.output_text.insert(tk.END, "Bashkësitë:\n")
        for lab, s in sets.items():
            self.output_text.insert(tk.END, f"{lab} = {{ " + ", ".join(sorted(s)) + " }}\n")

        self.output_text.insert(tk.END, "\nRezultati:\n")
        self.output_text.insert(tk.END, "R = { " + ", ".join(sorted(result)) + " }\n\n")

        membership_table = build_membership_table(sets, result)
        self.output_text.insert(tk.END, membership_table + "\n\n")

        analysis_str = analyze_sets(sets)
        self.output_text.insert(tk.END, analysis_str + "\n\n")

        intelligent_comment = intelligent_summary(sets, result, op, first_label, second_label)
        if intelligent_comment.strip():
            self.output_text.insert(tk.END, intelligent_comment + "\n")

        # ruaj për export
        self.current_sets = sets
        self.current_result = result
        self.current_op_desc = desc
        self.current_membership = membership_table
        self.current_analysis = analysis_str
        self.current_intelligent = intelligent_comment

    def on_venn(self):
        if not self.current_sets:
            self.on_compute()
        sets = self.current_sets or self.read_sets()
        op = self.operation_var.get()
        first_label = self.first_set_var.get() if op in {"difference", "symdiff"} else None
        second_label = self.second_set_var.get() if op in {"difference", "symdiff"} else None
        draw_venn(sets, op, first_label, second_label)

    # ----------------- EXPORT -----------------
    def on_export_txt(self):
        if not self.current_sets:
            self.on_compute()
        text = self.output_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showinfo("Export TXT", "Nuk ka asgjë për të ruajtur.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not file_path:
            return
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)
            messagebox.showinfo("Export TXT", f"Rezultati u ruajt në:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Gabim", f"Nuk u ruajt file-i.\n{e}")

    def on_export_csv(self):
        if not self.current_sets:
            self.on_compute()
        if not self.current_sets:
            messagebox.showinfo("Export CSV", "Fillimisht llogarit rezultatet.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not file_path:
            return
        try:
            build_membership_csv(self.current_sets, self.current_result, file_path)
            messagebox.showinfo("Export CSV", f"CSV u ruajt në:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Gabim", f"Nuk u ruajt CSV.\n{e}")

    def on_export_pdf(self):
        if not self.current_sets:
            self.on_compute()
        if not self.current_sets:
            messagebox.showinfo("Export PDF", "Fillimisht llogarit rezultatet.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if not file_path:
            return
        try:
            export_to_pdf(
                file_path,
                self.current_sets,
                self.current_result,
                self.current_op_desc,
                self.current_membership,
                self.current_analysis,
                self.current_intelligent,
            )
            messagebox.showinfo("Export PDF", f"PDF u ruajt në:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Gabim", f"Nuk u ruajt PDF.\n{e}")

    # ----------------- PROJECT SAVE/LOAD -----------------
    def on_new_project(self):
        self.output_text.delete("1.0", tk.END)
        for e in self.set_entries.values():
            e.delete(0, tk.END)
        self.current_sets = {}
        self.current_result = set()

    def on_save_project(self):
        sets = self.read_sets()
        data = {
            "num_sets": self.num_sets_var.get(),
            "sets": {k: sorted(list(v)) for k, v in sets.items()},
            "operation": self.operation_var.get(),
            "first_label": self.first_set_var.get(),
            "second_label": self.second_set_var.get(),
        }
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not file_path:
            return
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Projekt", f"Projekti u ruajt në:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Gabim", f"Nuk u ruajt projekti.\n{e}")

    def on_open_project(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror("Gabim", f"Nuk u lexua projekti.\n{e}")
            return

        num_sets = data.get("num_sets", 2)
        self.num_sets_var.set(num_sets)
        self.build_set_inputs()

        sets_data = data.get("sets", {})
        for lab, entry in self.set_entries.items():
            entry.delete(0, tk.END)
            values = sets_data.get(lab, [])
            if values:
                entry.insert(0, ",".join(values))

        op = data.get("operation", "union")
        self.operation_var.set(op)
        self.update_set_choice_visibility()

        self.first_set_var.set(data.get("first_label", "A"))
        self.second_set_var.set(data.get("second_label", "B"))
        self.update_set_choice_comboboxes()

        # llogarit automatikisht pas hapjes
        self.on_compute()


def main():
    root = tk.Tk()
    app = SetApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
