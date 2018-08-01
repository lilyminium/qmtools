import os
import glob
import csv
import pandas as pd
from .gaussian_ import read_output
from utils import printred, printyellow, printdarkcyan, stylered
from xlsxwriter.utility import xl_rowcol_to_cell


HARTREE_TO_KJ_MOL = 2625.50
HARTREE_TO_J_MOL = HARTREE_TO_KJ_MOL*1000

class G3Out:
    dft = None
    cc = None
    solvate = False

    pka_keys = ["mass_total", "filename", "base_name", "solvent", "charge", "dft", 
                    "mp2s", "mp2l", "ccsdt", 
                    "hlc", "zpve", "tc", 
                    "entropy_j", "e0", "enthalpy_au", 
                    "enthalpy_kj", "dG", "energy_au", 
                    "energy_kj", "g_solv_dir", "direct_vs_indirect", 
                    "G_solv_", "self_ref_indirect", "self_ref_direct"]
    

    def __init__(self, *outfiles, verbose=1, **kwargs):
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
        elif verbose > 3:
            print(txt[1:])



    def get_options(self):
        dct = dict.fromkeys(self.pka_keys, None)
        dct.update(self.dft.get_all())
        self.elements = dct['elements']
        dct['dft'] = self.dft.get_energy()
        dct['mp2s'] = self.mp2s.get_energy()
        dct['mp2l'] = self.mp2l.get_energy()
        dct['ccsdt'] = self.cc.get_energy()
        # dct['entropy_j'] = dct['entropy']

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
        self.get_available_files(files, verbose=verbose, **kwargs)
        self.sort_by_coords(verbose=verbose, debug=debug)
        self.link_related_groups(debug=debug)
        

    def get_available_files(self, files, verbose=1, **kwargs):
        self.output_files = []
        _summaries = []
        for file in files:
            try:
                parsed = read_output(file, verbose=verbose, **kwargs)
                if parsed:
                    if parsed.summary not in _summaries:
                        self.output_files.append(parsed)
                        _summaries.append(parsed.summary)
                    elif verbose > 1:
                        idx = _summaries.index(parsed.summary)
                        printred(f"Not added: {file} is identical to {self.output_files[idx]}")
                elif verbose > 3:
                    printred(f"Failed to parse: {file}")
            except:
                if verbose > 3:
                    printred(f"Failed to parse: {file}")
        # self.output_files.sort(key=lambda x: x.charge, reverse=True)


    def sort_by_coords(self, verbose=1, debug=False):
        grouped_files = []
        self.g3 = []
        n_infile = len(self.output_files)
        while self.output_files:
            current = self.output_files[0]
            matched = [x for x in self.output_files if x.similar_to(current, debug=debug, verbose=verbose)]
            if len(matched) >= 4:
                try:
                    self.g3.append(G3Out(*matched, verbose=verbose, debug=debug))
                    prev_len = len(self.output_files)
                    self.output_files = [x for x in self.output_files if x not in self.g3[-1].outfiles]
                    if debug and verbose > 2:
                        print(f"Previous no. files: {prev_len}. New no: {len(self.output_files)}")

                except ValueError as err:
                    if debug and verbose > 1:
                        print(err)
                    self.output_files.pop(0)
            else:
                if debug and verbose>1:
                    print(f"Only {len(matched)} files found for {current.filename}")
                self.output_files = [x for x in self.output_files if x not in matched]
        printyellow(f"Parsed {len(self.g3)} G3 systems from {n_infile} files.")

    def link_related_groups(self, debug=False):
        self.grouped = []
        while self.g3:
            current = self.g3.pop(0)
            matched = [x for x in self.g3 if x.elements == current.elements and x.solvate != current.solvate]
            matched.sort(key = lambda x: current.sq_diff(x))
            try:
                match = matched[0]
                if debug:
                    printyellow(f"Matching {current.dft.filename} with {match.dft.filename}")
                self.grouped.append([current, matched[0]])
                self.g3.remove(matched[0])
            except IndexError as err:
                if debug:
                    print(err)
                    current.print_files()
        # self.grouped = [sorted(groups, key=lambda x: x.solvate) for groups in linked]#[::-1]

    def calculate_solvent_options(self, ref_solv=None, verbose=1):
        printdarkcyan("\n             ***********************")
        for each in self.grouped:
            try:
                vacuum = [x for x in each if not x.solvate][0]
                solvated = [x for x in each if x.solvate][0]
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

            except (ValueError, IndexError):
                if verbose:
                    printred("Failed to match to vacuum and solvent.")
                    for group in each:
                        group.print_files()
                        print("")
                    printdarkcyan("             ***********************")


    def gather(self):
        return [x.dct for y in self.grouped for x in y]


class PKARef:

    pka_keys_h = dict(
        mass_total="Mass (amu)",
        filename="File name",
        base_name="Base name", 
        charge="Charge",
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
    pka_keys =   ("{mass_total} {filename}, {base_name},{charge}, {solvent},{dft},"
                    "{mp2s},{mp2l},{ccsdt},"
                    "{hlc},{zpve},{tc},"
                    "{entropy_j},{e0},{enthalpy_au},"
                    "{enthalpy_kj},{dG},{energy_au},"
                    "{energy_kj},{g_solv_dir},{direct_vs_indirect},"
                    "{G_solv_},{self_ref_indirect},{self_ref_direct}")
    pka_keys = ["mass_total", "filename", "base_name", "solvent", "charge", "dft", 
                    "mp2s", "mp2l", "ccsdt", 
                    "hlc", "zpve", "tc", 
                    "entropy_j", "e0", "enthalpy_au", 
                    "enthalpy_kj", "dG", "energy_au", 
                    "energy_kj", "g_solv_dir", "direct_vs_indirect", 
                    "G_solv_", "self_ref_indirect", "self_ref_direct"]

    def __init__(self, paths, outfile="pka_energies", ext="xlsx", reference=None, verbose=2, debug=False, name_vacuum=False, **kwargs):
        files = []
        for path in paths:
            if os.path.isdir(path):
                realpath = os.path.join(path, "**", "*.*")
                if verbose:
                    printyellow(realpath)
                files += glob.glob(realpath, recursive=True)
            if os.path.isfile(path):
                files.append(os.path.realpath(path))

        self.parsed = MassG3(files, verbose=verbose, debug=debug, **kwargs)
        if reference:
            df = pd.read_csv(reference, header=0)
            solvated = df[df['Solvent']!='None'].to_dict(orient='records')[0]
        else:
            solvated = None

        self.parsed.calculate_solvent_options(solvated, verbose=verbose)
        flat = self.parsed.gather()
        self.df = pd.DataFrame(flat)[self.pka_keys]
        self.df.rename(columns=self.pka_keys_h, inplace=True)
        self.df.sort_values(by=['HLC', 'Mass (amu)', 'CC Energy (au)'], ascending=[False, False, True], inplace=True)
        self.nrows = len(self.df.index)

        if name_vacuum:
            self.df.loc[self.df['Solvent'].isna(), 'Solvent'] = "vacuum"


        fmt = dict(
            csv=self.write_csv,
            xlsx=self.write_xlsx
            )
        filename = fmt.get(ext, fmt['csv'])(outfile, verbose=verbose, debug=debug)

    def write_csv(self, outfile, **kwargs):
        filename = f"{outfile}.csv"
        self.df.to_csv(filename)
        printyellow(f"Wrote {filename}")


    def write_xlsx(self, outfile, verbose=2, debug=False, **kwargs):

        def _rc_to_a1(c, *r):
            # 0 indexed number to 1 indexed A1 Excel notation
            quot, rem = divmod(c, 26)
            c_ = "".join([chr(rem+65)]*(quot+1))
            #r_ = [str(x) for x in r]
            return ":".join([c_+str(x+1) for x in r]) if r else c_


        filename = f"{outfile}.xlsx"
        writer = pd.ExcelWriter(filename, engine='xlsxwriter')
        self.df.to_excel(writer, sheet_name='Energies', index=False, startrow=1, header=False)
        workbook = writer.book
        worksheet = writer.sheets['Energies']

        fmt_anion = workbook.add_format(dict( # red
                                            bg_color='#FFC7CE',
                                            font_color= '#9C0006'
                                            ))
        fmt_neutral = workbook.add_format(dict( # yellow
                                            bg_color='#fff3be',
                                            ))
        fmt_water = workbook.add_format(dict( # blue
                                            bg_color='#b0e2ea',
                                            font_color= '#160a3e'
                                            ))
        fmt_vacuum = workbook.add_format(dict( # green
                                            bg_color='#C6EFCE',
                                            font_color= '#006100'
                                            ))
        fmt_header = workbook.add_format(dict( #header
                                            bold=True,
                                            valign='center',
                                            border=1,
                                            font_size=14,
                                            locked=True,
                                            ))


        for ncol, heading in enumerate(self.df.columns):
            worksheet.write(0, ncol, heading, fmt_header)


        charge, solvent = map(self.df.columns.get_loc, ('Charge', 'Solvent'))
        FIRST_COL, LAST_COL = 0, len(self.df.columns) # Indexed from 0
        charge_A1, solvent_A1, first_col_A1, last_col_A1 = map(_rc_to_a1, [charge, solvent, FIRST_COL, LAST_COL])
        FIRST_ROW, LAST_ROW = 1, self.nrows

        charge_col, solvent_col = [_rc_to_a1(x, FIRST_ROW, LAST_ROW) for x in [charge, solvent]]

        worksheet.conditional_format(charge_col,
                                            dict(
                                        type='cell',
                                        criteria='<',
                                        value=0,
                                        format=fmt_anion
                                        ))
        worksheet.conditional_format(charge_col, 
                                    dict(
                                        type='cell',
                                        criteria='==',
                                        value=0,
                                        format=fmt_neutral
                                        ))
        

        worksheet.conditional_format(solvent_col, 
                                    dict(
                                        type='text',
                                        criteria='containing',
                                        value='water',
                                        format=fmt_water
                                        ))
        worksheet.conditional_format(solvent_col, 
                                    dict(
                                        type='text',
                                        criteria='not containing',
                                        value='water',
                                        format=fmt_vacuum
                                        ))

        for row in range(FIRST_ROW+1, LAST_ROW+2):
            # not charge=0, because Excel gets weird about it
            criteria = f'AND(${charge_A1}${row}=0,NOT(ISNUMBER(SEARCH("water",${solvent_A1}${row}))))'
            row_col = f"{first_col_A1}{row}:{last_col_A1}{row}"
            if verbose>3 and debug:
                print(row_col)
                print(criteria)
            worksheet.conditional_format(row_col,
                                    dict(
                                        type='formula',
                                        criteria=criteria,
                                        format=fmt_neutral
                                        ))

        writer.save()
        csv = self.write_csv(outfile)
        printyellow(f"Wrote {filename}")





