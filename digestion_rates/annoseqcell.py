# AUTOGENERATED! DO NOT EDIT! File to edit: ../02_AnnoSeqCell.ipynb.

# %% auto 0
__all__ = ['AnnoSequencesCells']

# %% ../02_AnnoSeqCell.ipynb 3
import numpy as np
import pandas as pd
import gzip
from .preprocess import SequencesCells
from pathlib import Path
from multiprocessing import Pool

# %% ../02_AnnoSeqCell.ipynb 17
class AnnoSequencesCells(SequencesCells):
    def __init__(self, df=None):
        super().__init__(df=df)

    def add_cell_anno(self, path, compression='gzip', usecols=None):
        anno_df = pd.read_csv(path, compression=compression, usecols=usecols)
        anno_df.columns = map(lambda x: x.lower(), anno_df.columns)
        self.table = join_df_anno(self.table, anno_df)
        return self

    def split_cells(self, by='sort_population', keep_only_common=False):
        group_names = list(self.table[by].unique())
        if keep_only_common:
            self.table = filter_unshared_sequences(self.table, group_names)
        dz = build_group_dictionary(self.table, by)    
        self.group = dz
        return self
        
    
