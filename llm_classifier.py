import pandas
from loader_extrato import ExtratoLoader
import google.generativeai as genai
from dotenv import load_dotenv, find_dotenv
import os
import time

def classify_transaction_with_gemini(transactions):
    load_dotenv(find_dotenv())
    
    genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    batch_size = 15  
    all_categories = []
    
    for i in range(0, len(transactions), batch_size):
        batch = transactions[i:i+batch_size]
        batch_text = "\n".join([f"{idx+1}. {trans}" for idx, trans in enumerate(batch)])
        
        prompt = f"""
                Você é um especialista em classificação de transações financeiras de pessoa física.

                Analise a descrição da transação e classifique em UMA das categorias abaixo:
                Classifique EXATAMENTE {batch_size} transações abaixo:

                CATEGORIAS E CRITÉRIOS:
                - Alimentação: Restaurantes, lanchonetes, delivery, bares, cafeterias, Fass
                - Receitas: Salários, PIX recebidos, depósitos, rendimentos, reembolsos
                - Saúde: Consultas médicas, exames, planos de saúde, hospitais, clínicas
                - Farmácia: Drogarias, medicamentos (Raia, Droga Raia, Drogasil, etc.)
                - Seguros: Seguros de vida, auto, residencial, previdência
                - Mercado: Supermercados, hipermercados, açougues, padarias, hortifrúti, frutas, etc.
                - Educação: Escolas, cursos, livros, mensalidades, material escolar
                - Compras: Lojas de roupas, eletrônicos, casa, decoração, shopping
                - Transporte: Combustível, Uber, táxi, ônibus, metrô, estacionamento, mecânico, autoelétrico, Reginaldo
                - Investimento: Aplicações, fundos, ações, renda fixa, corretoras, Pix enviado para Alvaro Bonavina
                - Transferências para terceiros: PIX enviados, DOC, TED para outras pessoas
                - Telefone: Operadoras de celular, internet, TV por assinatura
                - Moradia: Aluguel, condomínio, IPTU, luz, água, gás, reformas
                - Impostos: Receita Federal, IOF, Ministério da Fazenda, IRPF

                INSTRUÇÕES ESPECÍFICAS:
                - Raia, Drogaven = Farmácia
                - Supermercados (Savegnago, Casa Deliza, Braghini, etc.) = Mercado
                - Postos de gasolina = Transporte
                - Shopping/Magazine = Compras
                - PIX recebido = Receitas
                - PIX enviado = Transferências para terceiros
                - Aldeia, Divino Gourmet, = Alimentação
                

                Transação para classificar:
                {batch_text}

                Responda APENAS com o nome da categoria (sem pontuação ou explicação).
                """
        
        try:
            response = model.generate_content(prompt)
            batch_categories = response.text.strip().split('\n')
            
            cleaned_categories = []
            for cat in batch_categories:
                if cat.strip():
                    clean_cat = cat.split('. ', 1)[-1].strip()
                    if clean_cat:
                        cleaned_categories.append(clean_cat)
            
            if len(cleaned_categories) > len(batch):
                cleaned_categories = cleaned_categories[:len(batch)]
            elif len(cleaned_categories) < len(batch):
                cleaned_categories.extend(['Erro'] * (len(batch) - len(cleaned_categories)))
            
            all_categories.extend(cleaned_categories)
            print(f"Lote {i//batch_size + 1} processado - {len(cleaned_categories)} categorias")
            
            time.sleep(5)
            
        except Exception as e:
            if "429" in str(e): 
                print(f"Rate limit atingido! Aguardando 60 segundos...")
                time.sleep(60) 
                try:
                    response = model.generate_content(prompt)
                except Exception as e2:
                    print(f"Erro persistente: {e2}")
                    all_categories.extend(['Erro'] * len(batch))
            else:
                print(f"Erro: {e}")
                all_categories.extend(['Erro'] * len(batch))
    
    return all_categories

def integrate_category_in_df(path_extrato):
    EL = ExtratoLoader(path_extrato)
    df = EL.load_extrato()
    desc = EL.get_description_col(df=df)

    categories = classify_transaction_with_gemini(desc)

    df["Categoria"] = categories
    df.to_csv("finances.csv", index=False)