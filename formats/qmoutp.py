import os
import glob
import csv
import pandas as pd
from .gaussian_ import read_output
from utils import printred, printyellow, printdarkcyan, stylered


HARTREE_TO_KJ_MOL = 2625.50
HARTREE_TO_J_MOL = HARTREE_TO_KJ_MOL*1000

class G3Out:
    dft = None
    cc = None
    solvate = False

    pka_fields =   ("base_name","solvent","dft",
                    "mp2s","mp2l","ccsdt",
                    "hlc","zpve","tc",
                    "entropy_j","e0","enthalpy_au",
                    "enthalpy_kj","dG","energy_au",
                    "energy_kj","g_solv_dir","direct_vs_indirect",
                    "G_solv_", "self_ref_indirect", "self_ref_direct")
    

    def __init__(self, *outfiles, verbose=1):
        mp2_jobs = []
        for file in outfiles:
            if "mp2" in file.method.lower():
                mp2_jobs.append(file)
            elif file.tc is not None:
                self.dft = file
            else:
                self.cc = file 

        try:
            mp2_sorted = sorted(mp2_jobs, key=lambda x: x.n_basis)
            self.mp2s  = mp2_sorted.pop(0)
            self.mp2l  = mp2_sorted[-1]
        except (ValueError, IndexError):
            self.try_print_files(outfiles, verbose=verbose)

        self.try_print_files(outfiles, verbose=verbose)
        self.outfiles = [self.dft, self.mp2s, self.mp2l, self.cc]
        self.get_options()

    def print_files(self):
        print(f"""
                DFT : {self.dft.filename}
               MP2S : {self.mp2s.filename}
               MP2L : {self.mp2l.filename}
            CCSD(T) : {self.cc.filename}
            Solvent : {self.dct['solvent']}
            """)

    def try_print_files(self, outfiles, verbose=2):
        err = 0
        txt = ""
        for k in ["dft", "mp2s", "mp2l", "cc"]:
            try:
                filename = getattr(self, k).filename
            except:
                filename = stylered("Missing")
                err += 1
            txt += f"""
                {k.upper():>5} : {filename}"""
        if err:
            printred(f"""
                Missing files!""")
            print(txt[1:])
            print(f"{len(outfiles)} input files.")
            raise ValueError
        elif verbose > 1:
            print(txt[1:])



    def get_options(self):
        dct = dict.fromkeys(self.pka_fields, None)
        dct.update(self.dft.get_all())
        self.elements = dct['elements']
        dct['dft'] = self.dft.get_energy()
        dct['mp2s'] = self.mp2s.get_energy()
        dct['mp2l'] = self.mp2l.get_energy()
        dct['ccsdt'] = self.cc.get_energy()
        dct['entropy_j'] = dct['entropy']*HARTREE_TO_J_MOL

        dct['e0'] = dct['ccsdt'] - dct['mp2s'] + dct['mp2l'] + dct['hlc']
        dct['enthalpy_au'] = dct['e0'] + dct['zpve'] + dct['tc']
        dct['enthalpy_kj'] = dct['enthalpy_au'] * HARTREE_TO_KJ_MOL
        dct['dG'] = dct['enthalpy_kj'] - (dct['temperature']*dct['entropy_j']/1000)

        self.solvate = dct['solvate']
        self.dct = dct

    def sq_diff(self, other):
        try:
            return min(np.sum(self.dft.std_coords - other.dft.std_coords)**2,
                np.sum(self.dft.std_coords + other.dft.std_coords)**2)
        except:
            return 1e10


class MassG3:
    def __init__(self, files, verbose=1, debug=False, **kwargs):
        self.get_available_files(files, verbose=verbose)
        self.sort_by_coords(verbose=verbose, debug=debug)
        self.link_related_groups()
        

    def get_available_files(self, files, verbose=1):
        self.output_files = []
        _summaries = []
        for file in files:
            try:
                parsed = read_output(file, verbose=verbose)
                if parsed:
                    if parsed.summary not in _summaries:
                        self.output_files.append(parsed)
                        _summaries.append(parsed.summary)
                    elif verbose > 1:
                        idx = _summaries.index(parsed.summary)
                        printred(f"Not added: {file} is identical to {self.output_files[idx]}")
                elif verbose > 2:
                    printred(f"Failed to parse: {file}")
            except:
                if verbose > 2:
                    printred(f"Failed to parse: {file}")


    def sort_by_coords(self, verbose=1, debug=False):
        grouped_files = []
        self.g3 = []
        while self.output_files:
            current = self.output_files[0]
            matched = [x for x in self.output_files if x.similar_to(current, debug=debug, verbose=verbose)]
            if len(matched) >= 4:
                try:
                    self.g3.append(G3Out(*matched, verbose=verbose))
                    self.output_files = [x for x in self.output_files if x not in self.g3[-1].outfiles]

                except ValueError:
                    self.output_files.pop(0)
            else:
                self.output_files = [x for x in self.output_files if x not in matched]

    def link_related_groups(self):
        linked = []
        while self.g3:
            current = self.g3[0]
            matched = [x for x in self.g3 if x.elements == current.elements]
            matched.sort(key = lambda x: current.sq_diff(x))
            linked.append(matched[:2])
            self.g3 = [x for x in self.g3 if x not in matched[:2]]

        self.grouped = [sorted(groups, key=lambda x: x.solvate) for groups in linked][::-1]

    def calculate_solvent_options(self, ref_solv=None, verbose=1):
        printdarkcyan("\n             ***********************")
        for each in self.grouped:
            try:
                vacuum, solvated = each
                solvated.dct['energy_au'] = solvated.dct['dft'] - vacuum.dct['dft']
                solvated.dct['energy_kj'] = solvated.dct['energy_au'] * HARTREE_TO_KJ_MOL
                solvated.dct['g_solv_dir'] = solvated.dct['dG'] - vacuum.dct['dG']
                solvated.dct['direct_vs_indirect'] = solvated.dct['g_solv_dir'] - solvated.dct['energy_kj']
                solvated.dct['G_solv_'] = solvated.dct['energy_kj'] + vacuum.dct['dG']

                if ref_solv:
                    solvated.dct['self_ref_indirect'] = solvated.dct['G_solv_'] + ref_solv['G_solv_']
                    solvated.dct['self_ref_direct'] = solvated.dct['dG'] + ref_solv['dG']

                if verbose:
                    vacuum.print_files()
                    solvated.print_files()
                    printdarkcyan("             ***********************")

            except ValueError:
                if verbose:
                    for group in each:
                        group.print_files()
                    printdarkcyan("             ***********************")

            


class PKARef:

    pka_fields_h = dict(
        base_name="Base name", 
        solvent="Solvent", 
        dft="DFT Energy (au)",
        mp2s="MP2S Energy (au)", 
        mp2l="MP2L Energy (au)", 
        ccsdt="CC Energy (au)",
        hlc="HLC", 
        zpve="ZPVE", 
        tc="TherCorr", 
        entropy_j="Entropy (J)", 
        e0="E0", 
        enthalpy_au="Enthalpy (au)",
        enthalpy_kj="Enthalpy (kJ/mol)", 
        dG="G (kJ/mol)", 
        energy_au="Esol-Egas (au)", 
        energy_kj="Esol-Egas (kJ)",
        g_solv_dir="Direct Gsol-Ggas (kJ)", 
        direct_vs_indirect="Direct-Indirect", 
        G_solv_="G solv (kJ/mol)",
        self_ref_indirect="Self+Ref (Indirect)",
        self_ref_direct="Self+Ref (Direct)"
        )
    pka_fields =   ("{base_name},{solvent},{dft},"
                    "{mp2s},{mp2l},{ccsdt},"
                    "{hlc},{zpve},{tc},"
                    "{entropy_j},{e0},{enthalpy_au},"
                    "{enthalpy_kj},{dG},{energy_au},"
                    "{energy_kj},{g_solv_dir},{direct_vs_indirect},"
                    "{G_solv_},{self_ref_indirect},{self_ref_direct}")

    def __init__(self, paths, outfile="pka_energies.csv", reference=None, verbose=2, **kwargs):
        files = []
        for path in paths:
            if os.path.isdir(path):
                realpath = os.path.join(path, "**", "*.*")
                if verbose:
                    printyellow(realpath)
                files += glob.glob(realpath, recursive=True)
            if os.path.isfile(path):
                files.append(os.path.realpath(path))


        self.parsed = MassG3(files, verbose=verbose, **kwargs)

        if reference:
            df = pd.read_csv(reference, header=0)
            solvated = df[df['Solvent']!='None'].to_dict(orient='records')[0]
        else:
            solvated = None

        self.parsed.calculate_solvent_options(solvated, verbose=verbose)

        text = [self.pka_fields.format(**self.pka_fields_h)]
        for group in self.parsed.grouped:
            for line in group:
                for k, v in line.dct.items():
                    if v is None:
                        line.dct[k] = ""
                text.append(self.pka_fields.format(**line.dct))

        with open(outfile, 'w') as f:
            f.write("\n".join(text))

        printyellow(f"Written to {outfile}.")



