from __future__ import annotations
from typing import Dict, Set
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import re
import csv

# ------------------ OPTIONAL LIBS ------------------
import subprocess
import sys
import os
HAS_VENN = True
HAS_PDF = True

try:
    import matplotlib.pyplot as plt
    from matplotlib_venn import venn2, venn3
except:
    HAS_VENN = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
except:
    HAS_PDF = False


# ------------------ SET LOGIC ------------------
def parse_set_input(raw: str) -> Set[str]:
    raw = raw.replace("{", "").replace("}", "")
    return set(x.strip() for x in raw.replace(",", " ").split() if x.strip())


def evaluate_expression(expr: str, sets: Dict[str, Set[str]]) -> Set[str]:
    expr = expr.replace("∪", "|").replace("∩", "&").replace("\\", "-").replace("Δ", "^")
    for k in sets:
        expr = re.sub(rf"\b{k}\b", f"sets['{k}']", expr)
    return eval(expr)


def build_membership_table(sets: Dict[str, Set[str]], result: Set[str]) -> str:
    universe = set().union(*sets.values()) | result
    labels = list(sets.keys())

    header = "El".ljust(6)
    for l in labels:
        header += l.center(5)
    header += "R".center(5)

    lines = [header, "-" * len(header)]
    for el in sorted(universe):
        row = el.ljust(6)
        for l in labels:
            row += ("✓" if el in sets[l] else ".").center(5)
        row += ("✓" if el in result else ".").center(5)
        lines.append(row)

    return "\n".join(lines)


# ------------------ GUI APP ------------------
class SetApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Projekt inteligjent për bashkësi – Expression Builder")
        self.root.geometry("1050x700")

        self.num_sets_var = tk.IntVar(value=2)
        self.expr_var = tk.StringVar()

        self.set_entries: Dict[str, tk.Entry] = {}
        self.current_sets: Dict[str, Set[str]] = {}
        self.current_result: Set[str] = set()

        self.build_ui()

    # ------------------ UI ------------------
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

        btns = ttk.Frame(self.root, padding=8)
        btns.pack(fill=tk.X)

        ttk.Button(btns, text="Llogarit", command=self.compute).pack(side=tk.LEFT, padx=5)
        ttk.Button(btns, text="Diagram Venn", command=self.draw_venn).pack(side=tk.LEFT, padx=5)
        ttk.Button(btns, text="Export TXT", command=self.export_txt).pack(side=tk.LEFT, padx=5)
        ttk.Button(btns, text="Export CSV", command=self.export_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(btns, text="Export PDF", command=self.export_pdf).pack(side=tk.LEFT, padx=5)

        self.output = tk.Text(self.root, height=20)
        self.output.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.build_sets()
        self.build_expression_builder()

    # ------------------ SET INPUTS ------------------
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

    # ------------------ EXPRESSION BUILDER ------------------
    def build_expression_builder(self):
        for w in self.ops_frame.winfo_children():
            w.destroy()

        labels = list(self.set_entries.keys())

        row = ttk.Frame(self.ops_frame)
        row.pack(anchor=tk.W)

        for lab in labels:
            ttk.Button(row, text=lab,
                       command=lambda l=lab: self.add_expr(l)).pack(side=tk.LEFT, padx=4)

        ops = ttk.Frame(self.ops_frame)
        ops.pack(anchor=tk.W, pady=5)

        for sym in ["∪", "∩", "\\", "Δ", "(", ")"]:
            # Fixed: Also add spaces for set difference \ for better readability
            ttk.Button(
                ops, text=sym,
                command=lambda s=sym: self.add_expr(f" {s} " if s not in "()" else s)
            ).pack(side=tk.LEFT, padx=5)

        row2 = ttk.Frame(self.ops_frame)
        row2.pack(fill=tk.X)

        ttk.Label(row2, text="Shprehja:").pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.expr_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=5
        )

    def add_expr(self, t):
        self.expr_var.set(self.expr_var.get() + t)

    # ------------------ COMPUTE ------------------
    def read_sets(self):
        self.current_sets = {k: parse_set_input(e.get())
                             for k, e in self.set_entries.items()}

    def compute(self):
        self.output.delete("1.0", tk.END)
        self.read_sets()

        expr = self.expr_var.get().strip()
        if not expr:
            messagebox.showwarning("Gabim", "Shprehja është bosh")
            return

        try:
            self.current_result = evaluate_expression(expr, self.current_sets)
        except Exception as e:
            messagebox.showerror("Gabim", f"Gabim në llogaritje: {str(e)}")
            return

        self.output.insert(tk.END, f"Shprehja:\n{expr}\n\nBashkësitë:\n")
        for k, v in self.current_sets.items():
            self.output.insert(tk.END, f"{k} = {sorted(v)}\n")

        self.output.insert(tk.END, f"\nRezultati:\nR = {sorted(self.current_result)}\n\n")

        # -------- SUBSET CHECK (2 SETS) --------
        if len(self.current_sets) == 2:
            A = self.current_sets.get("A", set())
            B = self.current_sets.get("B", set())
            if A.issubset(B) and B.issubset(A):
                self.output.insert(tk.END, "Info: A është e barabartë me B (A ⊆ B dhe B ⊆ A)\n\n")
            elif A.issubset(B):
                self.output.insert(tk.END, "Info: A është nënbashkësi e B (A ⊆ B)\n\n")
            elif B.issubset(A):
                self.output.insert(tk.END, "Info: B është nënbashkësi e A (B ⊆ A)\n\n")

        self.output.insert(tk.END, build_membership_table(self.current_sets, self.current_result))

    # ------------------ UTILS ------------------
    def evaluate_symbolic(self, rid: str, labels: list[str]) -> bool:
        """Evaluates if a specific region (bitmask) is part of the result."""
        test_sets = {l: set() for l in labels}
        for i, bit in enumerate(rid):
            if bit == '1':
                test_sets[labels[i]].add("x")
        
        expr = self.expr_var.get().strip()
        if not expr: return False
        try:
            res = evaluate_expression(expr, test_sets)
            return "x" in res
        except: return False

    # ------------------ VENN ------------------
    def draw_venn(self):
        if not HAS_VENN:
            messagebox.showinfo("Venn", "matplotlib-venn mungon")
            return

        if not self.current_sets:
            self.compute()

        n = len(self.current_sets)
        plt.close('all') # Clear previous plots

        # -------- 2 BASHKËSI --------
        if n == 2:
            labels_list = ["A", "B"]
            A, B = self.current_sets["A"], self.current_sets["B"]
            plt.figure(figsize=(8, 7))
            v = venn2([A, B], set_labels=labels_list)
            
            regions_map = {"10": A - B, "01": B - A, "11": A & B}
            for rid, elems in regions_map.items():
                patch = v.get_patch_by_id(rid)
                label = v.get_label_by_id(rid)
                if label: label.set_text("\n".join(sorted(elems)) if elems else "")
                is_active = self.evaluate_symbolic(rid, labels_list)
                if patch:
                    patch.set_alpha(0.8 if is_active else 0.2)
                    if is_active:
                        patch.set_edgecolor('black')
                        patch.set_linewidth(2)

            plt.title(f"Diagrami i Vennit (2 bashkësi):\n{self.expr_var.get()}", pad=20)
            plt.show()
            return

        # -------- 3 BASHKËSI --------
        if n == 3:
            labels_list = ["A", "B", "C"]
            A, B, C = (self.current_sets[l] for l in labels_list)
            plt.figure(figsize=(9, 8))
            v = venn3([A, B, C], set_labels=labels_list)
            
            universe = set().union(A, B, C)
            regions_ids = ["100", "010", "110", "001", "101", "011", "111"]
            for rid in regions_ids:
                patch = v.get_patch_by_id(rid)
                label = v.get_label_by_id(rid)
                
                # Calculate precise region elements
                curr = universe.copy()
                for i, bit in enumerate(rid):
                    s = self.current_sets[labels_list[i]]
                    curr = (curr & s) if bit == '1' else (curr - s)
                
                if label: label.set_text("\n".join(sorted(curr)) if curr else "")
                is_active = self.evaluate_symbolic(rid, labels_list)
                if patch:
                    patch.set_alpha(0.8 if is_active else 0.2)
                    if is_active:
                        patch.set_edgecolor('black')
                        patch.set_linewidth(2)

            plt.title(f"Diagrami i Vennit (3 bashkësi):\n{self.expr_var.get()}", pad=20)
            plt.show()
            return

        # -------- 4 BASHKËSI (SHADED AREAS) --------
        if n == 4:
            import numpy as np
            from matplotlib.patches import Ellipse
            labels_list = ["A", "B", "C", "D"]
            sets_data = [self.current_sets[l] for l in labels_list]
            universe = set().union(*sets_data)

            # High-res grid for pixel-perfect shading of complex operations
            res = 400
            gx = np.linspace(0, 10, res)
            gy = np.linspace(0, 10, res)
            X, Y = np.meshgrid(gx, gy)

            # Ellipse definitions
            ell_params = [
                ((4.0, 5.0), 3.8, 7.8, 35),  # A
                ((6.0, 5.0), 3.8, 7.8, -35), # B
                ((4.0, 5.8), 3.8, 7.8, 35),  # C
                ((6.0, 5.8), 3.8, 7.8, -35)  # D
            ]

            def get_mask(X, Y, center, w, h, angle_deg):
                ang = np.radians(angle_deg)
                cx, cy = center
                a, b = w/2, h/2
                dx, dy = X - cx, Y - cy
                rx = dx * np.cos(ang) + dy * np.sin(ang)
                ry = -dx * np.sin(ang) + dy * np.cos(ang)
                return (rx**2 / a**2 + ry**2 / b**2) <= 1

            masks = {labels_list[i]: get_mask(X, Y, *p) for i, p in enumerate(ell_params)}

            # Evaluate the set expression on the bitmasks
            expr_val = self.expr_var.get().strip()
            # Convert expression to numpy-compatible bitwise logic
            # Union: |, Intersection: &, SymDiff: ^, Diff: \ -> & ~
            clean_expr = expr_val.replace("∪", "|").replace("∩", "&").replace("Δ", "^").replace("\\", "& ~")
            for k in masks:
                clean_expr = re.sub(rf"\b{k}\b", f"masks['{k}']", clean_expr)
            
            try:
                result_mask = eval(clean_expr)
            except:
                result_mask = np.zeros_like(X, dtype=bool)

            fig, ax = plt.subplots(figsize=(10, 10))
            ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.set_aspect('equal')
            ax.axis('off')

            # Shade the resulting union/intersection area in Gold
            if np.any(result_mask):
                ax.contourf(X, Y, result_mask, levels=[0.5, 1.5], colors=['#FFD700'], alpha=0.5)

            # Draw set outlines
            colors = ['#ff4d4d', '#4dff4d', '#4d4dff', '#ffb347']
            for i, p in enumerate(ell_params):
                # Light fill
                ax.add_patch(Ellipse(p[0], p[1], p[2], angle=p[3], fc=colors[i], alpha=0.1))
                # Thick border
                ax.add_patch(Ellipse(p[0], p[1], p[2], angle=p[3], ec=colors[i], fc='none', lw=2.5, zorder=10))

            # Color-coded Legend at the top left
            for i, l in enumerate(labels_list):
                members = sorted(list(self.current_sets[l]))
                ax.text(0.2, 9.8 - i*0.4, f"Bashkësia {l}: {members}", 
                        color=colors[i], weight='bold', fontsize=9, ha='left', transform=ax.transData)

            # Region Markers (Gold buttons for result-active areas)
            centers = {
                "1000": (1.8, 3.8), "0100": (8.2, 3.8), "0010": (1.8, 7.2), "0001": (8.2, 7.2),
                "1100": (5.0, 1.8), "1010": (3.1, 5.5), "0101": (6.9, 5.5), "0011": (5.0, 9.2),
                "1001": (4.3, 4.2), "0110": (5.7, 4.2), "1110": (3.8, 3.0), "1101": (6.2, 3.0),
                "1011": (3.8, 8.0), "0111": (6.2, 8.0), "1111": (5.0, 5.5)
            }

            for bits, pos in centers.items():
                if self.evaluate_symbolic(bits, labels_list):
                    ax.plot(pos[0], pos[1], 'o', color='gold', markersize=14, markeredgecolor='black', zorder=15)
                    ax.text(pos[0], pos[1], "R", ha='center', va='center', weight='bold', fontsize=8, zorder=16)

            plt.title(f"Rezultati i Shprehjes: {expr_val}", fontsize=14, pad=40)
            plt.show()
            return


        
    # ------------------ METRICS ------------------
    def get_code_metrics(self, file_path):
        """Runs radon and pylint, returns tuple: (report_str, metrics_dict)."""
        report = []
        data = {"loc": 0, "cc_avg": 0.0, "mi_score": 0.0, "pylint_score": 0.0}
        
        def run_cmd(cmd, title):
            report.append(f"{'='*30}\n{title}\n{'='*30}")
            output = ""
            try:
                if cmd[0] == "radon":
                    full_cmd = [sys.executable, "-m", "radon"] + cmd[1:]
                elif cmd[0] == "pylint":
                    full_cmd = [sys.executable, "-m", "pylint"] + cmd[1:]
                else:
                    full_cmd = cmd

                full_cmd.append(file_path)
                result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=15)
                
                if result.stdout:
                    output = result.stdout
                    report.append(output)
                if result.stderr:
                    report.append(f"[STDERR]\n{result.stderr}")
            except Exception as e:
                report.append(f"Error running {title}: {str(e)}")
            report.append("\n")
            return output

        # 1. Radon Raw -> Parse LOC
        out_raw = run_cmd(["radon", "raw"], "Radon Raw Metrics (LOC, Comments)")
        try:
            # Example: "    LOC: 368"
            for line in out_raw.splitlines():
                if "LOC:" in line:
                    data["loc"] = int(line.split("LOC:")[1].strip())
        except: pass

        # 2. Radon CC -> Parse Grade/Avg
        out_cc = run_cmd(["radon", "cc", "-a"], "Radon Cyclomatic Complexity")
        try:
            # Example: "Average complexity: A (1.615...)"
            for line in out_cc.splitlines():
                if "Average complexity:" in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        data["cc_grade"] = parts[2] 
        except: pass
        
        # 3. Radon Halstead
        run_cmd(["radon", "hal"], "Radon Halstead Metrics")
        
        # 4. Radon MI -> Parse Score
        out_mi = run_cmd(["radon", "mi"], "Maintainability Index")
        try:
            # Example: "main3.py - A (87.42)"
            if "(" in out_mi and ")" in out_mi:
                score_str = out_mi.split("(")[1].split(")")[0]
                data["mi_score"] = float(score_str)
        except: pass

        # 5. Pylint -> Parse Score
        out_pylint = run_cmd(["pylint", "--reports=y"], "Pylint Code Quality Report")
        try:
            # Example: "Your code has been rated at 6.50/10"
            match = re.search(r"rated at (\d+\.\d+)/10", out_pylint)
            if match:
                data["pylint_score"] = float(match.group(1))
        except: pass

        return "\n".join(report), data

    def generate_detailed_explanation(self, data):
        """Generates specific Albanian text based on metrics data."""
        lines = []
        
        # LOC
        loc = data.get("loc", 0)
        size_desc = "i vogël"
        if loc > 200: size_desc = "mesatar"
        if loc > 500: size_desc = "i madh"
        lines.append(f"• Madhësia: Kodi ka {loc} rreshta. Konsiderohet projekt {size_desc}.")

        # CC 
        cc_grade = data.get("cc_grade", "?")
        cc_desc = "shkëlqyer"
        if cc_grade in ['B']: cc_desc = "mirë"
        elif cc_grade in ['C']: cc_desc = "moderuar (kujdes)"
        elif cc_grade in ['D', 'E', 'F']: cc_desc = "kompleks (duhet thjeshtuar)"
        lines.append(f"• Kompleksiteti: Nota mesatare është {cc_grade}. Struktura e programit është e {cc_desc}.")

        # MI
        mi = data.get("mi_score", 0)
        mi_msg = "lehtë për t'u mirëmbajtur" if mi > 50 else "vështirë për t'u mirëmbajtur"
        lines.append(f"• Mirëmbajtja: Indeksi është {mi:.2f}. Kodi është i {mi_msg}.")

        # Pylint - User requested removal of this specific line
        # py_score = data.get("pylint_score", 0)
        # qual_desc = "mirë"
        # if py_score > 9: qual_desc = "shkëlqyer"
        # elif py_score < 7: qual_desc = "nevojë për përmirësim"
        # lines.append(f"• Cilësia (Pylint): Nota është {py_score}/10. Cilësia e përgjithshme është {qual_desc}.")

        return "\n".join(lines)

    # ------------------ EXPORT ------------------
    def export_txt(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.output.get("1.0", tk.END))

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Element"] + list(self.current_sets.keys()) + ["R"])
            universe = set().union(*self.current_sets.values()) | self.current_result
            for el in sorted(universe):
                row = [el]
                for k in self.current_sets:
                    row.append(1 if el in self.current_sets[k] else 0)
                row.append(1 if el in self.current_result else 0)
                writer.writerow(row)

    def export_pdf(self):
        if not HAS_PDF:
            messagebox.showinfo("PDF", "reportlab mungon")
            return
        path = filedialog.asksaveasfilename(defaultextension=".pdf")
        if not path:
            return

        try:
            # Import high-level layout tools
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.pagesizes import A4
            
            # Setup Document
            doc = SimpleDocTemplate(path, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []

            # 1. Main Application Results
            title = Paragraph("Projekt inteligjent për bashkësi", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 12))

            # Use Preformatted for the set results/tables to keep alignment
            content_text = self.output.get("1.0", tk.END)
            # A simple monospace style
            code_style = styles['Code']
            story.append(Preformatted(content_text, code_style))
            
            # 2. Append Dynamic Metrics Content
            try:
                story.append(PageBreak())
                
                # Title for Metrics Section
                story.append(Paragraph("Analiza e Kodit (Live)", styles['Title']))
                story.append(Spacer(1, 12))
                
                story.append(Paragraph(f"Raport i gjeneruar automatikisht për: {os.path.basename(path)}", styles['Normal']))
                story.append(Spacer(1, 12))

                # Calculate metrics for THIS file (or the main script)
                target_file = os.path.abspath(__file__)
                print(f"INFO: Running metrics on {target_file}")
                
                metrics_output, metrics_data = self.get_code_metrics(target_file)
                print(f"INFO: Metrics generated. Data: {metrics_data}")
                
                # Use Preformatted for the metrics text as it is terminal output
                story.append(Preformatted(metrics_output, styles['Code']))

                # 3. Add Generic Interpretation (Definitions)
                story.append(PageBreak())
                story.append(Paragraph("Interpretimi i Rezultateve (Gjeneral)", styles['Title']))
                story.append(Spacer(1, 12))
                
                explanations = [
                    ("Radon Raw Metrics", "Tregon numrin e rreshtave të kodit (LOC), komenteve dhe rreshtave bosh. Më shumë komente zakonisht nënkuptojnë dokumentacion më të mirë."),
                    ("Cyclomatic Complexity (CC)", "Mat kompleksitetin e kodit. Nota A (1-5) është e shkëlqyer. Nota B (6-10) është e mirë. C (11-20) është e moderuar. D-F (>20) kërkon thjeshtim."),
                    ("Maintainability Index (MI)", "Indeksi i mirëmbajtjes (0-100). Vlera > 50 është A (shumë e mirë). Vlera < 20 tregon kod të vështirë për t'u mirëmbajtur."),
                    ("Halstead Metrics", "Mat vështirësinë dhe përpjekjen për të kuptuar kodin bazuar në operatorë dhe operandë."),
                    ("Pylint Score", "Një notë nga 0 deri në 10. Synoni për > 8.0 për kod cilësor. Tregon pajtueshmërinë me standardet PEP 8 dhe gabimet e mundshme.")
                ]
                
                for title, text in explanations:
                    story.append(Paragraph(f"<b>{title}:</b>", styles['Heading3']))
                    story.append(Paragraph(text, styles['BodyText']))
                    story.append(Spacer(1, 6))

                # 4. Add Specific Interpretation (Live Analysis)
                story.append(Spacer(1, 12))
                story.append(Paragraph("Rezultatet e Analizës (Specifike për këtë kod)", styles['Title']))
                story.append(Spacer(1, 12))
                
                # Custom Albanian text
                explanation_text = self.generate_detailed_explanation(metrics_data)
                
                # Render as bullet points or just text
                for line in explanation_text.splitlines():
                    story.append(Paragraph(line, styles['BodyText']))
                    story.append(Spacer(1, 6))

            except Exception as e_inner:
                 story.append(Spacer(1, 12))
                 story.append(Paragraph(f"Error generating metrics: {str(e_inner)}", styles['Normal']))

            # 3. Build PDF
            doc.build(story)
            messagebox.showinfo("PDF", "PDF u ruajt me sukses!")

        except Exception as e:
            messagebox.showerror("Gabim PDF", str(e))


# ------------------ MAIN ------------------
def main():
    root = tk.Tk()
    SetApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
