import pandas as pd 
import numpy as np
import mdtraj as md
import mendeleev as meev

from utils.chem_files import coordinate_lines_from_log, coordinate_lines_from_xyz


class FileReader:

    def __init__(self, file):
        self.file = file
        self.read()

    def read(self):
        try:
            self.structure = md.load(self.file, top=self.md_topology())
        except ValueError:
            self.structure = md.load(self.file, top=self.xyz_topology())
        except OSError:
            self.structure = self.load_log()
        self.topology = self.structure.topology.to_dataframe()


    def log_to_df(self):
        atoms = coordinate_lines_from_log(self.file)
        df = pd.DataFrame.from_dict(atoms)
        df['element'] = [meev.element(int(x)).symbol for x in df['atomic_number']]
        df['name'] = df['element']
        df['resSeq'] = 1
        df['resName'] = "UNK"
        df['chainID'] = 0
        return df

    def xyz_topology(self):
        atoms = coordinate_lines_from_xyz(self.file)
        df = pd.DataFrame.from_dict(atoms)
        df['name'] = df['element']
        df['resSeq'] = 1
        df['resName'] = "UNK"
        df['chainID'] = 0
        df['serial'] = list(range(1, len(df['element'])+1))
        bonds = np.empty((0, 0))
        top =  md.Topology.from_dataframe(df, bonds)
        return top

    def load_log(self):
        df = self.log_to_df()
        bonds = np.empty((0, 0))
        topology = md.Topology.from_dataframe(df, bonds)
        xyz = df.loc[:, ('x', 'y', 'z')].values
        return md.Trajectory(xyz, topology)

    def md_topology(self):
        df, bonds = md.load(self.file).topology.to_dataframe()
        df['resSeq'] = 1
        return md.Topology.from_dataframe(df, bonds)
