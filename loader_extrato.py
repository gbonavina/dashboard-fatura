import pandas as pd 

class ExtratoLoader:
    def __init__(self, df_path):
        self.df_path = df_path
    def load_extrato(self):
        df = pd.read_excel(self.df_path)
        
        df.columns = df.iloc[4] 
        df = df.drop(df.index[:5])
        df.reset_index(drop=True, inplace=True) 
        df.columns = ([ 'Data', 'Descrição', 'Docto', 'Situação', 'Crédito (R$)', 'Débito (R$)', 'Saldo (R$)'])

        df = df.drop(columns=['Docto', 'Situação', 'Saldo (R$)'])
        df = df.fillna(0)

        df = df[df['Data'].astype(str).str.match(r'\d{2}/\d{2}/\d{4}', na=False)]
        
        df = df.drop(df.index[-1])
        df.reset_index(drop=True, inplace=True)

        def convert_br_to_float(value):
            if pd.isna(value) or value == 0:
                return 0.0
            
            str_val = str(value)
            str_val = str_val.replace('.', '').replace(',', '.')
            try:
                return float(str_val)
            except:
                return 0.0

        # Converte colunas do formato brasileiro
        df['Crédito (R$)'] = df['Crédito (R$)'].apply(convert_br_to_float)
        df['Débito (R$)'] = df['Débito (R$)'].apply(convert_br_to_float)
        
        df['Valor'] = df['Crédito (R$)'] + df['Débito (R$)']
        
        df = df.drop(columns=['Crédito (R$)', 'Débito (R$)'])

        return df

    def get_description_col(self, df):
        return list(df["Descrição"].values)