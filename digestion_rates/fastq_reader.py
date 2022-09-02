# AUTOGENERATED! DO NOT EDIT! File to edit: ../01_FastQ.ipynb.

# %% auto 0
__all__ = ['extract_umi_cb', 'extract_dictionary', 'count_unique_sequences', 'SequencesCells', 'FastQ']

# %% ../01_FastQ.ipynb 3
import numpy as np
import pandas as pd
import gzip

# %% ../01_FastQ.ipynb 5
def extract_umi_cb(nm):
    nm = nm.split(' ')[0]
    cb, umi = nm.split('_')[1:3]
    return cb, umi

# %% ../01_FastQ.ipynb 8
def extract_dictionary(path, plate_name):
    fastq_dict = {}
    with gzip.open(path, 'rt') as f:
        content = f.readlines()
        for i, line in enumerate(content):
            index_seq = i % 4
            line = line.strip()
            if index_seq == 0:
                sequence = content[i+1].strip()
                cb, umi = extract_umi_cb(line)
                cb = plate_name + '_' + cb 
                i += 0
                if cb in fastq_dict.keys():
                    if sequence in fastq_dict[cb].keys():                    
                        fastq_dict[cb][sequence].append(umi)
                    else:
                        fastq_dict[cb][sequence] = [umi]

                else:
                    fastq_dict[cb] = {sequence:[umi]}
    return fastq_dict


# %% ../01_FastQ.ipynb 11
def count_unique_sequences(dz):    
    df = pd.DataFrame(dz)
    df = df.applymap(lambda x: len(set(x)) if isinstance(x,list) else 0)
    return df

# %% ../01_FastQ.ipynb 14
class SequencesCells():
    def __init__(self, df, plate):
        self.table = df
        self.plates = [plate]
    def join_plate(self, sequences_cells):
        addtable = sequences_cells.table
        plates_to_add = [p for p in sequences_cells.plates if p not in self.plates]
        if len(plates_to_add) == 0:
            return self
        select_cells = np.array([[plate in name_cell for name_cell in addtable.columns]
                                    for plate in plates_to_add]).sum(axis=0).astype(bool)
        other = addtable.loc[:,select_cells]
        self.table = pd.concat([self.table,other], axis=1).dropna()
        self.plates = self.plates + plates_to_add
        return self
    def select_plate(self, plate):
        df = self.table.loc[:, [col for col in plates.table.columns if plate in col]]
        return SequencesCells(df, plate)

# %% ../01_FastQ.ipynb 15
class FastQ():
    def __init__(self, fastq_file, plate_name=None):
        self.fastq_file = fastq_file
        self.plate_name = plate_name
        
    def parse_file(self):
        if self.plate_name is None:
            self.plate_name = '-'.join(self.fastq_file.split('_')[0].split('-')[1:])
            
            
        fastq = extract_dictionary(self.fastq_file, self.plate_name)
        df_fastq = count_unique_sequences(fastq)
        return SequencesCells(df_fastq, self.plate_name)

            
