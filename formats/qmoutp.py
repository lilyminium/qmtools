import os

class CSVOut:
    ext = ".csv",
    fields = "{base_name},{solvent},{energy}"
    fields_h = ["Base name", "Solvent", "Energy (au)"]
    pka_fields =   ("{base_name},{solvent},{dft},"
                    "{mp2s},{mp2l},{ccsdt},"
                    "{hlc},{zpve},{tc},"
                    "{entropy_j},{e0},{enthalpy_au},"
                    "{enthalpy_kj},{dG},{energy_au},"
                    "{energy_kj},{g_solv_dir},{direct_vs_indirect},"
                    "{G_solv_}")

    headings = dict(
        fields_h = dict(
            base_name="Base name", 
            solvent="Solvent", 
            energy="Energy (au)"
            )
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
            G_solv_="G solv (kJ/mol)"
            )
        reference_h = dict(
            HA_ref_indirect="HA+Ref (indirect)", 
            HA_ref_direct="HA+ref (direct)", 
            Href_A_indirect="Href+A (indirect)", 
            Href_A_direct="Href+A(direct)",
            raw_pka_indirect="Raw pKa (indirect)", 
            raw_pka_direct="Raw pKa (direct)", 
            pka_indirect="pKa (indirect)", 
            pka_direct="pKa (direct)"
            )
        )

    reference =    (",{HA_ref_indirect},{HA_ref_direct},"
                    "{Href_A_indirect},{Href_A_direct},{raw_pka_indirect},"
                    "{raw_pka_direct},{pka_indirect},{pka_direct}")
    reference_h = 

    def __init__(self, outfile, *infiles, show=False, delimiter="both",  dft="", 
                    mp2s="", mp2l="", cc="", ref="", **kwargs):

        self.out = f"{outfile}{self.ext}"

        include = []
        if mp2s or mp2l or dft or cc:
            include.append("pka_fields")
            if ref:
                include.append("reference")
        else:
            include.append(fields)

        self.pattern = "".join(include)
        self.include_headings = [x+"_h" for x in include]
        self.write_headings()

    def write_headings(self)
        if not os.path.isfile(self.out):
            heading_dict = {}
            for h in self.include_headings:
                heading_dict.update(self.headings[h])
            with open(self.out, 'w') as f:
                f.write(self.pattern.format(**heading_dict))





class QMOut:
    """
    Base class for generating QM input files. Should be
    subclassed for actual usage.


    """

    #
    # Questions to ask
    #

    whitespace = dict(
        ext = ".txt",
        fields = "{base_name:25} {solvent:8} {energy:16.11f}",
        pka_fields =   ("{base_name:25} {solvent: 8} {dft:16.11f} "
                        "{mp2s:16.11f} {mp2l:16.11f} {ccsdt:16.11f} "
                        "{hlc:12.7f} {zpve: 12.7f} {tc: 12.7f} "
                        "{entropy_j: 12.6f} {e0: 16.11f} {enthalpy_au: 16.11f} "
                        "{enthalpy_kj: 16.11f} {dG: 16.11f} {indirect_au: 12.7f} "
                        "{indirect_kj: 12.7f} {direct_kj:12.7f} {direct_vs_indirect:12.6f} "
                        "{G_solv_kj: 12.7f}"),

        reference =    (" {HA_ref_indirect:12.7f} {HA_ref_direct: 12.7f} "
                        "{Href_A_indirect:12.7f} {Href_A_direct: 12.7f} {raw_pka_indirect:12.7f} "
                        "{raw_pka_direct:12.7f} {pka_indirect: 6.4f} {pka_direct: 6.4f}")
                )

    csv = dict(
        ext = ".csv",
        fields = "{base_name},{solvent},{energy}",
        pka_fields =   ("{base_name},{solvent},{dft},"
                        "{mp2s},{mp2l},{ccsdt},"
                        "{hlc},{zpve},{tc},"
                        "{entropy_j},{e0},{enthalpy_au},"
                        "{enthalpy_kj},{dG},{indirect_au},"
                        "{indirect_kj},{direct_kj},{direct_vs_indirect},"
                        "{G_solv_kj}"),

        reference =    (",{HA_ref_indirect},{HA_ref_direct},"
                        "{Href_A_indirect},{Href_A_direct},{raw_pka_indirect},"
                        "{raw_pka_direct},{pka_indirect},{pka_direct}")
                )


    


    def __init__(self, outfile, *infiles, show=False, delimiter="both",  dft="", 
                    mp2s="", mp2l="", cc="", ref="", **kwargs):

        self.csv, self.wht = f"{outfile}.csv", f"{outfile}.dat"


        print(style(f"    File: {file}", "yellow"))
        self.process_geometry(file)

        if kwargs:
            if not interactive:
                self._ask_questions = False

            rassolov = kwargs.pop("rassolov", True)
            basis = kwargs.pop("basis", self.basis)
            theory = kwargs.pop("theory", self.theory)
            self.rassolov = rassolov
            self.basis = basis
            self.theory = theory
            self.jobid = f"{self.geometry.base_name}.{self.theory}_{self.rassolov_version}"
            
            for k, v in kwargs.items():
                setattr(self, k, v)

    def write(self):


            

        self.make_coords()
        if self._ask_questions:
            self.ask_questions()
        else:
            print(f"""
                Theory  : {self.theory}
                Basis   : {self.basis} {("" if not self.rassolov else self.genbasis)} (Rassolov={self.rassolov})
                Charge  : {self.charge}  Multiplicity: {self.multiplicity}
                Optimize: {self.optimize}  Frequencies: {self.calculate_frequencies}
                Solvate : {self.solvate}""")
            if self.solvate:
                print(f"""
                    Solvent model: {self.solvent_model}
                    Solvent      : {self.solvent}"""[1:])
        
        self.make_string_options()
        self.make_file_lines()
        self.write_file()
        if show:
            print(f"""
                ------   {self.path}{self.jobid}.{self.ext}   ------\n{self.file_lines}
              