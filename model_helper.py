from sklearn.naive_bayes import MultinomialNB
from sklearn_pandas import DataFrameMapper
from baikal import Step
import pandas as pd
from sklearn.base import TransformerMixin

class DataFrameMapperStep(Step, DataFrameMapper):
    def __init__(self, *args, name=None, n_outputs=1, **kwargs):
        super().__init__(*args, name=name,n_outputs=n_outputs,**kwargs)

    def __getstate__(self):
        state = super().__getstate__()
        state["_name"] = self._name
        state["_nodes"] = self._nodes
        state["_n_outputs"] = self._n_outputs
        return state

    def __setstate__(self, state):
        self._name = state.pop("_name")
        self._nodes = state.pop("_nodes")
        self._n_outputs = state.pop("_n_outputs")
        super().__setstate__(state)
        
                
# The order of inheritance is important!
class NaiveBayes(Step, MultinomialNB):
    def __init__(self, *args, name=None, n_outputs=1, **kwargs):
        super().__init__(*args, name=name,n_outputs=n_outputs,**kwargs)
        
    def predict_proba(self, X):
        output = super().predict_proba(X)
        return pd.DataFrame(output, columns=self.classes_)
    

class IsDeposit(TransformerMixin):
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        return X < 0
    