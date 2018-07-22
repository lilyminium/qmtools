import os
import glob
import csv
import pandas as pd
from .gaussian_ import read_output


HARTREE_TO_KJ_MOL = 2625.50
HARTREE_TO_J_MOL = HARTREE_TO_KJ_MOL*1000

class G3Out:

    pka_fields =   ("base_name","solvent","dft",
                    "mp2s","mp2l","ccsdt",
                    "hlc","zpve","tc",
                    "entropy_j","e0","enthalpy_au",
                    "enthalpy_kj","dG","energy_au",
                    "energy_kj","g_solv_dir","direct_vs_indirect",
                    "G_solv_", "self_ref_indirect", "self_ref_direct")
    

    def __init__(self, *outfiles):
        mp2_jobs = []
        for file in outfiles:
            if "mp2" in file.method.lower():
                mp2_jobs.append(file)
            elif file.thermal is not None:
                self.dft = file
            else:
                self.cc = file 

        self.mp2s, self.mp2l = sorted(mp2_jobs, key=lambda x: x.n_basis)

        print(f"""
            DFT     : {self.dft.filename}
            MP2S    : {self.mp2s.filename}
            MP2L    : {self.mp2l.filename}
            CCSD(T) : {self.cc.filename}
            """)
        self.get_options()

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


class MassG3:
    def __init__(self, path):
        self.get_available_files(path)
        self.sort_by_coords()
        self.link_related_groups()
        

    def get_available_files(self, path):
        realpath = os.path.join(path, "**", "*.*")
        files = glob.glob(realpath, recursive=True)
        self.output_files = []
        for file in files:
            try:
                self.output_files.append(read_output(file))
            except KeyError:
                pass



    def sort_by_coords(self):
        grouped_files = []
        while self.output_files:
            current = self.output_files[0]
            matched = [x for x in self.output_files if x.similar_orientation_to(current)]
            grouped_files.append(matched)
            self.output_files = [x for x in self.output_files if x not in matched]
        self.g3 = [G3Out(*x) for x in grouped_files]

    def link_related_groups(self):
        linked = []
        while self.g3:
            current_elements = self.g3[0].dft.elements
            matched = [x for x in self.g3 if x.elements == current_elements]
            linked.append(matched)
            self.g3 = [x for x in self.g3 if x not in matched]

        self.grouped = [sorted(groups, key=lambda x: x.solvate) for groups in linked]

    def calculate_solvent_options(self, ref_solv=None):
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

            except ValueError:
                pass


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

    def __init__(self, path=".", outfile="pka_energies.csv", reference=None):
        self.parsed = MassG3(path)

        if reference:
            df = pd.read_csv(reference, header=0)
            solvated = df[df['solvent']!='None'].to_dict(orient='records')[0]
        else:
            solvated = None

        self.parsed.calculate_solvent_options(solvated)

        text = [self.pka_fields.format(**self.pka_fields_h)]
        for group in self.parsed.grouped:
            for line in group:
                text.append(self.pka_fields.format(**line.dct))
            print("*****")

        with open(outfile, 'w') as f:
            f.write("\n".join(text))



